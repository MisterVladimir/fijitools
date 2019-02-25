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
from setuptools import setup
from ruamel import yaml
from addict import Dict


with open('README.md', 'r') as f:
    README = f.read()


def get_package_info():
    package_info_yaml = yaml.YAML()
    with open('meta.yaml', 'r') as f:
        return Dict(package_info_yaml.load(f))


if __name__ == '__main__':
    from setuptools import find_packages
    info = get_package_info()
    ver = info.package.version
    url = info.about.home
    req = info.requirements.run

    setup(name='fijitools',
          version=ver,
          packages=find_packages(),
          python_requires='>=3.6',
          install_requires=req,
          include_package_data=True,
          author='Vladimir Shteyn',
          author_email='vladimir.shteyn@googlemail.com',
          url=url,
          download_url=r'{0}/archive/{1}.tar.gz'.format(url, ver),
          long_description=README,
          license="GNUv3",
          test_suite='fijitools.test.run_tests',
          classifiers=[
              'Intended Audience :: Science/Research',
              'Programming Language :: Python :: 3.6'])
