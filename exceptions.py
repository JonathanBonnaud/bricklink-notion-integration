class NameNotFound(Exception):
    """Raised when no name found in page"""

    pass


class CategoryNotFound(Exception):
    """Raised when no category found in page"""

    pass


class BLQuotaExceeded(Exception):
    """Raised when BrickLink quota is exceeded"""

    pass
