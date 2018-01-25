#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

""" docstring placeholder """

# =================================== TO DO ===================================

# TODO: There is no way to initiate debug logging.  Setting it with a state variable for now. When it's time, use the template.
# TODO: Setup update notifications. When it's time, use the template.
# TODO: kDefaultPluginPrefs


# ================================== IMPORTS ==================================

# Built-in modules
import inspect
import logging
import os
import sys

# Third-party modules
from DLFramework import indigoPluginUpdateChecker
try:
    import indigo
except ImportError, error:
    indigo.server.log(str(error))
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
__version__   = '1.0.13'

# =============================================================================

# kDefaultPluginPrefs = {}


class Plugin(indigo.PluginBase):

    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        updater_url = "https://davel17.github.io/Multitool/Multitool_version.html"
        self.updater = indigoPluginUpdateChecker.updateChecker(self, updater_url)

        self.error_msg_dict = indigo.Dict()
        self.plugin_file_handler.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d\t%(levelname)-10s\t%(name)s.%(funcName)-28s %(msg)s', datefmt='%Y-%m-%d %H:%M:%S'))
        self.debugLevel = int(self.pluginPrefs.get('showDebugLevel', '30'))
        self.indigo_log_handler.setLevel(self.debugLevel)

        # ====================== Initialize DLFramework =======================

        self.Fogbert = Dave.Fogbert(self)

        # Log pluginEnvironment information when plugin is first started
        self.Fogbert.pluginEnvironment()

        # =====================================================================

        # try:
        #     pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)
        # except:
        #     pass


    def aboutIndigo(self):
        """"""
        self.logger.debug(u"Call to aboutIndigo")
        lat_long = indigo.server.getLatitudeAndLongitude()
        lat      = lat_long[0]
        long     = lat_long[1]
        indigo.server.log(u"{0:=^130}".format(u" Indigo Status Information "))
        indigo.server.log(u"Server Version: {0}".format(indigo.server.version))
        indigo.server.log(u"API Version: {0}".format(indigo.server.apiVersion))
        indigo.server.log(u"Server IP Address: {0}".format(indigo.server.address))
        indigo.server.log(u"Install Path: {0}".format(indigo.server.getInstallFolderPath()))
        indigo.server.log(u"Database: {0}/{1}".format(indigo.server.getDbFilePath(), indigo.server.getDbName()))
        indigo.server.log(u"Port Number: {0}".format(indigo.server.portNum))
        indigo.server.log(u"Latitude and Longitude: {0}/{1}".format(lat, long))

        if indigo.server.connectionGood:
            indigo.server.log(u"Connection Good.".format(indigo.server.connectionGood))
        else:
            indigo.server.log(u"Connection Bad.".format(indigo.server.connectionGood), isError=True)

    def classToPrint(self, valuesDict, typeId):
        """"""
        self.logger.debug(u"Call to to classToPrint")

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        """ User closes config menu. The validatePrefsConfigUI() method will
        also be called."""
        self.logger.debug(u"Call to closedPrefsConfigUi")

        if not userCancelled:
            self.debugLevel = int(valuesDict.get('showDebugLevel', '20'))
            self.indigo_log_handler.setLevel(self.debugLevel)
            self.logger.debug(u"Call to closedPrefsConfigUi")

            return valuesDict

    def colorPicker(self, valuesDict, typeId):
        """"""
        if not valuesDict['chosenColor']:
            valuesDict['chosenColor'] = "FF FF FF"
        indigo.server.log(u"Raw: {0}".format(valuesDict['chosenColor']))
        indigo.server.log(u"Hex: #{0}".format(valuesDict['chosenColor'].replace(' ', '')))
        indigo.server.log(u"RGB: {0}".format(tuple([int(thing, 16) for thing in valuesDict['chosenColor'].split(' ')])))
        return True

    def deviceDependencies(self, valuesDict, typeId):
        """"""
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

    def deviceInventory(self, valuesDict, typeId):
        """"""
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

    def deviceLastSuccessfulComm(self):
        """"""
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

    def deviceToBeep(self, valuesDict, typeId):
        """"""
        self.logger.debug(u"Call to deviceToBeep")

        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(u"{0:=^80}".format(u" Send Beep to {0} ".format(indigo.devices[int(valuesDict['listOfDevices'])].name)))
            indigo.device.beep(int(valuesDict['listOfDevices']), suppressLogging=False)
            return True

        except ValueError as err:
            err_msg_dict['listOfDevices'] = u"You must select a device to receive the beep request"
            err_msg_dict['showAlertText'] = u"Beep Error.\n\nReason: No device selected."
            return False, valuesDict, err_msg_dict

        except StandardError as err:
            self.logger.critical(u"Error sending beep request.")
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Beep Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict

    def deviceToPing(self, valuesDict, typeId):
        """"""
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

    def dictToPrint(self, typeId, valuesDict, targetId):
        """"""
        self.logger.debug(u"Call to dictToPrint")

        if not valuesDict:
            return [("none", "None")]
        else:
            return [(thing.id, thing.name) for thing in getattr(indigo, valuesDict['classOfThing'])]

    def environmentPath(self):
        """ """

        indigo.server.log(u"{0:=^130}".format(u" Current System Path "))
        for p in sys.path:
            indigo.server.log(p)
        indigo.server.log(u"{0:=^130}".format(u" (Sorted) "))
        for p in sorted(sys.path):
            indigo.server.log(p)

    def errorInventory(self, valuesDict, typeId):
        """Create an inventory of error messages appearing in the Indigo Logs."""

        # TODO: what if file already exists? Maybe a checkbox to 'retain old inventory' --> then result.txt, result1.txt, etc.

        check_list = [' Err ', ' err ', 'Error', 'error']
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

    def generatorDeviceList(self, filter="", valuesDict=None, typeId="", targetId=0):
        """Returns a list of plugin devices."""
        self.logger.debug(u"generatorDeviceList() called.")

        return self.Fogbert.deviceList(filter=None)

    def generatorEnabledDeviceList(self, filter="", valuesDict=None, typeId="", targetId=0):
        """Returns a list of plugin devices."""
        self.logger.debug(u"generatorDeviceList() called.")

        return self.Fogbert.deviceListEnabled(filter=None)

    def generatorDevVar(self, filter="", valuesDict=None, typeId="", targetId=0):
        """This method collects IDs and names for all Indigo devices and
        variables. It creates a list of the form:
        [(dev.id, dev.name), (var.id, var.name)].
        """
        self.logger.debug(u"generatorDevVar() called.")

        return self.Fogbert.deviceAndVariableList()

    def generatorStateOrValue(self, filter="", valuesDict=None, typeId="", targetId=0):
        """The generatorStateOrValue() method returns a list to populate the relevant
        device states or variable value to populate a menu control."""
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

    def generatorSubstitutions(self, valuesDict, typeId="", targetId=0):
        """The generatorSubstitutions function is used with the Substitution Generator.
        It is the callback that's used to create the Indigo substitution
        construct."""
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

    def getSerialPorts(self):
        """"""
        self.logger.debug(u"Call to getSerialPorts")
        indigo.server.log(u"{0:=^80}".format(u" Current Serial Ports "))
        indigo.server.log(unicode(indigo.server.getSerialPorts()))  # Also available: indigo.server.getSerialPorts(filter="indigo.ignoreBluetooth")

    def inspectMethod(self, valuesDict, typeId):
        """"""
        self.logger.debug(u"Call to inspectMethod")

        method = getattr(self, valuesDict['listOfMethods'])
        signature = inspect.getargspec(method)
        indigo.server.log(u"self.{0}: {1}".format(valuesDict['listOfMethods'], signature))
        indigo.server.log(u"Docstring: {0}".format(getattr(self, valuesDict['listOfMethods']).__doc__), isError=False)

    def installedPlugins(self):
        """Credit: Jon (autolog)"""
        self.logger.debug(u"Call to installedPlugins")

        import os
        import plistlib

        plugin_name_list = []
        indigo_install_path = indigo.server.getInstallFolderPath()
        plugin_folders = ['Plugins', 'Plugins (Disabled)']

        for plugin_folder in plugin_folders:
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

    def listOfMethods(self, valuesDict, typeId, targetId):
        """"""
        self.logger.debug(u"Call to listOfMethods")

        list_of_attributes = []
        for method in dir(indigo.PluginBase):
            try:
                inspect.getargspec(getattr(indigo.PluginBase, method))
                list_of_attributes.append((method, method))
            except (AttributeError, TypeError):
                continue
        return list_of_attributes

    def refreshFields(self, filter="", typeId="", targetId=0):
        """The refreshFields() method is a dummy callback used solely to fire
        other actions that require a callback be run. It performs no other
        function."""
        self.logger.debug(u"refreshFields() called.")
        pass

    def removeAllDelayedActions(self, valuesDict, typeId):
        """"""
        self.logger.debug(u"Call to removeAllDelayedActions")
        indigo.server.removeAllDelayedActions()
        # return True

    def runningPlugins(self):
        """"""
        self.logger.debug(u"Call to runningPlugins")
        import subprocess

        ret = subprocess.Popen("/bin/ps -ef | grep 'MacOS/IndigoPluginHost' | grep -v grep", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        indigo.server.log(u"{0:=^80}".format(u" Running Plugins "))
        indigo.server.log(u"\n{0}".format(ret))

    def resultsOutput(self, valuesDict, caller):
        """"""
        self.logger.debug(u"Call to resultsOutput")

        thing = getattr(indigo, valuesDict['classOfThing'])[int(valuesDict['thingToPrint'])]
        indigo.server.log(u"{0:=^80}".format(u" {0} Dict ".format(thing.name)))
        indigo.server.log(u"\n{0}".format(thing))
        indigo.server.log(u"{0:=^80}".format(u""))
        return True

    def sendStatusRequest(self, valuesDict, typeId):
        """"""
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

    def speakString(self, valuesDict, typeId):
        """"""
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

    def substitutionGenerator(self, valuesDict, typeId):
        """"""
        err_msg_dict = indigo.Dict()
        substitutionText = valuesDict['thingToSubstitute']
        result = self.substitute(substitutionText)

        if result:
            indigo.server.log(result)
            return True, valuesDict
        else:
            err_msg_dict['thingToSubstitute'] = u"Invalid substitution string."
            err_msg_dict['showAlertText'] = u"Substitution Error.\n\nYour substitution string is invalid. See the Indigo log for available information."
            return False, valuesDict, err_msg_dict
