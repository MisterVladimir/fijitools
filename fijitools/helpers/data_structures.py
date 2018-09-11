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
import numpy as np
import copy
import h5py
import weakref
from addict import Dict
from collections import OrderedDict
import datetime
import json
from struct import pack

from fijitools.helpers.iteration import isiterable


class IndexedDict(Dict):
    """
    Allows setting and getting keys/values by passing in the key index. 

    We cannot use an integer key to set a value to None. The workaround is to
    use a key of type slice and an iterable containing None:
    >>> d = IndexedDict()
    >>> d['a'] = 0
    >>> d.iloc(slice(1), [None])
    >>> d
    {'a': None}
    """
    def _get_with_int(self, key, value):
        return self[key]

    def _get_with_slice(self, key, value):
        return [self[k] for k in key]

    def _set_with_int(self, key, value):
        self[key] = value

    def _set_with_slice(self, key, value):
        for k, v in zip(key, value):
            self[k] = v

    def iloc(self, i, value=None):
        try:
            keys = list(self.keys())[i]
        except IndexError as e:
            raise KeyError('Key must be set via self.__setitem__ before '
                           'referencing it via the .iloc() method.') from e
        else:
            method_dict = {(True, False): self._get_with_int,
                           (True, True): self._get_with_slice,
                           (False, False): self._set_with_int,
                           (False, True): self._set_with_slice}

            try:
                method = method_dict[(value is None,
                                      isiterable(keys) and isiterable(value))]
            except KeyError as e:
                raise TypeError(
                    'If key is iterable, value must also be iterable.') from e
            else:
                return method(keys, value)


class TrackedList(list):
    """
    List that keeps track of items added and removed.
    """
    removed = []
    added = []

    def _append_removeable(self, item):
        self.removed.append(item)

    def __delitem__(self, index):
        self._append_removeable(self[index])
        super().__delitem__(index)

    def clear(self):
        self.removed += list(self)
        super().clear()

    def remove(self, item):
        self._append_removeable(item)
        super().remove(item)

    def pop(self):
        self._append_removeable(self[-1])
        super().pop()

    def _append_addable(self, item):
        if np.iterable(item) and not isinstance(item, (str,)):
            self.added += list(item)
        else:
            self.added.append(item)

    def __add__(self, item):
        ret = copy.copy(self)
        ret._append_addable(item)
        super().__add__(ret)

    def __setitem__(self, key, value):
        self._append_removeable(self[key])
        self._append_addable(value)
        super().__setitem__(key, value)

    def extend(self, items):
        self._append_addable(items)
        super().extend(items)

    def append(self, item):
        self._append_addable(item)
        super().append(item)

    def insert(self, index, item):
        self._append_addable(item)
        super().insert(index, item)

ds_dtype = [('x', '>i4')]


# there must be a more elegant way of doing this?
class NestedDict(dict):
    """
    Helper class for converting fit data from h5 format into dictionary or
    numpy structured array.
    """
    dtype = np.dtype(ds_dtype)

    def __init__(self):
        super().__init__()
#        list of all field names in our dtype
        self.all_fields = np.concatenate(
            [[k] if self.dtype[k].fields is None else
                [k] + list(self.dtype[k].fields.keys())
                for k in self.dtype.fields])

    def __missing__(self, key):
        # make sure we're adding data appropriate for this class
        if key not in self.all_fields:
            pass
        # raise KeyError(
        # '{0} not a legal key. Use keys from self.dtype.'.format(key))
        else:
            self[key] = self.__new__(type(self))
            return self[key]

    def __call__(self, name, node):
        """
        Use this method as the argument to h5py.visititems() in order to
        load data from h5py file into self. Group and Dataset names form the
        keys of self. Values are leaves.
        """
        if isinstance(node, h5py.Dataset):
            if len(name.split(r'/')) == 1:
                self[name] = node.value
            # print("Dataset:", node.name, name, node)
        elif isinstance(node, h5py.Group):
            # print("Group:", node.name, name, node)
            _name = node.name.split(r'/')[-1]
            for item in node.values():
                child_name = item.name.split(r'/')[-1]
                self[_name].__call__(child_name, item)
        else:
            pass
        return None

    def to_struct_array(self, shape):
        """
        Return the data as a numpy structured array of type self.dtype
        """
        def func(ret, val, dtype):
            for k in dtype.fields:
                if dtype[k].fields is None:
                    ret[k] = val[k]
                else:
                    func(ret[k], val[k], ret[k].dtype)
            return ret
        # structured array that is filled and returned
        ret = np.zeros(shape, dtype=self.dtype)
        # source of data
        source = self
        dtype = self.dtype
        return func(ret, source, dtype)


class RoiPropsDict(OrderedDict):
    """
    """
    def __init__(self, string='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ugly workaround for when the last character of
        # string.split(r'\n') is '' because the string ends in r'\n'.
        # This is common (always the case?) for ImageJ ROI.
        if string:
            if string[:-1] == '\n':
                string = string[:-1]
            kv = [pair.split(': ') for pair in string.split('\n')
                  if len(pair.split(': ')) == 2]
            self.update(kv)
            self.string = string

            # self.update(OrderedDict([(item.split(': ')[0], item.split(': ')[1])
            #                          for item in string.split('\n')]))

    def to_IJ(self, image_name=''):
        """
        "{}: {}\n" format allows ImageJ to parse ROI properties and store them
        as a java.utils.Properties object.
        """
        add = r'Software: https://github.com/MisterVladimir/fiji_utils'+'\n'

        date = datetime.date.today()
        date = date.year, date.month, date.day
        add += 'YYYYMMDD: {}-{}-{}\n'.format(*date)

        if image_name:
            image_name = 'Image Name: {}'.format(image_name)
        else:
            image_name = ''
        add += image_name

        li = ["{}: {}".format(k, v) for k, v in self.items()]
        as_string = '\n'.join(map(str, li)) + '\n' + add
        return pack('>' + 'h'*len(as_string), *tuple(map(ord, as_string)))

    def to_JSON(self, image_name=''):
        if image_name:
            self['image_name'] = image_name
        return json.dumps(self)
