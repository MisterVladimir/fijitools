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
import os
from addict import Dict

from test import AbstractTestClass
from fijitools.io.roi import roi_read

true_common = Dict({'0': {'c': 0, 't': 0, 'z': 0, 'centroid': [42.5, 193.],
                          'top_left': [6., 156.], 'sides': [73., 74.]},
                    '1': {'c': 1, 't': 1, 'z': 1, 'centroid': [120.5, 133.5],
                          'top_left': [86., 108.], 'sides': [69., 51.]},
                    '2': {'c': 0, 't': 1, 'z': 1, 'centroid': [179., 230.5],
                          'top_left': [149., 169.], 'sides': [60., 123.]}})


class ReadTest(AbstractTestClass, unittest.TestCase):
    def test_common_params(self):
        for k in true_common.keys():
            roi = self.data[self.zipname]['item'][k]
            roi_dict = {'c': roi.c, 't': roi.t, 'z': roi.z,
                        'centroid': list(roi.centroid['px']),
                        'top_left': list(roi.top_left['px']),
                        'sides': list(roi.sides['px'])}
            self.assertDictEqual(roi_dict, true_common[k])


class RectReadTest(ReadTest):
    roi_path = ReadTest.as_path('rectangles.zip')


class OvalReadTest(ReadTest):
    roi_path = ReadTest.as_path('ovals.zip')


if __name__ == '__main__':
    test_classes = (RectReadTest, OvalReadTest)
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2)
    for class_ in test_classes:
        loaded_tests = loader.loadTestsFromTestCase(class_)
        runner.run(loaded_tests)
