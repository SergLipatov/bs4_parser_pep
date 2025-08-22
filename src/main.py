import logging
import re
from collections import Counter
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (DOWNLOADS_DIR, DOWNLOADS_URL, MAIN_DOC_URL,
                       MAIN_PEPS_URL, WHATS_NEW_URL)
from exceptions import VersionsNotFoundError
from outputs import control_output
from utils import check_status_consistency, find_tag, prepare_soup


def whats_new(session):
    try:
        soup = prepare_soup(session, WHATS_NEW_URL)
    except Exception as error:
        logging.error(error)
    main_div = find_tag(
        soup,
        'section',
        attrs={'id': 'what-s-new-in-python'}
    )
    div_with_ul = find_tag(
        main_div,
        'div',
        attrs={'class': 'toctree-wrapper compound'}
    )
    sections_by_python = div_with_ul.find_all('li', attrs={
        'class': 'toctree-l1'})
    result = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(WHATS_NEW_URL, href)
        soup = prepare_soup(session, version_link)
        h1 = find_tag(soup, 'h1').text
        dl = find_tag(soup, 'dl').text.replace('\n', ' ')
        result.append((version_link, h1, dl))
    return result


def latest_versions(session):
    try:
        soup = prepare_soup(session, MAIN_DOC_URL)
    except Exception as error:
        logging.error(error)
    sidebar = find_tag(
        soup,
        'div',
        attrs={'class': 'sphinxsidebarwrapper'}
    )
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise VersionsNotFoundError('Элемент со списком версий не найден в '
                                    'боковой панели.')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if not text_match:
            version = a_tag.text
            status = ''
        else:
            version, status = text_match.groups()
        results.append((link, version, status))
    return results


def download(session):
    try:
        soup = prepare_soup(session, DOWNLOADS_URL)
    except Exception as error:
        logging.error(error)
    table = find_tag(soup, 'table', attrs={'class': 'docutils'})
    a_tag = find_tag(
        table,
        'a',
        {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    url = urljoin(DOWNLOADS_URL, a_tag['href'])
    filename = url.split('/')[-1]
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    archive_path = DOWNLOADS_DIR / filename
    response = session.get(url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    try:
        soup = prepare_soup(session, MAIN_PEPS_URL)
    except Exception as error:
        logging.error(error)
    tables = soup.find_all('table', attrs={'class': 'pep-zero-table'})
    result_global = [('status', 'status_on_page', 'number', 'title', 'url')]
    warnings = []
    errors = []
    for table in tqdm(tables):
        body = find_tag(table, 'tbody')
        all_row = body.find_all('tr')
        for row in all_row:
            status = row.abbr.text[1::] if row.abbr else ''
            number_col = row.find('a')
            title_href_col = number_col.find_next('a')
            number = number_col.text
            title = title_href_col.text
            url = urljoin(MAIN_PEPS_URL, title_href_col['href'])
            try:
                soup = prepare_soup(session, url)
            except Exception as error:
                errors.append(f'Ошибка при обработке URL {url}: {error}')
            status_on_page = find_tag(soup, 'abbr').text
            warning_message = check_status_consistency(
                status,
                status_on_page,
                url
            )
            if warning_message:
                warnings.append(warning_message)
            result_global.append((status, status_on_page, number, title, url))
    for warning in warnings:
        logging.warning(warning)
    for error in errors:
        logging.error(error)

    status_counts = Counter(item[1] for item in result_global[1:])
    result = [('Status', 'Count')]
    result.extend(status_counts.items())
    result.append(('Total', len(result_global) - 1))
    return result


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    try:
        configure_logging()
        logging.info('Парсер запущен!')
        arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
        args = arg_parser.parse_args()
        logging.info(f'Аргументы командной строки: {args}')
        session = requests_cache.CachedSession()
        if args.clear_cache:
            session.cache.clear()
        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)
        if results is not None:
            control_output(results, args)
    except Exception as exception:
        logging.exception(f'Произошла ошибка: {exception}')
        return 1
    logging.info('Парсер завершил работу.')
    return 0


if __name__ == '__main__':
    main()
