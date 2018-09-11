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

from functools import singledispatch, update_wrapper
import numbers

def create_dispatcher(n):
    def decorator(func):
        """
        Decorator for function/method overloading based on argument at position
        n instead of 0, or at keyword n like functools.singledispatch.

        Similar to

        https://stackoverflow.com/questions/24601722/
        how-can-i-use-functools-singledispatch-with-instance-methods
        """
        dispatcher = singledispatch(func)

        if isinstance(n, numbers.Integral):
            def wrapper(*args, **kwargs):
                return dispatcher.dispatch(args[n].__class__)(*args, **kwargs)
        elif isinstance(n, str):
            def wrapper(*args, **kwargs):
                return dispatcher.dispatch(kwargs[n].__class__)(*args, 
                                                                **kwargs)

        # so that registering a type for the wrapped instance method
        # can be done by calling method.register(type)
        wrapper.register = dispatcher.register
        update_wrapper(wrapper, func)
        return wrapper
    return decorator

methdispatch = create_dispatcher(1)
