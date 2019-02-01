#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

""" docstring placeholder """

# =================================== TO DO ===================================

# Nada

# ================================== IMPORTS ==================================

# Built-in modules
import inspect
import logging
import os
import sys

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
__version__   = '1.0.22'

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
    def closedPrefsConfigUi(self, valuesDict, userCancelled):

        self.logger.debug(u"Call to closedPrefsConfigUi")

        if not userCancelled:
            self.debugLevel = int(valuesDict.get('showDebugLevel', '20'))
            self.indigo_log_handler.setLevel(self.debugLevel)
            self.logger.debug(u"Call to closedPrefsConfigUi")

            # Ensure that self.pluginPrefs includes any recent changes.
            for k in valuesDict:
                self.pluginPrefs[k] = valuesDict[k]

            return valuesDict

    # =============================================================================
    def deviceUpdated(self, origDev, newDev):

        # Call the base implementation first just to make sure all the right
        # things happen elsewhere
        indigo.PluginBase.deviceUpdated(self, origDev, newDev)

        # If subscribe to changes is enabled
        if self.pluginPrefs.get('enableSubscribeToChanges', False):

            track_list = self.pluginPrefs.get('subscribedDevices', '')
            if track_list == '':
                subscribed_items = []
            else:
                subscribed_items = [int(_) for _ in track_list.replace(' ', '').split(',')]

            # If dev id in list of tracked items
            if origDev.id in subscribed_items:

                # Attribute changes
                exclude_list = ('globalProps', 'lastChanged', 'lastSuccessfulComm', 'ownerProps', 'states')
                attrib_list = [attr for attr in dir(origDev) if not callable(getattr(origDev, attr)) and '__' not in attr and attr not in exclude_list]
                attrib_dict = {attrib: (getattr(origDev, attrib), getattr(newDev, attrib)) for attrib in attrib_list if getattr(origDev, attrib) != getattr(newDev, attrib)}

                # Property changes
                orig_props = dict(origDev.ownerProps)
                new_props = dict(newDev.ownerProps)
                props_dict = {key: (orig_props[key], new_props[key]) for key in orig_props if orig_props[key] != new_props[key]}

                # State changes
                state_dict = {key: (origDev.states[key], val) for key, val in newDev.states.iteritems() if key not in origDev.states or val != origDev.states[key]}

                if len(attrib_dict) > 0 or len(state_dict) > 0 or len(props_dict) > 0:
                    indigo.server.log(u"\nDevice Changes: [{0}]\n{1:<8}{2}\n{3:<8}{4}\n{5:<8}{6}".format(newDev.name, 'Attr:', attrib_dict, 'Props', props_dict, 'States', state_dict))

    # =============================================================================
    def getMenuActionConfigUiValues(self, menuId):

        # Grab the setting values for the Subscribe to Changes tool
        if menuId == 'subscribeToChanges':

            changes_dict = indigo.Dict()
            changes_dict['enableSubscribeToChanges'] = self.pluginPrefs.get('enableSubscribeToChanges', False)
            changes_dict['subscribedDevices'] = self.pluginPrefs.get('subscribedDevices', '')

            return changes_dict

        else:
            return indigo.Dict()

    # =============================================================================
    def variableUpdated(self, origVar, newVar):

        # Call the base implementation first just to make sure all the right
        # things happen elsewhere
        indigo.PluginBase.variableUpdated(self, origVar, newVar)

        # If subscribe to changes is enabled
        if self.pluginPrefs.get('enableSubscribeToChanges', False):

            track_list = self.pluginPrefs.get('subscribedDevices', '')
            if track_list == '':
                subscribed_items = []
            else:
                subscribed_items = [int(_) for _ in track_list.replace(' ', '').split(',')]

            # If var id in list of tracked items
            if origVar.id in subscribed_items:

                # Attribute changes
                exclude_list = ('globalProps', 'lastChanged', 'lastSuccessfulComm')
                attrib_list = [attr for attr in dir(origVar) if not callable(getattr(origVar, attr)) and '__' not in attr and attr not in exclude_list]
                attrib_dict = {attrib: (getattr(origVar, attrib), getattr(newVar, attrib)) for attrib in attrib_list if getattr(origVar, attrib) != getattr(newVar, attrib)}

                # Variable value
                val_dict = {}
                if origVar.value != newVar.value:
                    val_dict = {newVar.name: (origVar.value, newVar.value)}

                if len(attrib_dict) > 0 or len(val_dict):
                    indigo.server.log(u"\nVariable Changes: [{0}]\n{1:<8}{2}\n{3:<8}{4}".format(newVar.name, 'Attr:', attrib_dict, 'Value', val_dict))

    # =============================================================================
    def validatePrefsConfigUi(self, valuesDict):

        return True, valuesDict

    # =============================================================================
    # ============================== Plugin Methods ===============================
    # =============================================================================
    def __dummyCallback__(self, valuesDict, typeId):
        """
        Dummy callback to cause refresh of dialog elements

        The __dummyCallback__ method is used and a placeholder callback to force a
        refresh of dialog elements based for controls with dynamic refresh attributes.

        -----

        :return:
        """

        pass

    # =============================================================================
    def aboutIndigo(self):
        """
        Prints information about the Indigo environment to the events log

        The aboutIndigo method prints select Indigo environment information to the
        Indigo events log. It can be a useful tool to get a user to quickly print
        relevant environment information for trouble-shooting.

        -----

        :return:
        """

        self.logger.debug(u"Call to aboutIndigo")
        lat_long = indigo.server.getLatitudeAndLongitude()
        latitude      = lat_long[0]
        longitude     = lat_long[1]
        indigo.server.log(u"{0:=^130}".format(u" Indigo Status Information "))
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
    def colorPicker(self, valuesDict, typeId):
        """
        Print color information to the Indigo events log

        Write color information to the Indigo events log to include the raw, hex, and
        RGB values.

        -----

        :return:
        """

        self.logger.debug(u"Call to colorPicker")
        if not valuesDict['chosenColor']:
            valuesDict['chosenColor'] = "FF FF FF"
        indigo.server.log(u"Raw: {0}".format(valuesDict['chosenColor']))
        indigo.server.log(u"Hex: #{0}".format(valuesDict['chosenColor'].replace(' ', '')))
        indigo.server.log(u"RGB: {0}".format(tuple([int(thing, 16) for thing in valuesDict['chosenColor'].split(' ')])))
        return True

    # =============================================================================
    def deviceDependencies(self, valuesDict, typeId):
        """
        Print a list of device dependencies to the Indigo events log

        The deviceDependencies method prints a list of known dependencies for a
        selected Indigo device.

        -----

        :return:
        """

        self.logger.debug(u"Call to deviceDependencies")
        err_msg_dict = indigo.Dict()

        try:
            dependencies = indigo.device.getDependencies(int(valuesDict['listOfDevices']))
            indigo.server.log(u"{0:=^80}".format(u" {0} Dependencies ".format(indigo.devices[int(valuesDict['listOfDevices'])].name)))
            indigo.server.log(unicode(dependencies))
            return True

        except StandardError as err:
            self.logger.critical(u"Error obtaining dependencies.")
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Device dependencies Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict

    # =============================================================================
    def deviceInventory(self, valuesDict, typeId):
        """
        Print an inventory of Indigo devices to the Indigo events log

        The deviceInventory method prints an inventory of all Indigo devices to the
        Indigo events log.

        -----

        :return:
        """

        self.logger.debug(u"Call to deviceInventory")
        import datetime

        filter_item = ""

        if valuesDict['typeOfThing'] not in ('Other', 'pickone'):
            filter_item = valuesDict['typeOfThing']
            x = [[dev.id, dev.address, dev.name, dev.lastChanged] for dev in indigo.devices.iter(filter=filter_item)]
        elif valuesDict['typeOfThing'] == 'Other' and len(valuesDict['customThing']) > 0:
            filter_item = valuesDict['customThing']
            x = [[dev.id, dev.address, dev.name, dev.lastChanged] for dev in indigo.devices.iter(filter=filter_item)]
        else:
            x = []

        if len(x) > 0:

            x0 = max([len(unicode(thing[0])) for thing in x]) + 2
            x1 = max([len(unicode(thing[1])) for thing in x]) + 5
            x2 = max([len(unicode(thing[2])) for thing in x]) + 2
            x3 = max([len(unicode(thing[3])) for thing in x])
            table_width = sum((x0, x1, x2, x3))

            indigo.server.log(u"{0:=^{1}}".format(u" Inventory of '{0}' Devices ".format(filter_item), table_width))
            indigo.server.log(u"{0:<{1}} {2:<{3}} {4:<{5}} {6:<{7}}".format(u"ID", (x0 - 1), u"Addr", (x1 - 1), u"Name", (x2 - 1), u"Last Changed", x3))
            indigo.server.log(u"{0}".format(u'=' * table_width))

            for thing in x:
                indigo.server.log(u"{0:<{1}} {2:<{3}} {4:<{5}} {6:<{7}}".format(thing[0], (x0 - 1),
                                                                                u"[{0}]".format(thing[1]), (x1 - 1),
                                                                                thing[2], (x2 - 1),
                                                                                datetime.datetime.strftime(thing[3], '%Y-%m-%d %H:%M:%S'), x3))
        else:
            if valuesDict['typeOfThing'] not in ('Other', 'pickone'):
                indigo.server.log(u"No {0} devices found.".format(valuesDict['typeOfThing']))
            elif valuesDict['typeOfThing'] == 'Other' and len(valuesDict['customThing']) > 0:
                indigo.server.log(u"No {0} devices found.".format(valuesDict['customThing']))

        return valuesDict

    # =============================================================================
    def deviceLastSuccessfulComm(self):
        """
        Print information on the last successful communication with a device

        The deviceLastSuccessfulComm method prints information on the last successful
        communication with each Indigo device to the Indigo events log.

        -----

        :return:
        """

        self.logger.debug(u"Call to deviceLastSuccessfulComm")

        # Get the data we need
        table = [(dev.id, dev.name, dev.lastSuccessfulComm) for dev in indigo.devices.iter()]

        # Sort the data from newest to oldest
        table = sorted(table, key=lambda (devId, name, comm): comm, reverse=True)

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
    def deviceToBeep(self, valuesDict, typeId):
        """
        Send a beep request to a device

        The deviceToBeep method will send a beep request to a selected Indigo device.
        Only select devices support the beep request and only enabled devices are
        displayed for selection.

        -----

        :return:
        """

        self.logger.debug(u"Call to deviceToBeep")

        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(u"{0:=^80}".format(u" Send Beep to {0} ".format(indigo.devices[int(valuesDict['listOfDevices'])].name)))
            indigo.device.beep(int(valuesDict['listOfDevices']), suppressLogging=False)
            return True

        except ValueError:
            err_msg_dict['listOfDevices'] = u"You must select a device to receive the beep request"
            err_msg_dict['showAlertText'] = u"Beep Error.\n\nReason: No device selected."
            return False, valuesDict, err_msg_dict

        except StandardError as err:
            self.logger.critical(u"Error sending beep request.")
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Beep Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict

    # =============================================================================
    def deviceToPing(self, valuesDict, typeId):
        """
        Send a ping request to a device

        The deviceToPing method will send a ping request to a selected Indigo device.
        Only enabled devices are displayed. Plugin devices must support sendDevicePing
        method and plugin must be enabled.

        -----

        :return:
        """

        self.logger.debug(u"Call to deviceToPing")

        dev_id = int(valuesDict['listOfDevices'])
        err_msg_dict = indigo.Dict()

        try:
            if indigo.devices[dev_id].enabled:
                indigo.server.log(u"{0:=^80}".format(u" Pinging device: {0} ".format(indigo.devices[dev_id].name)))
                result = indigo.device.ping(dev_id, suppressLogging=False)
                indigo.server.log(unicode(result))
                return True
            else:
                err_msg_dict['listOfDevices'] = u"A disabled device can not respond to a ping request."
                err_msg_dict['showAlertText'] = u"Ping Error.\n\nDevice [{0}] cannot respond to a ping because it is disabled.".format(indigo.devices[dev_id].name)
                return False, valuesDict, err_msg_dict

        except StandardError as err:
            self.logger.critical(u"Error sending ping.")
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Ping Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict

        except Exception as err:
            self.logger.critical(u"Error sending ping.")
            err_msg_dict['listOfDevices'] = u"Please select a device that supports the Ping function."
            err_msg_dict['showAlertText'] = u"Ping Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict

    # =============================================================================
    def dictToPrint(self, typeId, valuesDict, targetId):
        """
        Return a list of Indigo objects for inspection

        The dictToPrint method will return a list of objects for inspection. Objects
        that are supported include Actions, Control Pages, Devices, Schedules,
        Triggers, and variables. It is called by the Object Dictionary... menu item in
        conjunction with the resultsOutput method.

        -----

        :return:
        """

        self.logger.debug(u"Call to dictToPrint")

        if not valuesDict:
            return [("none", "None")]
        else:
            return [(thing.id, thing.name) for thing in getattr(indigo, valuesDict['classOfThing'])]

    # =============================================================================
    def environmentPath(self):
        """
        Print the Indigo server's environment path variable to the Indigo Events log

        the environmentPath method outputs the value of the server computer's
        environment path variable to the Indigo events log. This can help with trouble-
        shooting--for example, when an expected import statement fails.

        -----

        :return:
        """

        self.logger.debug(u"Call to environmentPath")

        indigo.server.log(u"{0:=^130}".format(u" Current System Path "))
        for p in sys.path:
            indigo.server.log(p)
        indigo.server.log(u"{0:=^130}".format(u" (Sorted) "))
        for p in sorted(sys.path):
            indigo.server.log(p)

    # =============================================================================
    def errorInventory(self, valuesDict, typeId):
        """
        Create an inventory of error messages appearing in the Indigo Logs.

        The errorInventory method will scan log files and parse out any log lines than
        contain the term 'error'. It is agnostic as to whether the log line is an
        actual error or a debug statement that contains the term error.

        -----

        :return:
        """

        self.logger.debug(u"Call to errorInventory")

        # TODO: what if file already exists? Maybe a checkbox to 'retain old inventory' --> then result.txt, result1.txt, etc.

        check_list = (' Err ', ' err ', 'Error', 'error')
        log_folder = indigo.server.getInstallFolderPath() + "/Logs/"

        with open(log_folder + 'error_inventory.txt', 'w') as outfile:

            for root, sub, files in os.walk(log_folder):
                for filename in files:
                    if filename.endswith((".log", ".txt")) and filename != 'error_inventory.txt':
                        with open(os.path.join(root, filename), "r") as infile:
                            log_file = infile.read()

                            for line in log_file.split('\n'):
                                if any(item in line for item in check_list):
                                    outfile.write("{0:<130}{1}\n".format(root + filename, line))

        self.logger.info(u"Error message inventory saved to: {0}error_inventory.txt".format(log_folder))
        return True

    # =============================================================================
    def generatorDeviceList(self, filter="", valuesDict=None, typeId="", targetId=0):
        """
        Returns a list of plugin devices.

        The generatorDeviceList method passes a list of Indigo devices to the calling
        control. It is a connector to the generator which is located in the DLFramework
        module.

        -----

        :return:
        """

        self.logger.debug(u"generatorDeviceList() called.")

        return self.Fogbert.deviceList(filter=None)

    # =============================================================================
    def generatorEnabledDeviceList(self, filter="", valuesDict=None, typeId="", targetId=0):
        """
        Returns a list of enabled plugin devices.

        The generatorEnabledDeviceList passes a list of enabled Indigo devices to the
        calling control. It is a connector to the generator which is located in the
        DLFramework module.

        -----

        :return:
        """

        self.logger.debug(u"generatorDeviceList() called.")

        return self.Fogbert.deviceListEnabled(filter=None)

    # =============================================================================
    def generatorDevVar(self, filter="", valuesDict=None, typeId="", targetId=0):
        """
        Return a list of Indigo devices and variables

        The generatorDevVar method collects IDs and names for all Indigo devices and
        variables. It creates a list of the form:

        [(dev.id, dev.name), (var.id, var.name)].

        -----

        :return:
        """

        self.logger.debug(u"generatorDevVar() called.")

        return self.Fogbert.deviceAndVariableList()

    # =============================================================================
    def generatorStateOrValue(self, filter="", valuesDict=None, typeId="", targetId=0):
        """
        Return a list of device states and variable values

        The generatorStateOrValue() method returns a list to populate the relevant
        device states or variable value to populate a menu control.

        -----

        :return:
        """

        self.logger.debug(u"generatorStateOrValue() called.")

        try:
            id_number = int(valuesDict['devVarMenu'])

            if id_number in indigo.devices.keys():
                state_list = [(state, state) for state in indigo.devices[id_number].states if not state.endswith('.ui')]
                state_list.remove(('onOffState', 'onOffState'))
                return state_list

            elif id_number in indigo.variables.keys():
                return [('value', 'Value')]

        except (KeyError, ValueError):
            return [(0, 'Pick a Device or Variable')]

    # =============================================================================
    def generatorSubstitutions(self, valuesDict, typeId="", targetId=0):
        """
        Generate the construct for an Indigo substitution

        The generatorSubstitutions method is used with the Substitution Generator. It
        is the callback that's used to create the Indigo substitution construct.

        -----

        :return:
        """

        self.logger.debug(u"generatorSubstitutions() called.")

        dev_var_id    = valuesDict['devVarMenu']
        dev_var_value = valuesDict['generatorStateOrValue']

        if int(valuesDict['devVarMenu']) in indigo.devices.keys():
            indigo.server.log(u"Indigo Device Substitution: %%d:{0}:{1}%%".format(dev_var_id, dev_var_value))

        else:
            indigo.server.log(u"Indigo Variable Substitution: %%v:{0}%%".format(dev_var_id))

        valuesDict['devVarMenu'] = ''
        valuesDict['generatorStateOrValue'] = ''

        return valuesDict

    # =============================================================================
    def getSerialPorts(self):
        """
        Print a list of serial ports to the Indigo events log

        The getSerialPorts method prints a list of available serial ports to the Indigo
        events log.

        -----

        :return:
        """

        self.logger.debug(u"Call to getSerialPorts")

        self.logger.debug(u"Call to getSerialPorts")
        indigo.server.log(u"{0:=^80}".format(u" Current Serial Ports "))
        indigo.server.log(unicode(indigo.server.getSerialPorts()))  # Also available: indigo.server.getSerialPorts(filter="indigo.ignoreBluetooth")

    # =============================================================================
    def inspectMethod(self, valuesDict, typeId):
        """
        Print the signature of an Indigo method to the Indigo events log

        The inspectMethod method will inspect a selected Indigo method and print the
        target method's signature to the Indigo events log. This is useful when the
        signature of an Indigo method is unknown.  It will return a list of attributes
        passed by the Indigo method.  For example,

        .. code-block::

           Multitool    self.closedPrefsConfigUi: ArgSpec(args=['self', 'valuesDict', 'userCancelled'], varargs=None, keywords=None, defaults=None)
           Multitool    Docstring:  User closes config menu. The validatePrefsConfigUI() method will also be called.


        -----

        :return:
        """

        self.logger.debug(u"Call to inspectMethod")

        method = getattr(self, valuesDict['listOfMethods'])
        signature = inspect.getargspec(method)
        indigo.server.log(u"self.{0}: {1}".format(valuesDict['listOfMethods'], signature))
        indigo.server.log(u"Docstring: {0}".format(getattr(self, valuesDict['listOfMethods']).__doc__), isError=False)

    # =============================================================================
    def installedPlugins(self):
        """
        Print a list of installed plugins to the Indigo events log

        The installedPlugins method will print a list of installed plugins to the
        Indigo events log along with the plugin's bundle identifier. In instances
        where the plugin is disabled, [Disabled] will be appended to the log line.

        -----

        :return:
        """

        self.logger.debug(u"Call to installedPlugins")

        import os
        import plistlib

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

                    plugin_name_list.append((cf_bundle_identifier, cf_bundle_display_name))

        indigo.server.log(u"{0:=^130}".format(u" Installed Plugins "))
        for thing in plugin_name_list:
            indigo.server.log(u'{0}'.format(thing))
        indigo.server.log(u"{0:=^130}".format(u" Code Credit: Autolog "))

    # =============================================================================
    def listOfMethods(self, valuesDict, typeId, targetId):
        """
        Generate a list of Indigo methods for inspection

        The listOfMethods method will generate a list of Indigo methods available for
        inspection. It is used to populate the list of methods control for the Method
        Signature... tool.

        -----

        :return:
        """

        self.logger.debug(u"Call to listOfMethods")

        list_of_attributes = []
        for method in dir(indigo.PluginBase):
            try:
                inspect.getargspec(getattr(indigo.PluginBase, method))
                list_of_attributes.append((method, method))
            except (AttributeError, TypeError):
                continue
        return list_of_attributes

    # =============================================================================
    def listOfServerMethods(self, valuesDict, typeId, targetId):
        """
        Generate a list of Indigo Server methods

        The listOfServerMethods method will generate a list of Indigo methods available
        for review. It is used to populate the list of methods control for the Indigo
        Server Method... tool.

        -----

        :return:
        """

        self.logger.debug(u"Call to listOfServerMethods")

        return [(method, method) for method in dir(indigo.server)]

    # =============================================================================
    def logServerMethod(self, valuesDict, typeId):

        method_to_call = getattr(indigo.server, valuesDict['listOfServerMethods'])
        indigo.server.log(inspect.getdoc(method_to_call))

    # =============================================================================
    def removeAllDelayedActions(self, valuesDict, typeId):
        """
        Removes all delayed actions from the Indigo server

        The removeAllDelayedActions method is a convenience tool to remove all delayed
        actions from the Indigo server.

        -----

        :return:
        """

        self.logger.debug(u"Call to removeAllDelayedActions")
        indigo.server.removeAllDelayedActions()

    # =============================================================================
    def runningPlugins(self):
        """
        Print a list of running pluings to the Indigo events log

        The runningPlugins method prints a table of Indigo plugins that are currently
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

        self.logger.debug(u"Call to runningPlugins")
        import subprocess

        ret = subprocess.Popen("/bin/ps -ef | grep 'MacOS/IndigoPluginHost' | grep -v grep", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        indigo.server.log(u"\n{0:=^120}".format(u" Running Plugins (/bin/ps -ef) "))
        indigo.server.log(u"\n{0}\n\n{1}".format(u"  uid - pid - parent pid - recent CPU usage - process start time - controlling tty - elapsed CPU usage - associated command", ret))

    # =============================================================================
    def resultsOutput(self, valuesDict, caller):
        """
        Print an Indigo object's properties dict to the Indigo events log

        The resultsOutput method formats an object properties dictionary for output to
        the Indigo events log. It's used in conjunction with the Object Dictionary...
        tool.

        -----

        :return:
        """

        self.logger.debug(u"Call to resultsOutput")
        self.logger.debug(u"Caller: {0}".format(caller))

        thing = getattr(indigo, valuesDict['classOfThing'])[int(valuesDict['thingToPrint'])]
        indigo.server.log(u"{0:=^80}".format(u" {0} Dict ".format(thing.name)))
        indigo.server.log(u"\n{0}".format(thing))
        indigo.server.log(u"{0:=^80}".format(u""))
        return True

    # =============================================================================
    def sendStatusRequest(self, valuesDict, typeId):
        """
        Send a status request to an Indigo object

        The sendStatusRequest method will send a status request inquiry to a selected
        Indigo object. Note that not all objects support a status request and plugin
        devices that support status requests must have their host plugin enabled.
        Further, only enabled objects are available for a status request.

        -----

        :return:
        """

        self.logger.debug(u"Call to sendStatusRequest")
        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(u"{0:=^80}".format(u" Sending Status Request "))
            indigo.device.statusRequest(int(valuesDict['listOfDevices']), suppressLogging=False)
            return True

        except StandardError as err:
            self.logger.critical(u"Error sending status Request.")
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Status Request Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict

    # =============================================================================
    def speakString(self, valuesDict, typeId):
        """
        Speak a string

        The speakString method takes a user-input string and sends it for speech on the
        Indigo server. The method supports Indigo substitutions and is useful when
        testing substitution strings.

        -----

        :return:
        """

        self.logger.debug(u"Call to speakString")
        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(u"{0:=^80}".format(u" Speaking "))
            indigo.server.log(self.substitute(valuesDict['thingToSpeak']))
            indigo.server.speak(self.substitute(valuesDict['thingToSpeak']))
            return True

        except StandardError as err:
            self.logger.critical(u"Error sending status Request.")
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Status Request Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict

    # =============================================================================
    def subscribedToChanges(self, valuesDict, typeId):
        """
        Save Subscribe To Changes menu item configuration to plugin prefs for storage.

        The subscribedToChanges method is used to save the settings for the Subscribe
        To Changes menu tool. We do this because there is no closedMenuConfigUi method
        similar to closedDeviceConfigUi method. We must save the menu configuration
        settings to the plugin configuration menu so that they're persistent.

        :param valuesDict:
        :param typeId:
        :return:
        """

        # If user changes subscription preference, set flag for plugin restart (see __init__)
        if self.pluginPrefs['enableSubscribeToChanges'] == valuesDict['enableSubscribeToChanges']:
            restart_required = False
        else:
            restart_required = True

        # Save preferences to plugin config for storage
        self.pluginPrefs['enableSubscribeToChanges'] = valuesDict['enableSubscribeToChanges']
        self.pluginPrefs['subscribedDevices']        = valuesDict['subscribedDevices']

        if restart_required:
            indigo.server.log(u"Preparing to restart plugin...")
            self.sleep(2)

            plugin = indigo.server.getPlugin("com.fogbert.indigoplugin.multitool")
            plugin.restart(waitUntilDone=False)

        return True

    # =============================================================================
    def substitutionGenerator(self, valuesDict, typeId):
        """
        Generate an Indigo substitution string

        The substitutionGenerator method is used to construct Indigo substitution
        string segments from Indigo objects.  For example,

        .. code-block::

            Indigo Device Substitution: %%d:978421449:stateName%%

        -----

        :return:
        """

        self.logger.debug(u"Call to substitutionGenerator")

        err_msg_dict = indigo.Dict()
        substitution_text = valuesDict.get('thingToSubstitute', '')
        result = self.substitute(substitution_text)

        if substitution_text == '':
            return True, valuesDict

        elif result:
            indigo.server.log(result)
            return True, valuesDict

        else:
            err_msg_dict['thingToSubstitute'] = u"Invalid substitution string."
            err_msg_dict['showAlertText'] = u"Substitution Error.\n\nYour substitution string is invalid. See the Indigo log for available information."
            return False, valuesDict, err_msg_dict
    # =============================================================================
