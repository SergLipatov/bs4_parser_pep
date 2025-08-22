from pathlib import Path
from urllib.parse import urljoin

# Основные URL для парсинга документации Python
MAIN_DOC_URL = 'https://docs.python.org/3/'
MAIN_PEPS_URL = 'https://peps.python.org/'
WHATS_NEW_URL = urljoin(MAIN_DOC_URL, 'whatsnew/')
DOWNLOADS_URL = urljoin(MAIN_DOC_URL, 'download.html')

# Базовые пути для работы с файловой системой
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / 'logs'
LOG_FILE = LOG_DIR / 'parser.log'

# Форматы даты и времени для различных целей
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'  # Для имен файлов
DT_FORMAT = '%d.%m.%Y %H:%M:%S'        # Для логирования

# Настройки логирования
LOG_FORMAT = '"%(asctime)s - [%(levelname)s] - %(message)s"'

# Режимы вывода результатов работы парсера
PRETTY_MODE = 'pretty'
FILE_MODE = 'file'

# Соответствие статусов PEP (код → возможные названия)
EXPECTED_STATUS = {
    'A': ('Active', 'Accepted'),
    'D': ('Deferred',),
    'F': ('Final',),
    'P': ('Provisional',),
    'R': ('Rejected',),
    'S': ('Superseded',),
    'W': ('Withdrawn',),
    '': ('Draft', 'Active'),
}
