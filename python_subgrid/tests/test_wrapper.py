import unittest

import mock

from python_subgrid import wrapper


class TestHelperFunctions(unittest.TestCase):

    def test_libname1(self):
        with mock.patch('platform.system', lambda: 'Linux'):
            self.assertEquals(wrapper._libname(), 'libsubgrid.so')

    def test_libname2(self):
        with mock.patch('platform.system', lambda: 'Darwin'):
            self.assertEquals(wrapper._libname(), 'libsubgrid.dylib')

    def test_libname3(self):
        with mock.patch('platform.system', lambda: 'Windows'):
            self.assertEquals(wrapper._libname(), 'libsubgrid.dll')
