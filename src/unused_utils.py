"""File to place unused functions for future use."""


def route_call_to_member(cls, member, method):
    """Map cls.method to cls.member.method instead."""
    setattr(
        cls,
        method,
        lambda x, *args, **kwargs: getattr(getattr(x, member), method,)(
            *args, **kwargs
        ),
    )


def route_calls_to_member(member, calls):
    """
    Apply :func:`route_call_to_member` to class using a decorator.

    Usage:
        @route_calls_to_member("some_list", "len", "__getitem__", "__contains__", "__iter__" )
        class SomeClass:
            some_list = []
    """

    def decorator_func(cls):
        for call in calls:
            route_call_to_member(cls, member, call)
        return cls

    return decorator_func
