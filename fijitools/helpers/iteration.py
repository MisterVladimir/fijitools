# -*- coding: utf-8 -*-
from six import string_types
from typing import Any, Generator, Iterable, Iterator, List


def isiterable(arg: Any):
    # copied from
    # https://stackoverflow.com/questions/1055360/how-to-tell-a-variable-is-iterable-but-not-a-string/44328500#44328500
    return isinstance(arg, Iterable) and not isinstance(arg, string_types)


def current_and_next(iterable: Iterable[Any],
                     interval: int = 1
                     ) -> Generator[Any, None, None]:
    """
    Return item at current index and the item an 'interval' array distance
    forward.
    """
    iterator: Iterator[Any] = iter(iterable)
    missed: List[Any] = [next(iterator) for _ in range(interval)]
    for next_ in iterator:
        yield missed[0], next_
        missed = missed[1:] + [next_]
