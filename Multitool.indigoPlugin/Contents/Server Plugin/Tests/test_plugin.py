""" Docstring placeholder """
from unittest import TestCase
import logging
import indigo

LOGGER = logging.getLogger("Plugin")


class TestAdd(TestCase):
    """ Docstring placeholder """
    def test_add(self):
        """ Docstring placeholder """
        self.assertEqual(indigo.activePlugin.add(1, 2), 3)
        self.assertEqual(indigo.activePlugin.add(1, 2), 4)  # This one fails on purpose.
