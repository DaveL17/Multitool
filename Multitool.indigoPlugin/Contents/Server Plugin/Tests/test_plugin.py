""" The test_plugin.py file contains unit tests for the Multitool plugin. """
import xml.etree.ElementTree as ET  # noqa
import os
import unittest
import dotenv
import httpx
# from curlcodes import codes as curlcodes
from httpcodes import codes as httpcodes
from indigo_devices_filters import DEVICE_FILTERS

dotenv.load_dotenv()

API_SECRET: str = os.environ["API_SECRET"]
API_URL: str = os.environ["SERVER_API_URL"]
API_BASE: str = os.environ["SERVER_API_BASE"]
PLUGIN_ID: str = os.environ["PLUGIN_ID"]


class TestActions(unittest.TestCase):
    """
    The TestActions class is used to test plugin actions
    """

    @classmethod
    def setUpClass(cls):
        ...

    @staticmethod
    def communicate(message):
        """ Send the API command message """
        headers = {'Authorization': f'Bearer {API_SECRET}'}
        return httpx.post(API_URL, headers=headers, json=message, verify=False, timeout=None)

    def test_network_quality_action(self):
        """
        Note that the Network Quality Action can take some time to complete, and we wait for it to finish before
        determining success.
        """
        # Run the action.
        message = {
            "id": f"{self._testMethodName} - Run Network Quality action",
            "message": "plugin.executeAction",
            "pluginId": "com.fogbert.indigoplugin.multitool",
            "actionId": "networkQualityAction",
            "waitUntilDone": True,
        }
        resp = self.communicate(message)
        self.assertEqual(resp.status_code, 200, "Error running action.")
        self.assertIsInstance(resp.json(), dict, "Response is not a dict")

    def test_network_quality_device_action(self):
        """
        Note that the Network Quality Action can take some time to complete, and we wait for it to finish before
        determining success.
        """
        # Run the action.
        message = {
            "id": f"{self._testMethodName} - Run Network Quality Device action",
            "message": "plugin.executeAction",
            "pluginId": "com.fogbert.indigoplugin.multitool",
            "actionId": "networkQualityDeviceAction",
            "props": {"selected_device": 609659860},
            "waitUntilDone": True,
        }
        resp = self.communicate(message)
        self.assertEqual(resp.status_code, 200, "Error running action.")
        self.assertIsInstance(resp.json(), dict, "Response is not a dict")


class TestDevices(unittest.TestCase):
    """
    The TestDevices class is used to test plugin devices

    The devices are tested for creation, deletion, and communication (i.e., update, etc.) of each type of device
    defined in `Devices.xml`. This is not meant to test aspects of the various APIs, but it uses the HTTP API to pass
    commands to and receive updates from the Indigo server.
    """
    # TODO: set up test of speak string tool.
    @classmethod
    def setUpClass(cls):
        ...

    @staticmethod
    def communicate(message):
        """ Send the API command message """
        headers = {'Authorization': f'Bearer {API_SECRET}'}
        return httpx.post(API_URL, headers=headers, json=message, verify=False)

    def test_api(self):
        """ Tests the plugin API by creating, testing, and deleting a plugin device. """
        # ===== Network Quality Device =====
        # Create the device
        message = {
            "id": f"{self._testMethodName} - Create device",
            "message": "plugin.executeAction",
            "pluginId": "com.fogbert.indigoplugin.multitool",
            "actionId": "test_foo",
            "props": {
                'address': 1235,
                'description': "My test description.",
                'deviceTypeId': 'networkQuality',
                'instruction': 'create',
                'folder': 788686594,  # the multitool devices folder
                'name': "Unit Test Device",
                'props': {
                    'outputVerification': False,
                    'runDownloadTest': True,
                    'runTestsSequentially': False,
                    'runUploadTest': True,
                    'usePrivateRelay': False,
                    'verboseOutput': False
                },
            },
            "waitUntilDone": True
        }
        resp = self.communicate(message)
        self.assertEqual(resp.status_code, 200, "Error creating device")
        self.assertIsInstance(resp.json(), dict, "Response is not a dict")

        # Delete the device
        # Get the dev id from the response above, so we can delete the device when we're done with it.
        reply_dict = eval(resp.json()['reply_data'])
        message = {
            "id": f"{self._testMethodName} - Delete device",
            "message": "plugin.executeAction",
            "pluginId": "com.fogbert.indigoplugin.multitool",
            "actionId": "test_foo",
            "props": {
                'instruction': 'delete',
                'dev_id': reply_dict['dev_id'],
                'deviceTypeId': 'networkQuality',
            },
            "waitUntilDone": True
        }
        resp = self.communicate(message)
        self.assertEqual(resp.status_code, 200, "Error deleting device")
        self.assertIsInstance(resp.json(), dict, "Response is not a dict")


class TestXml(unittest.TestCase):
    """
    The TestXml class is used to test the various XML files that are part of a standard Indigo plugin.

    The files tested are listed in the setUpClass method below. The tests include checks for required elements (like
    element `id` and `type` attributes) and syntax.
    """
    @classmethod
    def setUpClass(cls):
        """ Set up the tests. """
        cls.xml_files   = ['../Actions.xml', '../MenuItems.xml', '../Devices.xml', '../Events.xml']
        cls.field_types = ['button', 'checkbox', 'colorpicker', 'label', 'list', 'menu', 'separator', 'textfield']
        # Load the plugin.py code into a var for testing later.
        with open('../plugin.py', 'r', encoding='utf-8') as infile:
            cls.plugin_lines = infile.read()

    @staticmethod
    def get_item_name(xml_file: str, item_id: int):
        """ Parse the xml file """
        tree = ET.parse(xml_file)
        return tree.getroot()

    def test_xml_files(self):
        """ Tests the various plugin XML files. """
        try:
            for file_type in self.xml_files:
                try:
                    root = self.get_item_name(file_type, 0)
                except FileNotFoundError:
                    print(f"\"{file_type}\" file not present.")
                    continue
                for item in root:
                    # Test the 'id' attribute (required):
                    node_id = item.get('id')
                    self.assertIsNotNone(node_id,
                                         f"\"{file_type}\" element \"{item.tag}\" attribute 'id' is required.")
                    self.assertIsInstance(node_id, str, "id names must be strings.")
                    self.assertNotIn(' ', node_id, "`id` names should not contain spaces.")

                    # Test the 'deviceFilter' attribute:
                    dev_filter = item.get('deviceFilter')
                    self.assertIsInstance(node_id, str, "`deviceFilter` values must be strings.")
                    if dev_filter:  # None if not specified in item attributes
                        self.assertIn(dev_filter, DEVICE_FILTERS, "'deviceFilter' values must be strings.")

                    # Test the 'uiPath' attribute:
                    # The uiPath value can essentially be anything as plugins can create their own uiPaths, so we
                    # can only test a few things regarding its contents.
                    ui_path = item.get('uiPath')
                    self.assertIsInstance(ui_path, str, "uiPath names must be strings.")
                    # self.assertIn(ui_path, self.ui_paths)

                # Test items that have a 'Name' element. The reference to `root.tag[:-1]` takes the tag name and
                # converts it to the appropriate child element name. For example, `Actions` -> `Action`, etc.
                for thing in root.findall(f"./{root.tag[:-1]}/Name"):
                    self.assertIsInstance(thing.text, str, "Action names must be strings.")

                # Test items that have a 'CallBackMethod` element:
                for thing in root.findall(f"./{root.tag[:-1]}/CallbackMethod"):
                    self.assertIsInstance(thing.text, str, "Action callback names must be strings.")
                    # We can't directly access the plugin.py file from here, so we read it into a variable instead.
                    # We then search for the string `def <CALLBACK METHOD>` within the file as a proxy to doing a
                    # `dir()` to see if it's in there.
                    self.assertTrue(f"def {thing.text}" in self.plugin_lines,
                                    f"The callback method \"{thing.text}\" does not exist in the plugin.py file.")

                # Test items that have a 'configUI' element
                for thing in root.findall(f"./{root.tag[:-1]}/ConfigUI/SupportURL"):
                    self.assertIsInstance(thing.text, str, "Config UI support URLs must be strings.")
                    result = httpx.get(thing.text).status_code
                    self.assertEqual(result, 200,
                                     f"ERROR: Got status code {result} -> {httpcodes[result]}.")

                # Test Config UI `Field` elements
                for thing in root.findall(f"./{root.tag[:-1]}/ConfigUI/Field"):
                    # Required attributes. Will throw a KeyError if missing.
                    self.assertIsInstance(thing.attrib['id'], str, "Config UI field IDs must be strings.")
                    self.assertFalse(thing.attrib['id'] == "", "Config UI field IDs must not be an empty string.")
                    self.assertIsInstance(thing.attrib['type'], str, "Config UI field types must be strings.")
                    self.assertIn(thing.attrib['type'].lower(), self.field_types,
                                  f"Config UI field types must be one of {self.field_types}.")
                    # Optional attributes
                    self.assertIsInstance(thing.attrib.get('defaultValue', ""), str,
                                          "Config UI defaultValue types must be strings.")
                    self.assertIsInstance(thing.attrib.get('enabledBindingId', ""), str,
                                          "Config UI enabledBindingId types must be strings.")
                    self.assertIsInstance(thing.attrib.get('enabledBindingNegate', ""), str,
                                          "Config UI enabledBindingNegate types must be strings.")
                    self.assertIn(thing.attrib.get('hidden', "false"), ['true', 'false'],
                                  "Config UI hidden attribute must be 'true' or 'false'.")
                    self.assertIn(thing.attrib.get('readonly', "false"), ['true', 'false'],
                                  "Config UI readonly attribute must be 'true' or 'false'.")
                    self.assertIn(thing.attrib.get('secure', "false"), ['true', 'false'],
                                  "Config UI secure attribute must be 'true' or 'false'.")
                    self.assertIsInstance(thing.attrib.get('tooltip', ""), str,
                                          "Config UI field tool tips must be strings.")
                    self.assertIsInstance(thing.attrib.get('visibleBindingId', ""), str,
                                          "Config UI visibleBindingId types must be strings.")
                    self.assertIsInstance(thing.attrib.get('visibleBindingValue', ""), str,
                                          "Config UI visibleBindingValue types must be strings.")

        except AssertionError as err:
            print(f"ERROR: {self._testMethodName}: {err}")
