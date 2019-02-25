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
import unittest
import numpy as np

from fijitools.helpers import coordinate
from fijitools.test import run_tests


class CoordinateTest(unittest.TestCase):
    def create_coord(self):
        return coordinate.Coordinate(um=(5., 6))

    def test_create(self):
        self.assertTrue(self.create_coord())

    def test_conversion(self):
        coord = self.create_coord()
        # print("coord['nm']: {}".format(coord['nm']))
        # print("coord keys: {}".format(", ".join(coord.keys())))
        self.assertTrue(all(coord['nm']))

    def test_get_pixelsize(self):
        coord = self.create_coord()
        self.assertFalse(coord.pixelsize)
        coord['px'] = np.array((5, 5))
        self.assertTrue(all(coord.pixelsize))

    def test_set_pixelsize(self):
        # setting pixelsize to a number
        coord = self.create_coord()
        coord.pixelsize = 100.
        # print('pixelsize: {}'.format(coord.pixelsize))
        # print('length: {}'.format(len(coord)))
        # print('coord: {}'.format(coord))
        self.assertTrue(all(coord['px'] == np.array([50, 60])))

        # setting pixelsize to an array
        coord = self.create_coord()
        coord.pixelsize = [20, 20]
        self.assertTrue(all(coord['px'] == np.array([250, 300])))

        # setting pixelsize to a Coordinate
        coord = self.create_coord()
        coord.pixelsize = coordinate.Coordinate(nm=(50, 50))

    def test_equal(self):
        coord1 = self.create_coord()
        coord2 = self.create_coord()
        # print('coord1: {}'.format(coord1))
        # print('coord2: {}'.format(coord2))
        # print('equal: {}'.format(coord1 == coord2))
        self.assertTrue(all(coord1 == coord2))
        self.assertTrue(
            coordinate.Coordinate(nm=1000.) == coordinate.Coordinate(um=1.))

    def test_sum(self):
        intended_result = coordinate.Coordinate(um=(7., 6.))
        start_coord = coordinate.Coordinate(um=(5., 6.))
        to_add = coordinate.Coordinate(um=(2., 0.))
        result = start_coord + to_add
        self.assertTrue(np.all(intended_result == result))
        # print('\n')
        # print("test_sum still has errors")
        # print("result         : {}".format(result))
        # print("intended result: {}".format(intended_result))
        # setting to_add = Coordinate(um=(0., 0.)) returns [True, True]
        # print("intended_result == result: {}".format(intended_result == result))

    def test_mul(self):
        intended_result = coordinate.Coordinate(um=(10., 12))
        start_coord = self.create_coord()
        n = 2
        self.assertTrue(all(start_coord * n == intended_result))
        self.assertTrue(all(start_coord * np.array((n, n)) == intended_result))

    def test_divide(self):
        intended_result = coordinate.Coordinate(um=(2.5, 3.))
        start_coord = self.create_coord()
        self.assertTrue(all(start_coord / 2. == intended_result))
        self.assertTrue(all(start_coord / [2., 2] == intended_result))


def run():
    pass


if __name__ == '__main__':
    run()
