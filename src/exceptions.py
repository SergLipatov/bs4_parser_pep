class ParserFindTagException(Exception):
    """Вызывается, когда парсер не может найти тег."""

class VersionsNotFoundError(Exception):
    """Вызывается, когда парсер не нашёл список версий в боковой панели."""