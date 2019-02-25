# -*- coding: utf-8 -*-
from functools import singledispatch, update_wrapper
import numbers
from typing import Any, Callable, Union


def create_dispatcher(n: Union[int, str]):
    def decorator(func: Callable) -> Callable[Any]:
        """
        Decorator for function/method overloading based on argument at position
        n instead of 0, or at keyword n like functools.singledispatch.

        Similar to

        https://stackoverflow.com/questions/24601722/how-can-i-use-functools-singledispatch-with-instance-methods
        """
        dispatcher = singledispatch(func)

        if isinstance(n, numbers.Integral):
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                return dispatcher.dispatch(args[n].__class__)(*args, **kwargs)
        elif isinstance(n, str):
            def wrapper(*args, **kwargs) -> Any:
                return dispatcher.dispatch(kwargs[n].__class__)(*args,
                                                                **kwargs)

        # so that registering a type for the wrapped instance method
        # can be done by calling method.register(type)
        wrapper.register = dispatcher.register
        update_wrapper(wrapper, func)
        return wrapper
    return decorator

methdispatch = create_dispatcher(1)
