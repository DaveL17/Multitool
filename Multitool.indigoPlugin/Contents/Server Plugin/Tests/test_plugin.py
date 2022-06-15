""" Docstring placeholder """
from unittest import TestCase
import logging
import indigo

LOGGER = logging.getLogger("Plugin")


class Tester(TestCase):
    """
    Run unit tests to ensure plugin is functioning properly.

    The Tests class contains all unit tests for the Multitool plugin.
    """
    def run_tests(self):
        indigo.server.log(f"Tests Add: {self.test_add()}")
        indigo.server.log(f"Tests Dev Deps: {self.device_dependencies()}")

    def test_add(self):
        """ Base test """
        self.assertEqual(indigo.activePlugin.add(1, 2), 3)  # This is axiomatically true.
        # self.assertEqual(indigo.activePlugin.add(1, 2), 4)  # This is axiomatically false.
        return True

    def device_dependencies(self):
        """  Device ID not found in Indigo.devices. """
        values_dict = indigo.Dict()
        values_dict['listOfDevices'] = 12345678
        result = indigo.activePlugin.device_dependencies(values_dict)
        self.assertEqual(result[1]['listOfDevices'], "Device ID not found.")
        return True
