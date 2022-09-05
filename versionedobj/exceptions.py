
class InvalidFilterError(Exception):
    """
    Exception raised whenever 'only' and 'ignore' filters are used at the same time
    """
    pass


class LoadObjError(Exception):
    """
    Exception raised whenever saved object data cannot be loaded because of a JSON parser error
    or because of a failed migration path
    """
    pass


class InputValidationError(Exception):
    """
    Exception raised whenever validation of a serialized object fails
    """
    pass


