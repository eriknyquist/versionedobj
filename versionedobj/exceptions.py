
class InvalidFilterError(Exception):
    """
    Exception raised whenever 'only' and 'ignore' filters are used at the same time
    """
    pass


class LoadObjectError(Exception):
    """
    Exception raised whenever saved object data cannot be loaded because of a JSON parser error
    """
    pass


class InputValidationError(Exception):
    """
    Exception raised whenever validation of a serialized object fails
    """
    pass


class InvalidVersionAttributeError(Exception):
    """
    Exception raised whenever a nested VersionedObject has a 'version' attribute
    """
    pass
