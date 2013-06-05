import unittest

import mock

from python_subgrid import utils


class TestUtils(unittest.TestCase):

    def test_generate_functions_documentation(self):
        with mock.patch('__builtin__.open'):
            utils.generate_functions_documentation()
