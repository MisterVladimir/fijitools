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
import numbers
from collections import OrderedDict

from .iteration import isiterable


# BUG: setting values to zero gets division by zero error when getting pixelsize
class Coordinate(dict):
    rtol = 1e-05
    atol = 1e-08
    _unit_conversion = OrderedDict([('nm', 1e-6), ('um', 1e-3), ('m', 1.)])

    def __init__(self, **kwargs):
        intersection = np.intersect1d(kwargs.keys(),
                                      self._unit_conversion.keys())
        assert len(intersection) < 2, "Initializing arguments may only "
        "contain one of {}.".format(', '.join(self._unit_conversion.keys()))
        super().__init__()

        for k, v in kwargs.items():
            if isiterable(v):
                kwargs[k] = np.array(v)

        super().__init__(**kwargs)

        keys = list(kwargs.keys())
        ckeys = list(self._unit_conversion.keys())
        mask = np.isin(ckeys, keys)
        if sum(mask) > 0:
            key = np.array(ckeys)[mask][0]
            self._expand_units(key, kwargs[key])

    def __len__(self):
        try:
            length = np.array([len(v) for v in self.values()])
            if not np.all(length[0] == length):
                raise Exception("Lengths of members not equal.")
        except TypeError:
            # value in self is a float or int
            return 1
        except IndexError:
            # no keys/values in self
            return 0
        else:
            return length[0]

    def _check_iterable(self, value):
        if not len(self) and isiterable(value):
            return True
        elif isiterable(value) and len(self) == len(np.array(value)):
            return True
        elif isinstance(value, numbers.Real):
            return False
        else:
            raise TypeError("{} (type {}) is not supported.".format(
                value, type(value)))

    def __setitem__(self, unit, value):
        if self._check_iterable(value):
            value = np.array(value)
        if unit in self._unit_conversion.keys():
            self._expand_units(unit, value)
        else:
            super().__setitem__(unit, value)

    def _expand_units(self, unit, value):
        # create values for 'm', 'um' and 'nm' units
        conversion = self._unit_conversion
        d = {k: value * conversion[unit] / conversion[k] for k in conversion}
        self.update(**d)

    def __call__(self, value, unit, newunit):
        """Return value given in unit in another unit."""
        conversion = self._unit_conversion
        if newunit in self.keys():
            return value * (self[newunit] / self[unit])
        elif unit in conversion and newunit in conversion:
            return value * (conversion[newunit] / conversion[unit])

    def _is_valid_operand(self, other):
        """
        For ==, >, >=, <, <=, != comparisons.
        """
        try:
            if self.ou_size is None and other.ou_size is None:
                ou = True
            if self.pixelsize is None and other.pixelsize is None:
                ps = True
            if ou and ps:
                return True

            if len(self) == len(other):
                px = np.all(np.isclose(other.pixelsize, self.pixelsize),
                            rtol=self.rtol, atol=self.atol)
                ou = np.all(np.isclose(other.ou_size, self.ou_size),
                            rtol=self.rtol, atol=self.atol)
                return px and ou

            return False

        except (TypeError, AttributeError):
            return False

    def __eq__(self, other):
        """
        Returns
        ---------
        If self.values() are np.ndarrays, return boolean array of len(self).
        Otherwise return boolean. Comparing items of unequal pixelsizes or
        optical unit sizes, and comparing to anything besides Coordinate
        instances returns NotImplemented.
        """
        if self._is_valid_operand(other):
            compare = np.array([np.isclose(self[k], other[k],
                                           rtol=self.rtol, atol=self.atol)
                                for k in self if k in other])
            if len(compare) == 0:
                # no keys in common between self and other
                return False
            else:
                return compare.all(axis=0)
        else:
            return NotImplemented

    def __lt__(self, other):
        if self._is_valid_operand(other):
            compare = np.array([self[k] < other[k] for k in
                                self.keys() if k in other.keys()])
            if len(compare) == 0:
                # no keys in common between self and other
                return False
            else:
                return compare.all(axis=0)
        else:
            return NotImplemented

    def __le__(self, other):
        if self._is_valid_operand(other):
            compare = np.array([self[k] <= other[k] for k in
                                self.keys() if k in other.keys()])
            if len(compare) == 0:
                # no keys in common between self and other
                return False
            else:
                return compare.all(axis=0)
        else:
            return NotImplemented

    def __gt__(self, other):
        if self._is_valid_operand(other):
            compare = np.array([self[k] > other[k] for k in
                                self.keys() if k in other.keys()])
            if len(compare) == 0:
                # no keys in common between self and other
                return False
            else:
                return compare.all(axis=0)
        else:
            return NotImplemented

    def __ge__(self, other):
        if self._is_valid_operand(other):
            compare = np.array([self[k] >= other[k] for k in
                                self.keys() if k in other.keys()])
            if len(compare) == 0:
                # no keys in common between self and other
                return False
            else:
                return compare.all(axis=0)
        else:
            return NotImplemented

    def __add__(self, other):
        other = Coordinate(**other)
        me = Coordinate(**self)
        try:
            ps = me.pixelsize is not None
            other_ps = other.pixelsize is not None
            if ps:
                other.pixelsize = me.pixelsize
            elif other_ps:
                me.pixelsize = other.pixelsize
            kwargs = {k: self[k] + other[k] for k in
                      me.keys() if k in other.keys()}
            return Coordinate(**kwargs)
        except (AttributeError, KeyError):
            return NotImplemented

    def __sub__(self, other):
        return self.__add__(-1 * other)

    def __mul__(self, other):
        coord = self.__class__()
        coord.update(**{k: v * other for k, v in self.items()})
        return coord

    __rmul__ = __mul__

    def __truediv__(self, other):
        it = self._check_iterable(other)
        if it and it is not NotImplemented:
            return self.__mul__(1. / np.array(other))
        else:
            return self.__mul__(1. / other)

    def __floordiv__(self, other):
        ret = self.__truediv__(other)
        ret.update(**{k: np.floor(v, dtype=v.dtype)
                      for k, v in ret.items()})
        return ret

    def _ratio(self, value_1, value_2):
        if value_1 is None or value_2 is None:
            return None
        else:
            return value_1 / value_2

    @property
    def pixelsize(self):
        try:
            return self._ratio(self['nm'], self['px'])
        except KeyError:
            return None

    @pixelsize.setter
    def pixelsize(self, ps):
        # get value in nanometers
        ckeys = np.array(list(self._unit_conversion.keys()))
        keys = np.array(list(self.keys()))
        if isinstance(ps, Coordinate):
            pkeys = list(ps.keys())
            mask = np.isin(ckeys, pkeys)
            key = ckeys[mask][0]
            # do conversion
            ps_nm = self.__call__(ps[key], key, 'nm')
        elif self._check_iterable(ps):
            ps_nm = np.array(ps)
        elif len(self) > 1:
            ps_nm = np.array([ps] * len(self))
        elif len(self) == 1:
            ps_nm = ps

        mask = [item in keys for item in ckeys]
        if sum(mask) > 0 and 'px' not in self.keys():
            # 'nm', 'um', 'm' is set, but 'px' isn't
            # determine the number of pixels from the 'nm'/'um'/'m'
            # and the passed-in pixelsize
            self['px'] = self['nm'] / ps_nm
        elif sum(mask) == 0 and 'px' in self.keys():
            # 'nm', 'um', 'm' aren't set, 'px' is
            # determine the 'nm'/'um'/'m' from the
            # number of pixels and passed-in pixelsize
            self._expand_units('nm', self['px'] * ps_nm)
        elif sum(mask) > 0 and 'px' in self.keys():
            raise AttributeError('Pixelsize and physical sizes are both'
                                 'already set.')

    @property
    def ou_size(self):
        try:
            return self._ratio(self['nm'], self['ou'])
        except KeyError:
            return None

    @ou_size.setter
    def ou_size(self, *args):
        pass
