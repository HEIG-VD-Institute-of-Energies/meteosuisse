class MeteoSwissAPIError(Exception):
    pass


class CollectionNotFoundError(MeteoSwissAPIError):
    pass


class StationNotFoundError(MeteoSwissAPIError):
    pass


class DataNotAvailableError(MeteoSwissAPIError):
    pass


class InvalidDateRangeError(MeteoSwissAPIError):
    pass


