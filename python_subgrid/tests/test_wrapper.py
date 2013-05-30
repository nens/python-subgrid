import unittest

from python_subgrid import wrapper


class TestHelperFunctions(unittest.TestCase):

    def test_libname1(self):
        self.assertEquals(wrapper._libname(), 'libsubgrid.so')
