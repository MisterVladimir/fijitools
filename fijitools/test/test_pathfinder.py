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
import glob
import os

from fijitools.io.path import PathFinder
from fijitools.test import run_tests


class PathFinderTest(unittest.TestCase):
    def setUp(self):
        self.folder = os.path.abspath('data')

    def test_create(self):
        finder = PathFinder(extension='zip')

    def test_zip_file(self):
        finder = PathFinder(extension='zip')
        # print('folder: {}'.format(self.folder))
        self.assertEqual([('test_roi_basic.zip', )], finder.load(
            self.folder + os.path.sep + 'test_roi_basic.zip'))

    def test_zip_folder(self):
        correct = set([(os.path.basename(p), ) for p in glob.glob(
            self.folder + os.path.sep + '*.zip')])
        finder = PathFinder(extension='zip')
        result = set(finder.load(self.folder))
        # print('result: {}'.format(result))
        # print('correct: {}'.format(correct))
        self.assertTrue(result == correct)

    def test_regexp(self):
        correct = set([(os.path.basename(p), ) for p in glob.glob(
            self.folder + os.path.sep + 'test_roi_*')])
        finder = PathFinder(regexp='test_roi_.*', extension='zip')
        result = set(finder.load(self.folder))
        # print('result: {}'.format(result))
        # print('correct: {}'.format(correct))
        self.assertTrue(result == correct)


def run():
    run_tests(PathFinderTest)


if __name__ == '__main__':
    run()
