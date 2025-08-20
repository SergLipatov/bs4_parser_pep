import logging

from requests import RequestException

from constants import EXPECTED_STATUS
from exceptions import ParserFindTagException


def get_response(session, url):
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        return response
    except RequestException:
        logging.exception(
            f'Возникла ошибка при загрузке страницы {url}',
            stack_info=True
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        error_msg = f'Не найден тег {tag} {attrs}'
        logging.error(error_msg, stack_info=True)
        raise ParserFindTagException(error_msg)
    return searched_tag


def check_status_consistency(status_code, status_name, url):
    if (status_code in EXPECTED_STATUS
            and status_name in EXPECTED_STATUS[status_code]):
        return

    if status_code in EXPECTED_STATUS:
        logging.warning(f'Несовпадающе статусы:\n{url}\nСтатус в карточке: '
                        f'{status_name}\nОжидаемые статусы: '
                        f'{EXPECTED_STATUS[status_code]}')
    else:
        valid_codes = [code for code, names in EXPECTED_STATUS.items() if
                       status_name in names]
        if valid_codes:
            logging.warning(
                f'Несовпадающе статусы:\n{url}\nСтатус в карточке: '
                f'{status_name}\nОжидаемый код статуса: '
                f'{valid_codes}')
        else:
            logging.warning(
                f'Несуществующий статус:\n{url}\nСтатус в карточке: '
                f'{status_name}\nИзвестные статусы: '
                f'{list(sum(EXPECTED_STATUS.values(), ()))}')
    return
