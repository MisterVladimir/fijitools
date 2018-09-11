# -*- coding: utf-8 -*- 
"""
@author: Vladimir Shteyn
@email: vladimir.shteyn@googlemail.com

Copyright Vladimir Shteyn, 2018

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


from six import string_types
from collections import Iterable


def isiterable(arg):
    # copied from
    # https://stackoverflow.com/questions/1055360/how-to-tell-a-variable-is-iterable-but-not-a-string/44328500#44328500
    return isinstance(arg, Iterable) and not isinstance(arg, string_types)


def current_and_next(iterable, interval=1):
    """
    Return item at current index and the item an 'interval' array distance
    forward. 
    """
    iterator = iter(iterable)
    missed = [next(iterator) for _ in range(interval)] 
    for next_ in iterator:
        yield missed[0], next_
        missed = missed[1:] + [next_]
