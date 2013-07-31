import os
import unittest

import mock

from python_subgrid import utils


@unittest.skipIf(not os.path.exists('doc/source/index.rst'),
                 'doc/source dir not available')
class TestUtils(unittest.TestCase):

    def test_generate_functions_documentation(self):
        with mock.patch('__builtin__.open'):
            utils.generate_functions_documentation()
