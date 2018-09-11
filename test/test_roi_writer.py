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
from abc import ABC

from fijitools.io.roi import roi_write


class WriteTest(ABC):
    name = None

    @staticmethod
    def get_path(name):
        return os.path.abspath(os.path.join(
            os.path.curdir, 'test', 'data', name))

    def test_read(self):
        path = self.get_path(self.name)
        with roi_read.IJZipReader() as reader:
            reader.read(path)


class RectWriteTest(unittest.TestCase, WriteTest):
    name = 'rectangles.zip'


class OvalWriteTest(unittest.TestCase, WriteTest):
    name = 'ovals.zip'


if __name__ == '__main__':
    test_classes = (RectWriteTest, OvalWriteTest)
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2)
    for class_ in test_classes:
        loaded_tests = loader.loadTestsFromTestCase(class_)
        runner.run(loaded_tests)
