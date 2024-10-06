"""
These tests are invoked by using an action group call to run a hidden action 'my_tests'

These tests can't be run from the IDE because they rely on the plugin host process.
"""
import dotenv
import logging
import os
from unittest import TestCase
from unittest.mock import MagicMock
import indigo  # noqa
from Tools import *


import sys
sys.path.append('./Server Plugin/Tests')

test_case = TestCase()
dotenv.load_dotenv()
DEVICE_FOLDER    = int(os.getenv("DEVICE_FOLDER"))
TRIGGER_FOLDER   = int(os.getenv("TRIGGER_FOLDER"))
ACTION_FOLDER    = int(os.getenv("ACTION_FOLDER"))
ACTION_ID        = int(os.getenv("ACTION_ID"))
ACTION_DEVICE_ID = int(os.getenv("ACTION_DEVICE_ID"))
LOGGER           = logging.getLogger("Plugin")


class TestPlugin(TestCase):
    def setUp(self):
        ...

    def test_device_creation(self):
        """ """
        # ===================================== Create a ping device =====================================
        dev = indigo.device.create(
            protocol=indigo.kProtocol.Plugin,
            address='10.0.1.123',
            name='Multitool Unit Test Ping Device',
            description='Temporary device created during testing.',
            pluginId='com.fogbert.indigoplugin.multitool',
            deviceTypeId='networkPing',
            props={'hostname': '10.0.1.123', 'timeout': '5'},
            folder=DEVICE_FOLDER
        )
        LOGGER.warning("Test ping device created")
        test_case.assertIsInstance(dev, indigo.Device, "Ping device was not created.")
        test_case.assertTrue(dev.id in indigo.devices, "Ping device was not created.")

        # Delete the ping device
        indigo.device.delete(dev.id)
        LOGGER.warning("Test ping device deleted")
        test_case.assertTrue(dev.id not in indigo.devices, "Ping device was not deleted")

        # ===================================== Create a Network Quality Device =====================================
        dev = indigo.device.create(
            protocol=indigo.kProtocol.Plugin,
            address='',
            name='Multitool Unit Test Network Quality Device',
            description='Temporary device created during testing.',
            pluginId='com.fogbert.indigoplugin.multitool',
            deviceTypeId='networkQuality',
            props={'runDownloadTest': True,
                   'runUploadTest': True,
                   'usePrivateRelay': False,
                   'runTestsSequentially': False,
                   'verboseOutput': False,
                   'outputVerification': False
                   },
            folder=DEVICE_FOLDER
        )
        LOGGER.warning("Test network quality device created")
        test_case.assertIsInstance(dev, indigo.Device, "Network Quality device was not created")
        test_case.assertTrue(dev.id in indigo.devices, "Network Quality device was not created.")

        # Delete the network quality device
        indigo.device.delete(dev.id)
        LOGGER.warning("Test network quality device deleted")
        test_case.assertTrue(dev.id not in indigo.devices, "Network Quality device was not deleted")

    def test_action_group_creation(self):
        """  """
        # ===================================== Create the Action Group =====================================
        action = indigo.actionGroup.create(name='Test Action Group', description='Test Action Group', folder=ACTION_FOLDER)
        LOGGER.warning("Test Action group created")
        test_case.assertIsInstance(action, indigo.ActionGroup, "Action group was not created")
        test_case.assertTrue(action.id in indigo.actionGroups, "Action group was not created.")
        # TODO: Add a Multitool action to the action group
        # TODO: Execute the action group

        # ===================================== Delete the Action Group =====================================
        indigo.actionGroup.delete(action.id)
        LOGGER.warning("Test action group deleted")
        test_case.assertTrue(action.id not in indigo.actionGroups, "Action group was not deleted")

    def test_action_group_execution(self):
        """


        When executed, Action Groups return `None`
        """
        action = indigo.actionGroup.execute(ACTION_ID)
        test_case.assertIsNone(action, "Error running action.")

        action = indigo.actionGroup.execute(ACTION_DEVICE_ID)
        test_case.assertIsNone(action, "Error running action.")

    def test_plugin_functions(self):
        """ Plugin methods are available here, even if the IDE doesn't think they are. """

        LOGGER.debug("Running startup tests. (Warning messages are normal.)")
        try:
            # ===================================== About Indigo =====================================
            test_case.assertTrue(self.about_indigo(no_log=True), "Method failed.")
            # ===================================== Battery Level Report =====================================
            test_case.assertTrue(self.battery_level_report(no_log=True), "Method failed.")
            # ===================================== Color Picker =====================================
            dicts = [
                {'chosenColor': 'FF FF FF'},
                {'chosenColor': 1},  # wrong value type
                {'chosenColor': 'white'}  # wrong value type
            ]
            for test_dict in dicts:
                test_case.assertTrue(self.color_picker(test_dict, no_log=True), "Method failed.")
            # ===================================== Device Beep =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Device Inventory =====================================
            values_dict = {'customThing': 'self', 'typeOfThing': 'Other'}
            test_case.assertIsInstance(self.device_inventory(values_dict, no_log=True), dict, "Method failed.")
            # ===================================== Device Last Comm =====================================
            test_case.assertIsNone(self.device_last_successful_comm({'listOfDevices': 'indigo.relay'}, no_log=True), "Method failed.")
            # ===================================== Device Ping =====================================
            # ===================================== Environment Path =====================================
            test_case.assertTrue(self.environment_path(no_log=True), "Method failed")
            # ===================================== Error Inventory =====================================
            for values_dict in [{'error_level': 'err'}, {'error_level': 'err_warn'}]:
                test_case.assertTrue(self.error_inventory(values_dict, no_log=True), "Method failed")
            # ===================================== Indigo Inventory =====================================
            test_case.assertTrue(self.indigo_inventory(no_log=True), "Method failed")
            # ===================================== Methods Indigo Base =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Methods Plugin Base =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Network Quality Report =====================================
            # ===================================== Object Inspection =====================================
            # It's best if the referenced objects are ones that will be around permanently.
            for payload in [{'classOfThing': 'actionGroups', 'thingToPrint': 460267384},
                            {'classOfThing': 'controlPages', 'thingToPrint': 37036932},
                            {'classOfThing': 'devices', 'thingToPrint': 374100038},
                            {'classOfThing': 'schedules', 'thingToPrint': 147884757},
                            {'classOfThing': 'triggers', 'thingToPrint': 1789555909},
                            {'classOfThing': 'variables', 'thingToPrint': 23078783}
                            ]:
                # Print Object Dict
                test_case.assertTrue(self.results_output(payload, no_log=True), "Method failed.")
                # Print Object Dir
                test_case.assertTrue(self.object_directory(payload, no_log=True), "Method failed.")
                # Print Object Dependencies
                test_case.assertTrue(self.object_dependencies(payload, no_log=True), "Method failed.")
            # ===================================== Ping Host =====================================
            # Menu Call
            for hostname in ['10.0.1.1', 'google.com', 'indigo']:
                test_case.assertIsNone(ping_tool.do_the_ping({'hostname': hostname}, menu_call=True), "Method failed.")
            # Action Call
            values_dict = MagicMock()
            values_dict.props = {'selected_device': 1655068310}
            test_case.assertIsInstance(self.network_ping_device_action(values_dict), tuple, "Method failed.")
            # ===================================== Plugin Inventory =====================================
            test_case.assertTrue(self.installed_plugins(no_log=True), "Method failed.")
            # ===================================== Plugins Online =====================================
            test_case.assertTrue(self.running_plugins(no_log=True), "Method failed.")
            # ===================================== Remove Delayed Actions =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Scripts Embedded =====================================
            test_case.assertIsInstance(self.search_embedded_scripts({'search_string': ''}, no_log=True), tuple, "Method failed.")
            test_case.assertTrue(self.search_embedded_scripts({'search_string': ''}, no_log=True)[0], "Method failed.")
            test_case.assertIsInstance(self.search_embedded_scripts({'search_string': 'A'}, no_log=True), tuple, "Method failed.")
            test_case.assertTrue(self.search_embedded_scripts({'search_string': 'A'}, no_log=True)[0], "Method failed.")
            # ===================================== Scripts Linked =====================================
            values_dict = {}
            test_case.assertIsInstance(self.search_linked_scripts(values_dict, no_log=True), tuple, "Method failed.")
            test_case.assertTrue(self.search_linked_scripts(values_dict, no_log=True)[0], "Method failed.")
            # ===================================== Send Status Request =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Serial Ports =====================================
            test_case.assertTrue(self.get_serial_ports({'ignoreBluetooth': True}, no_log=True), "Method failed.")
            # ===================================== Speak String =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Subscribe to Changes =====================================
            # Standard Indigo command; may not need testing.
            # ===================================== Display Plugin Information =====================================
            test_case.assertTrue(self.log_plugin_environment(), "Method failed.")
        except AssertionError as err:
            line_number = err.__traceback__.tb_lineno
            indigo.server.log(f"Startup test failed: {err} at line {line_number}", level=logging.ERROR)
