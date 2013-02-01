# (c) 2013 Urban Airship and Contributors

class ClassProperty(object):
    """Use this as a decorator like @property, but for classes.

    When you need a 'property' like API for accessing data through a callable,
    but are working with a class, not an object instance, you can use this
    to achieve your ends.

    Example usage:

    .. code-block::

    @ClassProperty
    def items(cls):
        return cls._private_data

    """
    def __init__(self, func):
        self.func = func

    def __get__(self, inst, cls):
        return self.func(cls)
