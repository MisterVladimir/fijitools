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

from fijitools.helpers import data_structures as ds


class TrackedListTest(unittest.TestCase):
    def test_create(self):
        self.li = ds.TrackedList()

    def test_adding(self):
        compare_list = ['appended', 'inserted', 'item_set', 'item_added']
        self.li = ds.TrackedList()
        self.li.append('appended')
        self.li.insert(1, 'inserted')
        self.li.append(None)
        self.li[2] = 'item_set'
        self.li += ['item_added']
        for comp, item in zip(compare_list, self.li):
            self.assertEqual(comp, item)


def run():
    pass


if __name__ == '__main__':
    run()
