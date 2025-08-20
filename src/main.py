import logging
import re
from collections import Counter
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, MAIN_DOC_URL, MAIN_PEPS_URL
from outputs import control_output
from utils import check_status_consistency, find_tag, get_response


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
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
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1').text
        dl = find_tag(soup, 'dl').text.replace('\n', ' ')
        result.append((version_link, h1, dl))
    return result


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
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
        raise Exception('Ничего не нашлось')
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
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    table = find_tag(soup, 'table', attrs={'class': 'docutils'})
    a_tag = find_tag(
        table,
        'a',
        {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    url = urljoin(downloads_url, a_tag['href'])
    filename = url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    response = get_response(session, MAIN_PEPS_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    tables = soup.find_all('table', attrs={'class': 'pep-zero-table'})
    result_global = [('status', 'status_on_page', 'number', 'title', 'url')]
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
            response = get_response(session, url)
            if response is None:
                return
            soup = BeautifulSoup(response.text, features='lxml')
            status_on_page = find_tag(soup, 'abbr').text
            check_status_consistency(status, status_on_page, url)
            result_global.append((status, status_on_page, number, title, url))
    status_counts = Counter(item[1] for item in result_global[1:])
    result = [('Status', 'Count')]
    for status, count in status_counts.items():
        result.append((status, count))
    result.append(('Total', len(result_global) - 1))
    return result


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
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
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
