import unittest

import mock

from python_subgrid import wrapper


class TestHelperFunctions(unittest.TestCase):

    @mock.patch('platform.system', lambda: 'Linux')
    def test_libname1(self):
        self.assertEquals(wrapper._libname(), 'libsubgrid.so')

    @mock.patch('platform.system', lambda: 'Darwin')
    def test_libname2(self):
        self.assertEquals(wrapper._libname(), 'libsubgrid.dylib')

    @mock.patch('platform.system', lambda: 'Windows')
    def test_libname3(self):
        self.assertEquals(wrapper._libname(), 'libsubgrid.dll')

    @mock.patch('os.path.exists', lambda path: False)
    def test_library_path_not_found(self):
        self.assertRaises(RuntimeError, wrapper._library_path)

    def test_library_path1(self):
        self.assertTrue('libsubgrid' in wrapper._library_path())

    @mock.patch('os.environ', {'SUBGRID_PATH': 'somewhere'})
    def test_library_path2(self):
        self.assertTrue('libsubgrid' in wrapper._library_path())
