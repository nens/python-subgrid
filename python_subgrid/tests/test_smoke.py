from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import unittest

import python_subgrid


class VersionTest(unittest.TestCase):

    def test_dunder_version(self):
        # Test that we have a proper non-failing version attribute.
        self.assertTrue(python_subgrid.__version__)
