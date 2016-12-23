#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

# TODO: There is no way to initiate debug logging.  Setting it with a state variable for now.

try:
    import indigo
except ImportError, error:
    indigo.server.log(str(error))
try:
    import pydevd
except ImportError, error:
    indigo.server.log(str(error))

__author__    = "DaveL17"
__build__     = ""
__copyright__ = 'Copyright 2016 DaveL17'
__license__   = "MIT"
__title__     = 'Multitool Plugin for Indigo Home Control'
__version__   = '1.0.01'

class Plugin(indigo.PluginBase):

    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.error_msg_dict = indigo.Dict()
        self.debug = False

        # To enable remote PyCharm Debugging, uncomment the next line.
        # pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True, suspend=False)

    def classToPrint(self, valuesDict, typeId):
        self.debugLog(u"classToPrint")

    def deviceDependencies(self, valuesDict, typeId):
        err_msg_dict = indigo.Dict()

        try:
            dependencies = indigo.device.getDependencies(int(valuesDict['listOfDevices']))
            indigo.server.log(u"{0:=^80}".format(u" {0} Dependencies ".format(indigo.devices[int(valuesDict['listOfDevices'])].name)))
            indigo.server.log(unicode(dependencies))
            return True

        except StandardError as err:
            indigo.server.log(unicode(u"Error obtaining dependencies.  Reason: {0}".format(err)), isError=True)
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Device dependencies Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict

    def deviceInventory(self, valuesDict, typeId):
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
            indigo.server.log(u"{0}".format('=' * table_width))

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

    def deviceToBeep(self, valuesDict, typeId):
        self.debugLog(u"deviceToBeep")

        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(u"{0:=^80}".format(u" Send Beep to {0} ".format(indigo.devices[int(valuesDict['listOfDevices'])].name)))
            indigo.device.beep(int(valuesDict['listOfDevices']), suppressLogging=False)
            return True

        except StandardError as err:
            indigo.server.log(unicode(u"Error sending beep.  Reason: {0}".format(err)), isError=True)
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Beep Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict


    def deviceToPing(self, valuesDict, typeId):
        self.debugLog(u"deviceToPing")

        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(u"{0:=^80}".format(u" Pinging device: {0} ".format(indigo.devices[int(valuesDict['listOfDevices'])].name)))
            result = indigo.device.ping(int(valuesDict['listOfDevices']), suppressLogging=False)
            indigo.server.log(unicode(result))
            return True

        except StandardError as err:
            indigo.server.log(unicode(u"Error sending ping.  Reason: {0}".format(err)), isError=True)
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Ping Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict

        except Exception as err:
            indigo.server.log(unicode(u"Error sending ping.  Reason: {0}".format(err)), isError=True)
            err_msg_dict['listOfDevices'] = u"Please select a device that supports the Ping function."
            err_msg_dict['showAlertText'] = u"Ping Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict

    def dictToPrint(self, typeId, valuesDict, targetId):
        self.debugLog(u"dictToPrint")

        if not valuesDict:
            return [("none", "None")]
        else:
            return [(thing.id, thing.name) for thing in getattr(indigo, valuesDict['classOfThing'])]

    def installedPlugins(self):
        # Credit: Jon (autolog)

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

        indigo.server.log(u"{0:=^80}".format(u" Installed Plugins "))
        for thing in plugin_name_list:
            indigo.server.log(u'{0}'.format(thing))

    def listOfDevices(self, valuesDict, typeId, targetId):

        return [(dev.id, dev.name) for dev in indigo.devices]

    def runningPlugins(self):
        import subprocess

        ret = subprocess.Popen("/bin/ps -ef | grep 'MacOS/IndigoPluginHost' | grep -v grep", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        indigo.server.log(u"{0:=^80}".format(u" Running Plugins "))
        indigo.server.log(u"\n{0}".format(ret))

    def resultsOutput(self, valuesDict, caller):

        thing = getattr(indigo, valuesDict['classOfThing'])[int(valuesDict['thingToPrint'])]
        indigo.server.log(u"{0:=^80}".format(u" {0} Dict ".format(thing.name)))
        indigo.server.log(u"\n{0}".format(thing))
        indigo.server.log(u"{0:=^80}".format(u""))

        return True

    def sendStatusRequest(self, valuesDict, typeId):
        err_msg_dict = indigo.Dict()

        try:
            indigo.server.log(u"{0:=^80}".format(u" Sending Status Request "))
            indigo.device.statusRequest(int(valuesDict['listOfDevices']), suppressLogging=False)
            return True

        except StandardError as err:
            indigo.server.log(unicode(u"Error sending status Request.  Reason: {0}".format(err)), isError=True)
            err_msg_dict['listOfDevices'] = u"Problem communicating with the device."
            err_msg_dict['showAlertText'] = u"Status Request Error.\n\nReason: {0}".format(err)
            return False, valuesDict, err_msg_dict

    def getSerialPorts(self):
        indigo.server.log(u"{0:=^80}".format(u" Current Serial Ports "))
        indigo.server.log(unicode(indigo.server.getSerialPorts()))  # Also available: indigo.server.getSerialPorts(filter="indigo.ignoreBluetooth")

    def indigoInformation(self):
        lat_long = indigo.server.getLatitudeAndLongitude()
        lat     = lat_long[0]
        long    = lat_long[1]
        indigo.server.log(u"{0:=^80}".format(u" Indigo Status Information "))
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

    def removeAllDelayedActions(self, valuesDict, typeId):
        indigo.server.removeAllDelayedActions()
        return True
