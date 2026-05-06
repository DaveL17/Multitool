"""

"""
import dotenv
import httpx
import json
import os
from tests.shared import APIBase # noqa
from tests.shared.utils import run_host_script
import textwrap

dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


# ===================================== Plugin Actions =====================================
class TestPluginActions(APIBase):

    @classmethod
    def setUpClass(cls):
        pass

    @staticmethod
    def _execute_action(action_id: str, props: dict = None, wait: bool = True, msg_id: str = "test-plugin-action") -> bool | httpx.Response:
        """Post a plugin.executeAction command to the Indigo Web Server API.

        Args:
            action_id (str): The Indigo action ID to execute.
            props (dict): Optional action props to include in the payload.
            wait (bool): Whether to wait for the action to complete before returning.
            msg_id (str): Value for the message ``id`` field, used to identify the call in logs.

        Returns:
            bool | httpx.Response: The HTTP response, or False if the request failed.
        """
        try:
            message: dict = {
                "id":            msg_id,
                "message":       "plugin.executeAction",
                "pluginId":      os.getenv("PLUGIN_ID"),
                "actionId":      action_id,
                "waitUntilDone": wait,
            }
            if props is not None:
                message["props"] = props
            url = f"{os.getenv('URL_PREFIX')}/v2/api/command/?api-key={os.getenv('GOOD_API_KEY')}"
            return httpx.post(url, json=message, verify=False)
        except Exception:
            return False

    def _assert_response(self, result: bool | httpx.Response, msg: str) -> httpx.Response:
        """Assert that the result is a valid HTTP response, not a failed request.

        Args:
            result (bool | httpx.Response): The result from _execute_action.
            msg (str): Assertion failure message.

        Returns:
            httpx.Response: The validated response object.
        """
        self.assertIsInstance(result, httpx.Response, f"Request failed with exception: {msg}")
        return result

    def test_action_return_types(self):
        """Verify test_action_return returns the correct value for each supported return type."""
        base_props = {"field1": "a", "field2": "b", "field3": "c"}
        cases = [
            ("",              type(None)),
            (None,            type(None)),
            ("int",           int),
            ("float",         float),
            ("str",           str),
            ("tuple",         list),
            ("dict",          dict),
            ("list",          list),
            ("unrecognized",  type(None)),
        ]
        for return_value, expected_type in cases:
            with self.subTest(return_value=return_value):
                props       = {**base_props, "return_value": return_value}
                result      = self._assert_response(
                    self._execute_action(f"test_action_return",
                                         props=props,
                                         wait=True,
                                         msg_id=f"test_action_return_type_{return_value}"),
                    f"return_value={return_value!r}")
                result_json = json.loads(result.text)
                self.assertEqual(result.status_code, 200, f"Action call failed for return_value={return_value!r}")
                parsed = json.loads(result_json["reply_data"]) if result_json["reply_data"] != "null" else None
                self.assertIsInstance(parsed, expected_type, f"Unexpected type for return_value={return_value!r}")

    def test_email_battery_level_report(self):
        """Verify emailBatteryLevelReport executes successfully via the Indigo Web Server API."""
        props  = {
            "email_address": os.getenv("EMAIL_ADDRESS"),
            "email_device":  os.getenv("EMAIL_DEVICE_ID"),
        }
        result = self._assert_response(
            self._execute_action("emailBatteryLevelReport",
                                 props=props,
                                 wait=True,
                                 msg_id="test_email_battery_level_report"),
            "emailBatteryLevelReport")
        self.assertEqual(result.status_code, 200, "emailBatteryLevelReport action call was not successful.")

    def test_network_ping_device_action(self):
        """Verify networkPingDeviceAction executes successfully via the Indigo Web Server API."""
        props  = {"selected_device": os.getenv("NETWORK_PING_DEVICE_ID")}
        result = self._assert_response(
            self._execute_action("networkPingDeviceAction",
                                 props=props,
                                 wait=False,
                                 msg_id="test_network_ping_device_action"),
            "networkPingDeviceAction")
        self.assertEqual(result.status_code, 200, "networkPingDeviceAction action call was not successful.")

    def test_network_quality_action(self):
        """Verify networkQualityAction executes successfully via the Indigo Web Server API."""
        props  = {
            "runDownloadTest":    "true",
            "runUploadTest":      "true",
            "usePrivateRelay":    "false",
            "runTestsSequentially": "false",
            "verboseOutput":      "false",
            "outputVerification": "false",
        }
        result = self._assert_response(
            self._execute_action("networkQualityAction",
                                 props=props,
                                 wait=False,
                                 msg_id="test_network_quality_action"),
            "networkQualityAction")
        self.assertEqual(result.status_code, 200, "networkQualityAction action call was not successful.")

    def test_network_quality_device_action(self):
        """Verify networkQualityDeviceAction executes successfully via the Indigo Web Server API."""
        props  = {"selected_device": os.getenv("NETWORK_QUALITY_DEVICE_ID")}
        result = self._assert_response(
            self._execute_action("networkQualityDeviceAction",
                                 props=props,
                                 wait=False,
                                 msg_id="test_network_quality_device_action"),
            "networkQualityDeviceAction")
        self.assertEqual(result.status_code, 200, "networkQualityDeviceAction action call was not successful.")

    def test_modify_numeric_variable(self):
        """Verify modify_numeric_variable executes successfully via the Indigo Web Server API."""
        props  = {
            "list_of_variables": os.getenv("NUMERIC_VARIABLE_ID"),
            "modifier":          "+0",
        }
        action      = self._execute_action("modify_numeric_variable",
                                           props=props,
                                           wait=True,
                                           msg_id="test_modify_numeric_variable")
        result      = self._assert_response(action, "modify_numeric_variable")
        result_json = json.loads(result.text)
        self.assertEqual(result.status_code, 200, "modify_numeric_variable action call was not successful.")
        self.assertEqual(result_json["reply_data"], "true", "modify_numeric_variable returned False.")

    def test_modify_time_variable(self):
        """Verify modify_time_variable executes successfully via the Indigo Web Server API."""
        props  = {
            "list_of_variables": os.getenv("TIME_VARIABLE_ID"),
            "modifier":          "add",
            "days":              "0",
            "hours":             "0",
            "minutes":           "0",
            "seconds":           "0",
        }
        action      = self._execute_action("modify_time_variable",
                                           props=props,
                                           wait=True,
                                           msg_id="test_modify_time_variable")
        result      = self._assert_response(action, "modify_time_variable")
        result_json = json.loads(result.text)
        self.assertEqual(result.status_code, 200, "modify_time_variable action call was not successful.")
        self.assertEqual(result_json["reply_data"], "true", "modify_time_variable returned False.")


class TestPluginEvents(APIBase):

    @classmethod
    def setUpClass(cls):
        pass

    @staticmethod
    def _execute_trigger(trigger_id: int) -> bool | httpx.Response:
        """Post an indigo.trigger.execute command to the Indigo Web Server API.

        Args:
            trigger_id (int): The Indigo trigger object ID to execute.

        Returns:
            bool | httpx.Response: The HTTP response, or False if the request failed.
        """
        try:
            message: dict = {
                "id": "test-plugin-event-item",
                "message":  "indigo.trigger.execute",
                "objectId": trigger_id,
            }
            url = f"{os.getenv('URL_PREFIX')}/v2/api/command/?api-key={os.getenv('GOOD_API_KEY')}"
            return httpx.post(url, json=message, verify=False)
        except Exception:
            return False

    def _assert_response(self, result: bool | httpx.Response, msg: str) -> httpx.Response:
        """Assert that the result is a valid HTTP response, not a failed request.

        Args:
            result (bool | httpx.Response): The result from _execute_trigger.
            msg (str): Assertion failure message.

        Returns:
            httpx.Response: The validated response object.
        """
        self.assertIsInstance(result, httpx.Response, f"Request failed with exception: {msg}")
        return result

    def test_ping_offline_event(self):
        """Verify ping_offline trigger executes successfully via the Indigo Web Server API."""
        result = self._assert_response(
            self._execute_trigger(int(os.getenv("PING_OFFLINE_TRIGGER_ID"))),
            "ping_offline_event",
        )
        self.assertEqual(result.status_code, 200, "ping_offline trigger execution was not successful.")


class TestPluginMenuItems(APIBase):

    @classmethod
    def setUpClass(cls):
        pass

    @staticmethod
    def _execute_action(action_id: str, props: dict = None, wait: bool = True, msg_id: str = "test-plugin-menu-item") -> bool | httpx.Response:
        """Post a plugin.executeAction command to the Indigo Web Server API.

        Args:
            action_id (str): The Indigo action ID to execute.
            props (dict): Optional action props to include in the payload.
            wait (bool): Whether to wait for the action to complete before returning.
            msg_id (str): Value for the message ``id`` field, used to identify the call in logs.

        Returns:
            bool | httpx.Response: The HTTP response, or False if the request failed.
        """
        try:
            message: dict = {
                "id":            msg_id,
                "message":       "plugin.executeAction",
                "pluginId":      os.getenv("PLUGIN_ID"),
                "actionId":      action_id,
                "waitUntilDone": wait,
            }
            if props is not None:
                message["props"] = props
            url = f"{os.getenv('URL_PREFIX')}/v2/api/command/?api-key={os.getenv('GOOD_API_KEY')}"
            # Use a long timeout: the networkQuality CLI tool blocks the plugin thread
            # for up to ~60 s when test_network_quality_action runs before this class.
            return httpx.post(url, json=message, verify=False, timeout=90)
        except Exception:
            return False

    def _assert_response(self, result: bool | httpx.Response, msg: str) -> httpx.Response:
        """Assert that the result is a valid HTTP response, not a failed request.

        Args:
            result (bool | httpx.Response): The result from _execute_action.
            msg (str): Assertion failure message.

        Returns:
            httpx.Response: The validated response object.
        """
        self.assertIsInstance(result, httpx.Response, f"Request failed with exception: {msg}")
        return result

    def test_multi_tool_reports(self):
        """Verify each multiToolReports report executes successfully via the hidden menu_item_reports action."""
        report_keys = [
            "about_indigo",
            "battery_level_report",
            "environment_path",
            "indigo_inventory",
            "installed_plugins",
            "running_plugins",
            "pip_freeze_report",
            "log_plugin_environment",
        ]
        for key in report_keys:
            with self.subTest(report=key):
                result = self._assert_response(
                    self._execute_action("menu_item_reports",
                                         props={"actionMenu": key},
                                         wait=True,
                                         msg_id=f"test_multi-tool-reports-{key}"),
                    f"multiToolReports/{key}",
                )
                self.assertEqual(result.status_code, 200, f"multiToolReports/{key} was not successful.")

    def test_color_picker(self):
        """Verify pickColor menu item executes successfully by passing a predetermined color value."""
        chosen_color = "FF 00 80"
        props        = {"chosenColor": chosen_color}
        result       = self._assert_response(
            self._execute_action("menu_item_color_picker",
                                 props=props,
                                 wait=True,
                                 msg_id="test_color-picker"),
            "pickColor",
        )
        self.assertEqual(result.status_code, 200, "pickColor was not successful.")
        result_json = json.loads(result.text)
        self.assertIn("reply_data", result_json, "Response should always contain a 'reply_data' key.")
        if result_json["reply_data"] != "null":
            parsed = json.loads(result_json["reply_data"])
            self.assertIsInstance(parsed, list, "color_picker should return a list (tuple).")
            self.assertTrue(parsed[0], "color_picker return flag should be True.")
            self.assertEqual(parsed[1]["chosenColor"], chosen_color, "chosenColor should round-trip unchanged.")

    def test_beep_device(self):
        """Verify beepDevice menu item executes successfully via the hidden menu_item_beep_device action."""
        props  = {"listOfDevices": os.getenv("BEEP_DEVICE_ID")}
        result = self._assert_response(
            self._execute_action("menu_item_beep_device",
                                 props=props,
                                 wait=True,
                                 msg_id="test_beep-device"),
            "beepDevice",
        )
        self.assertEqual(result.status_code, 200, "beepDevice was not successful.")

    def test_device_inventory(self):
        """Verify deviceInventoryList menu item executes successfully via the hidden menu_item_device_inventory action."""
        props  = {"typeOfThing": "indigo.relay"}
        result = self._assert_response(
            self._execute_action("menu_item_device_inventory",
                                 props=props,
                                 wait=True,
                                 msg_id="test_device-inventory"),
            "deviceInventoryList",
        )
        self.assertEqual(result.status_code, 200, "deviceInventoryList was not successful.")

    def test_device_last_comm(self):
        """Verify deviceLastComm menu item executes successfully via the hidden menu_item_device_last_comm action."""
        props  = {"listOfDevices": os.getenv("GENERAL_DEVICE_ID")}
        result = self._assert_response(
            self._execute_action("menu_item_device_last_comm",
                                 props=props,
                                 wait=True,
                                 msg_id="test_device-last-comm"),
            "deviceLastComm",
        )
        self.assertEqual(result.status_code, 200, "deviceLastComm was not successful.")

    def test_ping_device(self):
        """Verify pingDevice menu item executes successfully via the hidden menu_item_ping_device action."""
        props  = {"listOfDevices": os.getenv("GENERAL_DEVICE_ID"), "suppressLogging": "true"}
        result = self._assert_response(
            self._execute_action("menu_item_ping_device",
                                 props=props,
                                 wait=False,
                                 msg_id="test_ping-device"),
            "pingDevice",
        )
        self.assertEqual(result.status_code, 200, "pingDevice was not successful.")

    def test_error_inventory(self):
        """Verify error_inventory menu item executes successfully via the hidden menu_item_error_inventory action."""
        props  = {"error_level": "err"}
        result = self._assert_response(
            self._execute_action("menu_item_error_inventory",
                                 props=props,
                                 wait=True,
                                 msg_id="test_error-inventory"),
            "error_inventory",
        )
        self.assertEqual(result.status_code, 200, "error_inventory was not successful.")

    def test_lorem_ipsum(self):
        """Verify lorem_ipsum menu item executes successfully via the hidden menu_item_lorem_ipsum action."""
        props  = {"text_level": "sentence"}
        result = self._assert_response(
            self._execute_action("menu_item_lorem_ipsum",
                                 props=props,
                                 wait=True,
                                 msg_id="test_lorem-ipsum"),
            "lorem_ipsum",
        )
        self.assertEqual(result.status_code, 200, "lorem_ipsum was not successful.")

    def test_indigo_signature(self):
        """Verify indigoSignature menu item executes successfully by passing known class and method values directly."""
        props  = {"list_of_indigo_classes": "server", "list_of_indigo_methods": "apiVersion"}
        result = self._assert_response(
            self._execute_action("menu_item_indigo_signature",
                                 props=props,
                                 wait=True,
                                 msg_id="test_indigo-signature"),
            "indigoSignature",
        )
        self.assertEqual(result.status_code, 200, "indigoSignature was not successful.")

    def test_method_signature(self):
        """Verify methodSignature menu item executes successfully by passing a known method name directly."""
        props  = {"list_of_plugin_methods": "debugLog"}
        result = self._assert_response(
            self._execute_action("menu_item_method_signature",
                                 props=props,
                                 wait=True,
                                 msg_id="test_method-signature"),
            "methodSignature",
        )
        self.assertEqual(result.status_code, 200, "methodSignature was not successful.")

    def test_network_ping(self):
        """Verify networkPing menu item executes successfully via the hidden menu_item_network_ping action."""
        props  = {"hostname": "8.8.8.8", "timeout": "1"}
        result = self._assert_response(
            self._execute_action("menu_item_network_ping",
                                 props=props,
                                 wait=True,
                                 msg_id="test_network-ping"),
            "networkPing",
        )
        self.assertEqual(result.status_code, 200, "networkPing was not successful.")

    def test_network_quality_menu(self):
        """Verify networkQuality menu item executes successfully via the hidden menu_item_network_quality action."""
        props  = {
            "runDownloadTest":      "true",
            "runUploadTest":        "true",
            "usePrivateRelay":      "false",
            "runTestsSequentially": "false",
            "verboseOutput":        "false",
            "outputVerification":   "false",
        }
        result = self._assert_response(
            self._execute_action("menu_item_network_quality",
                                 props=props,
                                 wait=False,
                                 msg_id="test_network-quality-menu"),
            "networkQuality",
        )
        self.assertEqual(result.status_code, 200, "networkQuality was not successful.")

    def test_print_dict(self):
        """Verify printDict Print Object Dict button executes successfully for a Schedule object."""
        props  = {"classOfThing": "schedules", "thingToPrint": os.getenv("SCHEDULE_ID")}
        result = self._assert_response(
            self._execute_action("menu_item_print_dict",
                                 props=props,
                                 wait=True,
                                 msg_id="test_print-dict"),
            "printDict/dict",
        )
        self.assertEqual(result.status_code, 200, "printDict/dict was not successful.")

    def test_print_dir(self):
        """Verify printDict Print Object Dir() button executes successfully for a Schedule object."""
        props  = {"classOfThing": "schedules", "thingToPrint": os.getenv("SCHEDULE_ID")}
        result = self._assert_response(
            self._execute_action("menu_item_print_dir",
                                 props=props,
                                 wait=True,
                                 msg_id="test_print-dir"),
            "printDict/dir",
        )
        self.assertEqual(result.status_code, 200, "printDict/dir was not successful.")

    def test_print_dependencies(self):
        """Verify printDict Print Object Dependencies button executes successfully for a Schedule object."""
        props  = {"classOfThing": "schedules", "thingToPrint": os.getenv("SCHEDULE_ID")}
        result = self._assert_response(
            self._execute_action("menu_item_print_dependencies",
                                 props=props,
                                 wait=True,
                                 msg_id="test_print-dependencies"),
            "printDict/dependencies",
        )
        self.assertEqual(result.status_code, 200, "printDict/dependencies was not successful.")

    def test_remove_delayed_actions(self):
        """Verify remove_all_delayed_actions menu item executes successfully via the hidden action."""
        result = self._assert_response(
            self._execute_action("menu_item_remove_delayed_actions",
                                 wait=True,
                                 msg_id="test_remove-delayed-actions"),
            "remove_all_delayed_actions",
        )
        self.assertEqual(result.status_code, 200, "remove_all_delayed_actions was not successful.")

    def test_embedded_scripts(self):
        """Verify embedded_scripts menu item executes successfully via the hidden menu_item_embedded_scripts action."""
        props  = {"search_string": ""}
        result = self._assert_response(
            self._execute_action("menu_item_embedded_scripts",
                                 props=props,
                                 wait=True,
                                 msg_id="test_embedded-scripts"),
            "embedded_scripts",
        )
        self.assertEqual(result.status_code, 200, "embedded_scripts was not successful.")

    def test_linked_scripts(self):
        """Verify linked_scripts menu item executes successfully via the hidden menu_item_linked_scripts action."""
        result = self._assert_response(
            self._execute_action("menu_item_linked_scripts",
                                 wait=True,
                                 msg_id="test_linked-scripts"),
            "linked_scripts",
        )
        self.assertEqual(result.status_code, 200, "linked_scripts was not successful.")

    def test_send_status_request(self):
        """Verify send_status_request menu item executes successfully via the hidden action."""
        props  = {"listOfDevices": os.getenv("GENERAL_DEVICE_ID")}
        result = self._assert_response(
            self._execute_action("menu_item_send_status_request",
                                 props=props,
                                 wait=True,
                                 msg_id="test_send-status-request"),
            "send_status_request",
        )
        self.assertEqual(result.status_code, 200, "send_status_request was not successful.")

    def test_get_serial_ports(self):
        """Verify get_serial_ports menu item executes successfully via the hidden menu_item_get_serial_ports action."""
        props  = {"ignoreBluetooth": "true"}
        result = self._assert_response(
            self._execute_action("menu_item_get_serial_ports",
                                 props=props,
                                 wait=True,
                                 msg_id="test_get-serial-ports"),
            "get_serial_ports",
        )
        self.assertEqual(result.status_code, 200, "get_serial_ports was not successful.")

    def test_speak_string(self):
        """Verify speak_string menu item executes successfully via the hidden menu_item_speak_string action."""
        props  = {"thingToSpeak": "test"}
        result = self._assert_response(
            self._execute_action("menu_item_speak_string",
                                 props=props,
                                 wait=True,
                                 msg_id="test_speak-string"),
            "speak_string",
        )
        self.assertEqual(result.status_code, 200, "speak_string was not successful.")

    def test_subscribe_to_changes(self):
        """Verify subscribeToChanges menu item executes successfully via the hidden action."""
        props  = {"enableSubscribeToChanges": "false", "subscribedDevices": ""}
        result = self._assert_response(
            self._execute_action("menu_item_subscribe_to_changes",
                                 props=props,
                                 wait=True,
                                 msg_id="test_subscribe-to-changes"),
            "subscribeToChanges",
        )
        self.assertEqual(result.status_code, 200, "subscribeToChanges was not successful.")

    def test_find_object_by_id_known_device(self):
        """Verify find_object_by_id runs successfully when given a known device ID."""
        props  = {"objectIds": os.getenv("GENERAL_DEVICE_ID")}
        result = self._assert_response(
            self._execute_action("menu_item_find_object_by_id",
                                 props=props,
                                 wait=True,
                                 msg_id="test_find-object-by-id-device"),
            "findObjectById/device",
        )
        self.assertEqual(result.status_code, 200, "findObjectById with known device ID was not successful.")

    def test_find_object_by_id_known_schedule(self):
        """Verify find_object_by_id runs successfully when given a known schedule ID."""
        props  = {"objectIds": os.getenv("SCHEDULE_ID")}
        result = self._assert_response(
            self._execute_action("menu_item_find_object_by_id",
                                 props=props,
                                 wait=True,
                                 msg_id="test_find-object-by-id-schedule"),
            "findObjectById/schedule",
        )
        self.assertEqual(result.status_code, 200, "findObjectById with known schedule ID was not successful.")

    def test_find_object_by_id_not_found(self):
        """Verify find_object_by_id runs successfully when the ID is not found in any collection."""
        props  = {"objectIds": "999999999"}
        result = self._assert_response(
            self._execute_action("menu_item_find_object_by_id",
                                 props=props,
                                 wait=True,
                                 msg_id="test_find-object-by-id-not-found"),
            "findObjectById/not-found",
        )
        self.assertEqual(result.status_code, 200, "findObjectById with non-existent ID was not successful.")

    def test_find_object_by_id_invalid_token(self):
        """Verify find_object_by_id runs successfully when the input is not an integer."""
        props  = {"objectIds": "abc"}
        result = self._assert_response(
            self._execute_action("menu_item_find_object_by_id",
                                 props=props,
                                 wait=True,
                                 msg_id="test_find-object-by-id-invalid"),
            "findObjectById/invalid",
        )
        self.assertEqual(result.status_code, 200, "findObjectById with non-integer token was not successful.")

    def test_find_object_by_id_known_folder(self):
        """Verify find_object_by_id correctly identifies a known folder ID."""
        props  = {"objectIds": os.getenv("FOLDER_ID")}
        result = self._assert_response(
            self._execute_action("menu_item_find_object_by_id",
                                 props=props,
                                 wait=True,
                                 msg_id="test_find-object-by-id-folder"),
            "findObjectById/folder",
        )
        self.assertEqual(result.status_code, 200, "findObjectById with known folder ID was not successful.")

    def test_find_object_by_id_mixed_input(self):
        """Verify find_object_by_id handles a mix of valid, not-found, and invalid tokens."""
        props  = {"objectIds": "%s, 999999999, abc" % os.getenv("GENERAL_DEVICE_ID")}
        result = self._assert_response(
            self._execute_action("menu_item_find_object_by_id",
                                 props=props,
                                 wait=True,
                                 msg_id="test_find-object-by-id-mixed"),
            "findObjectById/mixed",
        )
        self.assertEqual(result.status_code, 200, "findObjectById with mixed input was not successful.")
