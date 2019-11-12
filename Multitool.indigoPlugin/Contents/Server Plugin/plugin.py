#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

"""
The Multitool Plugin is an eclectic set of tools for use with Indigo

THe Multitool plugin provides a set of tools for use in using Indigo and for
use when developing plugins for Indigo.
"""

# =================================== TO DO ===================================

# TODO: Universal debugging

# ================================== IMPORTS ==================================

# Built-in modules
import datetime
import inspect
import logging
import os
import plistlib
import subprocess
import sys
import traceback

# Third-party modules
try:
    import indigo
except ImportError, error:
    indigo.server.log(unicode(error))
try:
    import pydevd
except ImportError:
    pass

# My modules
import DLFramework.DLFramework as Dave

# =================================== HEADER ==================================

__author__    = Dave.__author__
__copyright__ = Dave.__copyright__
__license__   = Dave.__license__
__build__     = Dave.__build__
__title__     = 'Multitool Plugin for Indigo Home Control'
__version__   = '1.0.25'

# =============================================================================

# kDefaultPluginPrefs = {}


class Plugin(indigo.PluginBase):

    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.pluginIsInitializing = True
        self.pluginIsShuttingDown = False

        self.error_msg_dict = indigo.Dict()
        self.plugin_file_handler.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d\t%(levelname)-10s\t%(name)s.%(funcName)-28s %(msg)s', datefmt='%Y-%m-%d %H:%M:%S'))
        self.debugLevel = int(self.pluginPrefs.get('showDebugLevel', '30'))
        self.indigo_log_handler.setLevel(self.debugLevel)

        # ====================== Initialize DLFramework =======================

        self.Fogbert = Dave.Fogbert(self)

        # Log pluginEnvironment information when plugin is first started
        self.Fogbert.pluginEnvironment()

        # ================ Subscribe to Indigo Object Changes =================
        if self.pluginPrefs.get('enableSubscribeToChanges', False):
            self.logger.warning(u"You have subscribed to device and variable changes. Disable this feature if not in use.")
            indigo.devices.subscribeToChanges()
            indigo.variables.subscribeToChanges()
            # indigo.triggers.subscribeToChanges()      # Not implemented
            # indigo.schedules.subscribeToChanges()     # Not implemented
            # indigo.actionGroups.subscribeToChanges()  # Not implemented
            # indigo.controlPages.subscribeToChanges()  # Not implemented

        # try:
        #     pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
        # except:
        #     pass

        self.pluginIsInitializing = False

    # =============================================================================
    # ============================== Indigo Methods ===============================
    # =============================================================================
    def closedPrefsConfigUi(self, values_dict=None, user_cancelled=None):

        self.logger.debug(u"Call to closedPrefsConfigUi")

        if not user_cancelled:
            self.debugLevel = int(values_dict.get('showDebugLevel', '20'))
            self.indigo_log_handler.setLevel(self.debugLevel)

            # Ensure that self.pluginPrefs includes any recent changes.
            for k in values_dict:
                self.pluginPrefs[k] = values_dict[k]

            return values_dict

    # =============================================================================
    def deviceUpdated(self, orig_dev, new_dev):

        # Call the base implementation first just to make sure all the right
        # things happen elsewhere
        indigo.PluginBase.deviceUpdated(self, orig_dev, new_dev)

        # If subscribe to changes is enabled
        if self.pluginPrefs.get('enableSubscribeToChanges', False):

            track_list = self.pluginPrefs.get('subscribedDevices', '')
            if track_list == '':
                subscribed_items = []
            else:
                subscribed_items = [int(_) for _ in track_list.replace(' ', '').split(',')]

            # If dev id in list of tracked items
            if orig_dev.id in subscribed_items:

                # Attribute changes
                exclude_list = ('globalProps', 'lastChanged', 'lastSuccessfulComm', 'ownerProps', 'states')
                attrib_list = [attr for attr in dir(orig_dev) if not callable(getattr(orig_dev, attr)) and '__' not in attr and attr not in exclude_list]
                attrib_dict = {attrib: (getattr(orig_dev, attrib), getattr(new_dev, attrib)) for attrib in attrib_list if getattr(orig_dev, attrib) != getattr(new_dev, attrib)}

                # Property changes
                orig_props = dict(orig_dev.ownerProps)
                new_props = dict(new_dev.ownerProps)
                props_dict = {key: (orig_props[key], new_props[key]) for key in orig_props if orig_props[key] != new_props[key]}

                # State changes
                state_dict = {key: (orig_dev.states[key], val) for key, val in new_dev.states.iteritems() if key not in orig_dev.states or val != orig_dev.states[key]}

                if len(attrib_dict) > 0 or len(state_dict) > 0 or len(props_dict) > 0:
                    indigo.server.log(u"\nDevice Changes: [{0}]\n{1:<8}{2}\n{3:<8}{4}\n{5:<8}{6}".format(new_dev.name, 'Attr:', attrib_dict, 'Props', props_dict, 'States', state_dict))

    # =============================================================================
    def getMenuActionConfigUiValues(self, menu_id):

        # Grab the setting values for the Subscribe to Changes tool
        if menu_id == 'subscribeToChanges':

            changes_dict = indigo.Dict()
            changes_dict['enableSubscribeToChanges'] = self.pluginPrefs.get('enableSubscribeToChanges', False)
            changes_dict['subscribedDevices'] = self.pluginPrefs.get('subscribedDevices', '')

            return changes_dict

        else:
            return indigo.Dict()

    # =============================================================================
    def sendDevicePing(self, dev_id=0, suppress_logging=False):

        indigo.server.log(u"Multitool Plugin devices do not support the ping function.")
        return {'result': 'Failure'}

    # =============================================================================
    def startup(self):

        # =========================== Audit Indigo Version ============================
        self.Fogbert.audit_server_version(min_ver=7)

    # =============================================================================
    def variableUpdated(self, orig_var, new_var):

        # Call the base implementation first just to make sure all the right
        # things happen elsewhere
        indigo.PluginBase.variableUpdated(self, orig_var, new_var)

        # If subscribe to changes is enabled
        if self.pluginPrefs.get('enableSubscribeToChanges', False):

            track_list = self.pluginPrefs.get('subscribedDevices', '')
            if track_list == '':
                subscribed_items = []
            else:
                subscribed_items = [int(_) for _ in track_list.replace(' ', '').split(',')]

            # If var id in list of tracked items
            if orig_var.id in subscribed_items:

                # Attribute changes
                exclude_list = ('globalProps', 'lastChanged', 'lastSuccessfulComm')
                attrib_list = [attr for attr in dir(orig_var) if not callable(getattr(orig_var, attr)) and '__' not in attr and attr not in exclude_list]
                attrib_dict = {attrib: (getattr(orig_var, attrib), getattr(new_var, attrib)) for attrib in attrib_list if getattr(orig_var, attrib) != getattr(new_var, attrib)}

                # Variable value
                val_dict = {}
                if orig_var.value != new_var.value:
                    val_dict = {new_var.name: (orig_var.value, new_var.value)}

                if len(attrib_dict) > 0 or len(val_dict):
                    indigo.server.log(u"\nVariable Changes: [{0}]\n{1:<8}{2}\n{3:<8}{4}".format(new_var.name, 'Attr:', attrib_dict, 'Value', val_dict))

    # =============================================================================
    def validatePrefsConfigUi(self, values_dict):

        return True, values_dict

    # =============================================================================
    # ============================== Plugin Methods ===============================
    # =============================================================================
    def __dummyCallback__(self, values_dict=None, type_id=""):
        """
        Dummy callback to cause refresh of dialog elements

        The __dummyCallback__ method is used and a placeholder callback to force a
        refresh of dialog elements based for controls with dynamic refresh attributes.

        -----
        :param values_dict:
        :param type_id:
        :return:
        """

        pass

    # =============================================================================
    def about_indigo(self):
        """
        Prints information about the Indigo environment to the events log

        The about_indigo method prints select Indigo environment information to the
        Indigo events log. It can be a useful tool to get a user to quickly print
        relevant environment information for trouble-shooting.

        -----

        :return:
        """

        self.logger.debug(u"Call to about_indigo")
        lat_long  = indigo.server.getLatitudeAndLongitude()
        latitude  = lat_long[0]
        longitude = lat_long[1]
        indigo.server.log(u"{0:{1}^130}".format(u" Indigo Status Information ", u"="))
        indigo.server.log(u"Server Version: {0}".format(indigo.server.version))
        indigo.server.log(u"API Version: {0}".format(indigo.server.apiVersion))
        indigo.server.log(u"Server IP Address: {0}".format(indigo.server.address))
        indigo.server.log(u"Install Path: {0}".format(indigo.server.getInstallFolderPath()))
        indigo.server.log(u"Database: {0}/{1}".format(indigo.server.getDbFilePath(), indigo.server.getDbName()))
        indigo.server.log(u"Port Number: {0}".format(indigo.server.portNum))
        indigo.server.log(u"Latitude and Longitude: {0}/{1}".format(latitude, longitude))

        if indigo.server.connectionGood:
            indigo.server.log(u"Connection Good.".format(indigo.server.connectionGood))
        else:
            indigo.server.log(u"Connection Bad.".format(indigo.server.connectionGood), isError=True)

    # =============================================================================
    def color_picker(self, values_dict=None, type_id=""):
        """
        Print color information to the Indigo events log

        Write color information to the Indigo events log to include the raw, hex, and
        RGB values.

        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        self.logger.debug(u"Call to color_picker")
        if not values_dict['chosenColor']:
            values_dict['chosenColor'] = "FF FF FF"
        indigo.server.log(u"Raw: {0}".format(values_dict['chosenColor']))
        indigo.server.log(u"Hex: #{0}".format(values_dict['chosenColor'].replace(' ', '')))
        indigo.server.log(u"RGB: {0}".format(tuple([int(thing, 16) for thing in values_dict['chosenColor'].split(' ')])))
        return True

    # =============================================================================
    def device_dependencies(self, values_dict=None, type_id=""):
        """
        Print a list of device dependencies to the Indigo events log

        The device_dependencies method prints a list of known dependencies for a
        selected Indigo device.

        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        self.logger.debug(u"Call to device_dependencies")
        err_msg_dict = indigo.Dict()

        try:
            dependencies = indigo.device.getDependencies(int(values_dict['listOfDevices']))
            indigo.server.log(u"{0:{1}^80}".format(u" {0} Dependencies ".format(indigo.devices[int(values_dict['listOfDevices'])].name), u"="))
            indigo.server.log(unicode(dependencies))

        except StandardError as err:
            self.logger.critical(u"Error obtaining dependencies.")
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Device dependencies Error.\n\nReason: {0}".format(err)
            return False, values_dict, err_msg_dict

    # =============================================================================
    def device_inventory(self, values_dict=None, type_id=""):
        """
        Print an inventory of Indigo devices to the Indigo events log

        The device_inventory method prints an inventory of all Indigo devices to the
        Indigo events log.

        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        self.logger.debug(u"Call to device_inventory")

        filter_item = ""

        if values_dict['typeOfThing'] not in ('Other', 'pickone'):
            filter_item = values_dict['typeOfThing']
            x = [[dev.id, dev.address, dev.name, dev.lastChanged] for dev in indigo.devices.iter(filter=filter_item)]

        elif values_dict['typeOfThing'] == 'Other' and len(values_dict['customThing']) > 0:
            filter_item = values_dict['customThing']
            x = [[dev.id, dev.address, dev.name, dev.lastChanged] for dev in indigo.devices.iter(filter=filter_item)]

        else:
            x = []

        if len(x) > 0:
            # ====================== Generate Custom Table Settings =======================

            x0 = max([len(unicode(thing[0])) for thing in x]) + 2
            x1 = max([len(unicode(thing[1])) for thing in x]) + 5
            x2 = max([len(unicode(thing[2])) for thing in x]) + 2
            x3 = max([len(unicode(thing[3])) for thing in x])
            table_width = sum((x0, x1, x2, x3))

            indigo.server.log(u"{0:=^{1}}".format(u" Inventory of '{0}' Devices ".format(filter_item), table_width))
            indigo.server.log(u"{0:<{1}} {2:<{3}} {4:<{5}} {6:<{7}}".format(u"ID", (x0 - 1), u"Addr", (x1 - 1), u"Name", (x2 - 1), u"Last Changed", x3))
            indigo.server.log(u"{0}".format(u'=' * table_width))

            # ============================= Output the Table ==============================
            for thing in x:
                indigo.server.log(u"{0:<{1}} {2:<{3}} {4:<{5}} {6:<{7}}".format(thing[0], (x0 - 1),
                                                                                u"[{0}]".format(thing[1]), (x1 - 1),
                                                                                thing[2], (x2 - 1),
                                                                                datetime.datetime.strftime(thing[3], '%Y-%m-%d %H:%M:%S'), x3))
        else:
            if values_dict['typeOfThing'] not in ('Other', 'pickone'):
                indigo.server.log(u"No {0} devices found.".format(values_dict['typeOfThing']))
            elif values_dict['typeOfThing'] == 'Other' and len(values_dict['customThing']) > 0:
                indigo.server.log(u"No {0} devices found.".format(values_dict['customThing']))

        return values_dict

    # =============================================================================
    def device_last_successful_comm(self):
        # TODO: Add a config menu and filter so users can list a subset of devices, and be able to generate multiple reports without revisiting the tool.
        """
        Print information on the last successful communication with a device

        The device_last_successful_comm method prints information on the last successful
        communication with each Indigo device to the Indigo events log.

        -----

        :return:
        """

        self.logger.debug(u"Call to device_last_successful_comm")

        # Get the data we need
        table = [(dev.id, dev.name, dev.lastSuccessfulComm) for dev in indigo.devices.iter()]

        # Sort the data from newest to oldest
        table = sorted(table, key=lambda (dev_id, name, comm): comm, reverse=True)

        # Find the length of the longest device name
        length = 0
        for element in table:
            if len(element[1]) > length:
                length = len(element[1])

        # Output the result
        indigo.server.log(u"{0:=^{1}}".format(u" Device Last Successful Comm ", 100))
        indigo.server.log(u"{id:<14}{name:<{length}}  {commTime}".format(id=u"ID", name=u"Name", commTime=u"Last Comm Success", length=length))
        indigo.server.log(u"{0}".format(u'=' * 100))
        for element in table:
            indigo.server.log(u"{id:<14}{name:<{length}}  {commTime}".format(id=element[0], name=element[1], commTime=element[2], length=length))

    # =============================================================================
    def device_to_beep(self, values_dict=None, type_id=""):
        """
        Send a beep request to a device

        The device_to_beep method will send a beep request to a selected Indigo device.
        Only select devices support the beep request and only enabled devices are
        displayed for selection.

        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        self.logger.debug(u"Call to device_to_beep")

        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(u"{0:{1}^80}".format(u" Send Beep to {0} ".format(indigo.devices[int(values_dict['listOfDevices'])].name), u"="))
            indigo.device.beep(int(values_dict['listOfDevices']), suppressLogging=False)
            return True

        except ValueError:
            err_msg_dict['listOfDevices'] = u"You must select a device to receive the beep request"
            err_msg_dict['showAlertText'] = u"Beep Error.\n\nReason: No device selected."
            return False, values_dict, err_msg_dict

        except StandardError as err:
            self.logger.critical(u"Error sending beep request.")
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Beep Error.\n\nReason: {0}".format(err)
            return False, values_dict, err_msg_dict

    # =============================================================================
    def device_to_ping(self, values_dict=None, type_id=""):
        """
        Send a ping request to a device

        The device_to_ping method will send a ping request to a selected Indigo device.
        Only enabled devices are displayed. Plugin devices must support sendDevicePing
        method and plugin must be enabled.

        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        self.logger.debug(u"Call to device_to_ping")

        dev_id = int(values_dict['listOfDevices'])

        try:
            if indigo.devices[dev_id].enabled:
                indigo.server.log(u"{0:{1}^80}".format(u" Pinging device: {0} ".format(indigo.devices[dev_id].name), u"="))
                result = indigo.device.ping(dev_id, suppressLogging=False)
                indigo.server.log(unicode(result))
                return True

        except Exception as err:
            self.logger.critical(u"Error sending ping: {0}".format(err))

    # =============================================================================
    def dict_to_print(self, filter_item="", values_dict=None, target_id=""):
        """
        Return a list of Indigo objects for inspection

        The dict_to_print method will return a list of objects for inspection. Objects
        that are supported include Actions, Control Pages, Devices, Schedules,
        Triggers, and variables. It is called by the Object Dictionary... menu item in
        conjunction with the results_output method.

        -----

        :param filter_item:
        :param values_dict:
        :param target_id:
        :return:
        """

        self.logger.debug(u"Call to dict_to_print")

        if not values_dict:
            return [("none", "None")]
        else:
            return [(thing.id, thing.name) for thing in getattr(indigo, values_dict['classOfThing'])]

    # =============================================================================
    def environment_path(self):
        """
        Print the Indigo server's environment path variable to the Indigo Events log

        the environment_path method outputs the value of the server computer's
        environment path variable to the Indigo events log. This can help with trouble-
        shooting--for example, when an expected import statement fails.

        -----

        :return:
        """

        self.logger.debug(u"Call to environment_path")

        indigo.server.log(u"{0:{1}^130}".format(u" Current System Path ", u"="))
        for p in sys.path:
            indigo.server.log(p)
        indigo.server.log(u"{0:{1}^130}".format(u" (Sorted) ", u"="))
        for p in sorted(sys.path):
            indigo.server.log(p)

    # =============================================================================
    def error_inventory(self, values_dict=None, type_id=""):
        """
        Create an inventory of error messages appearing in the Indigo Logs.

        The error_inventory method will scan log files and parse out any log lines than
        contain the term 'error'. It is agnostic as to whether the log line is an
        actual error or a debug statement that contains the term error.

        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        self.logger.debug(u"Call to error_inventory")

        check_list = (' Err ', ' err ', 'Error', 'error')
        log_folder = u"{0}/".format(indigo.server.getLogsFolderPath())

        # ========================= Create a Unique Filename ==========================
        i = 1
        while os.path.exists(u"{0}Multitool Plugin Error Inventory {1}.txt".format(log_folder, i)):
            i += 1

        full_path = u"{0}Multitool Plugin Error Inventory {1}.txt".format(log_folder, i)

        # ============================= Iterate Log Files =============================
        with open(full_path, 'w') as outfile:

            for root, sub, files in os.walk(log_folder):
                for filename in files:
                    # if filename.endswith((".log", ".txt")) and filename != 'error_inventory.txt':
                    if filename.endswith((".log", ".txt")) and not filename.startswith('Multitool Plugin Error Inventory'):
                        with open(os.path.join(root, filename), "r") as infile:
                            log_file = infile.read()

                            for line in log_file.split('\n'):
                                if any(item in line for item in check_list):
                                    outfile.write("{0:<130}{1}\n".format(root + filename, line))

        indigo.server.log(u"Error message inventory saved to: {0}".format(full_path))
        return True

    # =============================================================================
    def generator_device_list(self, filter_item="", values_dict=None, type_id="", target_id=0):
        """
        Returns a list of plugin devices.

        The generator_device_list method passes a list of Indigo devices to the calling
        control. It is a connector to the generator which is located in the DLFramework
        module.

        -----

        :param filter_item:
        :param values_dict:
        :param type_id:
        :param target_id:
        :return:
        """

        self.logger.debug(u"generator_device_list() called.")

        return self.Fogbert.deviceList(filter=None)

    # =============================================================================
    def generator_enabled_device_list(self, filter_item="", values_dict=None, type_id="", target_id=0):
        """
        Returns a list of enabled plugin devices.

        The generator_enabled_device_list passes a list of enabled Indigo devices to the
        calling control. It is a connector to the generator which is located in the
        DLFramework module.

        -----

        :param filter_item:
        :param values_dict:
        :param type_id:
        :param target_id:
        :return:
        """

        self.logger.debug(u"generator_device_list() called.")

        return self.Fogbert.deviceListEnabled(filter=None)

    # =============================================================================
    def generator_dev_var(self, filter_item="", values_dict=None, type_id="", target_id=0):
        """
        Return a list of Indigo devices and variables

        The generator_dev_var method collects IDs and names for all Indigo devices and
        variables. It creates a list of the form:

        [(dev.id, dev.name), (var.id, var.name)].

        -----

        :param filter_item:
        :param values_dict:
        :param type_id:
        :param target_id:
        :return:
        """

        self.logger.debug(u"generator_dev_var() called.")

        return self.Fogbert.deviceAndVariableList()

    # =============================================================================
    def generator_state_or_value(self, filter_item="", values_dict=None, type_id="", target_id=0):
        """
        Return a list of device states and variable values

        The generator_state_or_value() method returns a list to populate the relevant
        device states or variable value to populate a menu control.

        -----

        :param filter_item:
        :param values_dict:
        :param type_id:
        :param target_id:
        :return:
        """

        self.logger.debug(u"generator_state_or_value() called.")

        try:
            id_number = int(values_dict['devVarMenu'])

            if id_number in indigo.devices.keys():
                state_list = [(state, state) for state in indigo.devices[id_number].states if not state.endswith('.ui')]
                state_list.remove(('onOffState', 'onOffState'))
                return state_list

            elif id_number in indigo.variables.keys():
                return [('value', 'Value')]

        except (KeyError, ValueError):
            return [(0, 'Pick a Device or Variable')]

    # =============================================================================
    def generator_substitutions(self, values_dict=None, type_id="", target_id=0):
        """
        Generate the construct for an Indigo substitution

        The generator_substitutions method is used with the Substitution Generator. It
        is the callback that's used to create the Indigo substitution construct.

        -----

        :param values_dict:
        :param type_id:
        :param target_id:
        :return:
        """

        self.logger.debug(u"generator_substitutions() called.")

        dev_var_id    = values_dict['devVarMenu']
        dev_var_value = values_dict['generator_state_or_value']

        if int(values_dict['devVarMenu']) in indigo.devices.keys():
            indigo.server.log(u"Indigo Device Substitution: %%d:{0}:{1}%%".format(dev_var_id, dev_var_value))

        else:
            indigo.server.log(u"Indigo Variable Substitution: %%v:{0}%%".format(dev_var_id))

        values_dict['devVarMenu'] = ''
        values_dict['generator_state_or_value'] = ''

        return values_dict

    # =============================================================================
    def get_serial_ports(self, values_dict=None, type_id=""):
        """
        Print a list of serial ports to the Indigo events log

        The get_serial_ports method prints a list of available serial ports to the Indigo
        events log.

        -----

        :return:
        """

        self.logger.debug(u"Call to get_serial_ports")

        # ========================= Filter Bluetooth Devices ==========================
        if values_dict.get('ignoreBluetooth', False):
            port_filter = "indigo.ignoreBluetooth"
        else:
            port_filter = ""

        # ============================= Print the Report ==============================
        indigo.server.log(u"{0:{1}^80}".format(u" Current Serial Ports ", u"="))

        for k, v in indigo.server.getSerialPorts(filter=u"{0}".format(port_filter)).items():
            indigo.server.log(u"{0:40} {1}".format(k, v))

        return True

    # =============================================================================
    def indigo_inventory(self):

        # ============================== Build Inventory ==============================
        inventory = {'Action Groups': [], 'Control Pages': [], 'Devices': [], 'Schedules': [], 'Triggers': [], 'Variables': []}

        for action in indigo.actionGroups.iter():
            inventory['Action Groups'].append((action.id, action.name, action.folderId, indigo.actionGroups.folders.getName(action.folderId)))

        for page in indigo.controlPages.iter():
            inventory['Control Pages'].append((page.id, page.name, page.folderId, indigo.controlPages.folders.getName(page.folderId)))

        for dev in indigo.devices.iter():
            inventory['Devices'].append((dev.id, dev.name, dev.folderId, indigo.devices.folders.getName(dev.folderId)))

        for schedule in indigo.schedules.iter():
            inventory['Schedules'].append((schedule.id, schedule.name, schedule.folderId, indigo.schedules.folders.getName(schedule.folderId)))

        for trigger in indigo.triggers.iter():
            inventory['Triggers'].append((trigger.id, trigger.name, trigger.folderId, indigo.triggers.folders.getName(trigger.folderId)))

        for var in indigo.variables.iter():
            inventory['Variables'].append((var.id, var.name, var.folderId, indigo.variables.folders.getName(var.folderId)))

        # ====================== Generate Custom Table Settings =======================
        col_0 = []
        col_1 = []
        col_2 = []
        col_3 = []

        for key in inventory.keys():
            col_0 += [item[0] for item in inventory[key]]
            col_1 += [item[1] for item in inventory[key]]
            col_2 += [item[2] for item in inventory[key]]
            col_3 += [item[3] for item in inventory[key]]

        col0 = max([len(str(item)) for item in col_0]) + 2
        col1 = max([len(str(item)) for item in col_1]) + 2
        col2 = max([len(str(item)) for item in col_2]) + 2
        col3 = max([len(str(item)) for item in col_3]) + 2

        table_width = sum([col0, col1, col2, col3])

        # ============================= Output the Table ==============================
        for object_type in sorted(inventory):
            header = u" {0} ".format(object_type)
            indigo.server.log(u"{0:{1}^{2}}".format(header, '=', table_width))

            indigo.server.log(u"{0:{1}}{2:{3}}{4:{5}}{6:{7}}".format(u'ID', col0, u'Name', col1, u'Folder ID', col2, u'Folder Name', col3))
            indigo.server.log(u"{0:{1}^{2}}".format("", '=', table_width))

            for element in inventory[object_type]:
                indigo.server.log(u"{0:{1}}{2:{3}}{4:{5}}{6:{7}}".format(str(element[0]), col0, str(element[1]), col1, str(element[2]), col2, str(element[3]), col3))

        indigo.server.log(u"{0:{1}^{2}}".format(u" Summary ", '=', table_width))

        for object_type in sorted(inventory):
            indigo.server.log(u"{0:15}{1}".format(object_type, len(inventory[object_type])))

    # =============================================================================
    def inspect_method(self, values_dict=None, type_id=""):
        """
        Print the signature of an Indigo method to the Indigo events log

        The inspect_method method will inspect a selected Indigo method and print the
        target method's signature to the Indigo events log. This is useful when the
        signature of an Indigo method is unknown.  It will return a list of attributes
        passed by the Indigo method.  For example,

        .. code-block::

           Multitool    self.closedPrefsConfigUi: ArgSpec(args=['self', 'valuesDict', 'userCancelled'], varargs=None, keywords=None, defaults=None)
           Multitool    Docstring:  User closes config menu. The validatePrefsConfigUI() method will also be called.


        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        self.logger.debug(u"Call to inspect_method")

        method = getattr(self, values_dict['list_of_plugin_methods'])
        signature = inspect.getargspec(method)
        indigo.server.log(u"self.{0}: {1}".format(values_dict['list_of_plugin_methods'], signature))
        indigo.server.log(u"Docstring: {0}".format(getattr(self, values_dict['list_of_plugin_methods']).__doc__), isError=False)

    # =============================================================================
    def installed_plugins(self):

        """
        Print a list of installed plugins to the Indigo events log

        The installed_plugins method will print a list of installed plugins to the
        Indigo events log along with the plugin's bundle identifier. In instances
        where the plugin is disabled, [Disabled] will be appended to the log line.

        -----

        :return:
        """

        self.logger.debug(u"Call to installed_plugins")

        plugin_name_list = []
        indigo_install_path = indigo.server.getInstallFolderPath()

        for plugin_folder in ('Plugins', 'Plugins (Disabled)'):
            plugins_list = os.listdir(indigo_install_path + '/' + plugin_folder)

            for plugin in plugins_list:

                # Check for Indigo Plugins and exclude 'system' plugins
                if (plugin.lower().endswith('.indigoplugin')) and (not plugin[0:1] == '.'):

                    # retrieve plugin Info.plist file
                    pl = plistlib.readPlist(u"{0}/{1}/{2}/Contents/Info.plist".format(indigo_install_path, plugin_folder, plugin))
                    cf_bundle_identifier = pl["CFBundleIdentifier"]

                    # Don't include self (i.e. this plugin) in the plugin list
                    cf_bundle_display_name = pl["CFBundleDisplayName"]

                    # if disabled plugins folder, append 'Disabled' to name
                    if plugin_folder == 'Plugins (Disabled)':
                        cf_bundle_display_name += ' [Disabled]'

                    plugin_name_list.append((u"{0:45}{1}".format(cf_bundle_display_name, cf_bundle_identifier)))

        indigo.server.log(u"{0:{1}^130}".format(u" Installed Plugins ", u"="))

        for thing in plugin_name_list:
            indigo.server.log(u'{0}'.format(thing))

        indigo.server.log(u"{0:{1}^130}".format(u" Code Credit: Autolog ", u"="))

    # =============================================================================
    def list_of_plugin_methods(self, filter_item="", values_dict=None, target_id=""):
        """
        Generates a list of Indigo plugin methods for inspection

        The list_of_plugin_methods method will generate a list of Indigo plugin
        methods available for inspection. It is used to populate the list of
        methods control for the Methods - Plugin Base... tool.

        -----

        :param filter_item:
        :param values_dict:
        :param target_id:
        :return:
        """

        self.logger.debug(u"Call to list_of_plugin_methods")

        list_of_attributes = []

        for method in dir(indigo.PluginBase):
            try:
                inspect.getargspec(getattr(indigo.PluginBase, method))
                list_of_attributes.append((method, u"self.{0}".format(method)))

            except (AttributeError, TypeError):
                continue

        return list_of_attributes

    # =============================================================================
    @staticmethod
    def list_of_indigo_classes(filter_item="", values_dict=None, target_id=""):
        """
        Generates a list of Indigo classes for inspection

        The list_of_indigo_classes method will generate a list of Indigo classes
        available for inspection. It is used to populate the list of classes
        control for the Methods - Indigo Base... tool.

        -----

        :param filter_item:
        :param values_dict:
        :param target_id:
        :return:
        """

        return [(u"{0}".format(_), u"indigo.{0}".format(_)) for _ in sorted(dir(indigo), key=str.lower)]

    # =============================================================================
    @staticmethod
    def list_of_indigo_methods(filter_item="", values_dict=None, target_id=""):
        """
        Generates a list of Indigo methods for inspection

        The list_of_indigo_methods method will generate a list of Indigo methods
        available for inspection. It is used to populate the list of methods
        control for the Methods - Indigo Base... tool.

        -----

        :param filter_item:
        :param values_dict:
        :param target_id:
        :return:
        """
        if len(values_dict.keys()) == 0:
            return []

        else:
            foo = getattr(indigo, values_dict['list_of_indigo_classes'])
            directory = dir(foo)

            return [_ for _ in directory]

    # =============================================================================
    @staticmethod
    def log_of_method(values_dict=None, type_id=""):
        """
        Logs the inspection of the passed class/method

        The log_of_method method will generate an inspection of the passed class and
        method (i.e., indigo.server.log) and write the result to the Indigo
        Activity Log.

        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        method_to_call = getattr(indigo, values_dict['list_of_indigo_classes'])
        method_to_call = getattr(method_to_call, values_dict['list_of_indigo_methods'])
        inspector = inspect.getdoc(method_to_call)
        indigo.server.log(u"\nindigo.{0}.{1}".format(values_dict['list_of_indigo_classes'], inspector))

    # =============================================================================
    def remove_all_delayed_actions(self, values_dict=None, type_id=""):
        """
        Removes all delayed actions from the Indigo server

        The remove_all_delayed_actions method is a convenience tool to remove all delayed
        actions from the Indigo server.

        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        self.logger.debug(u"Call to remove_all_delayed_actions")
        indigo.server.removeAllDelayedActions()
        return True

    # =============================================================================
    def running_plugins(self):
        """
        Print a list of running plugins to the Indigo events log

        The running_plugins method prints a table of Indigo plugins that are currently
        enabled. It includes system and other information that is useful for trouble-
        shooting purposes.

        Display the uid, pid, parent pid, recent CPU usage, process start time,
        controlling tty, elapsed CPU usage, and the associated command.  If the -u
        option is also used, display the user name rather then the numeric uid.  When
        -o or -O is used to add to the display following -f, the command field is not
        truncated as severely as it is in other formats.

        -----

        :return:
        """

        self.logger.debug(u"Call to running_plugins")

        ret = subprocess.Popen("/bin/ps -ef | grep 'MacOS/IndigoPluginHost' | grep -v grep", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        indigo.server.log(u"\n{0:{1}^120}".format(u" Running Plugins (/bin/ps -ef) ", u"="))
        indigo.server.log(u"\n{0}\n\n{1}".format(u"  uid - pid - parent pid - recent CPU usage - process start time - controlling tty - elapsed CPU usage - associated command", ret))

    # =============================================================================
    def results_output(self, values_dict=None, caller=None):
        """
        Print an Indigo object's properties dict to the Indigo events log

        The results_output method formats an object properties dictionary for output to
        the Indigo events log. It's used in conjunction with the Object Dictionary...
        tool.

        -----

        :param values_dict:
        :param caller:
        :return:
        """

        self.logger.debug(u"Call to results_output")
        self.logger.debug(u"Caller: {0}".format(caller))

        thing = getattr(indigo, values_dict['classOfThing'])[int(values_dict['thingToPrint'])]
        indigo.server.log(u"{0:{1}^80}".format(u" {0} Dict ".format(thing.name), u"="))
        indigo.server.log(u"\n{0}".format(thing))
        indigo.server.log(u"{0:{1}^80}".format(u"", u"="))

    # =============================================================================
    def send_status_request(self, values_dict=None, type_id=""):
        """
        Send a status request to an Indigo object

        The send_status_request method will send a status request inquiry to a selected
        Indigo object. Note that not all objects support a status request and plugin
        devices that support status requests must have their host plugin enabled.
        Further, only enabled objects are available for a status request.

        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        self.logger.debug(u"Call to send_status_request")
        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(u"{0:{1}^80}".format(u" Sending Status Request ", u"="))
            indigo.device.statusRequest(int(values_dict['listOfDevices']), suppressLogging=False)
            return True

        except StandardError as err:
            self.logger.critical(u"Error sending status Request.")
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Status Request Error.\n\nReason: {0}".format(err)
            return False, values_dict, err_msg_dict

    # =============================================================================
    def speak_string(self, values_dict=None, type_id=""):
        """
        Speak a string

        The speak_string method takes a user-input string and sends it for speech on the
        Indigo server. The method supports Indigo substitutions and is useful when
        testing substitution strings.

        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        self.logger.debug(u"Call to speak_string")
        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(u"{0:{1}^80}".format(u" Speaking ", u"="))
            indigo.server.log(self.substitute(values_dict['thingToSpeak']))
            indigo.server.speak(self.substitute(values_dict['thingToSpeak']))

        except StandardError as err:
            self.logger.critical(u"Error sending status Request.")
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Status Request Error.\n\nReason: {0}".format(err)
            return False, values_dict, err_msg_dict

    # =============================================================================
    def subscribed_to_changes(self, values_dict=None, type_id=""):
        """
        Save Subscribe To Changes menu item configuration to plugin prefs for storage.

        The subscribed_to_changes method is used to save the settings for the Subscribe
        To Changes menu tool. We do this because there is no closedMenuConfigUi method
        similar to closedDeviceConfigUi method. We must save the menu configuration
        settings to the plugin configuration menu so that they're persistent.

        :param values_dict:
        :param type_id:
        :return:
        """

        # If user changes subscription preference, set flag for plugin restart (see __init__)
        if self.pluginPrefs['enableSubscribeToChanges'] == values_dict['enableSubscribeToChanges']:
            restart_required = False
        else:
            restart_required = True

        # Save preferences to plugin config for storage
        self.pluginPrefs['enableSubscribeToChanges'] = values_dict['enableSubscribeToChanges']
        self.pluginPrefs['subscribedDevices']        = values_dict['subscribedDevices']

        if restart_required:
            indigo.server.log(u"Preparing to restart plugin...")
            self.sleep(2)

            plugin = indigo.server.getPlugin("com.fogbert.indigoplugin.multitool")
            plugin.restart(waitUntilDone=False)

        return True

    # =============================================================================
    def substitution_generator(self, values_dict=None, type_id=""):
        """
        Generate an Indigo substitution string

        The substitution_generator method is used to construct Indigo substitution
        string segments from Indigo objects.  For example,

        .. code-block::

            Indigo Device Substitution: %%d:978421449:stateName%%

        -----

        :param values_dict:
        :param type_id:
        :return:
        """

        self.logger.debug(u"Call to substitution_generator")

        err_msg_dict = indigo.Dict()
        substitution_text = values_dict.get('thingToSubstitute', '')
        result = self.substitute(substitution_text)

        if substitution_text == '':
            return True, values_dict

        elif result:
            indigo.server.log(result)
            return True, values_dict

        else:
            err_msg_dict['thingToSubstitute'] = u"Invalid substitution string."
            err_msg_dict['showAlertText'] = u"Substitution Error.\n\nYour substitution string is invalid. See the Indigo log for available information."
            return False, values_dict, err_msg_dict
    # =============================================================================
