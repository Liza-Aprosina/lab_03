class CatalogError(Exception):
    pass


class BadItem(CatalogError):
    pass


class SameId(CatalogError):
    pass


class NotFound(CatalogError):
    pass


class BadVersion(CatalogError):
    pass


class BadFile(CatalogError):
    pass
