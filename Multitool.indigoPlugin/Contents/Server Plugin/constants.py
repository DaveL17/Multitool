"""
Repository of application constants

The Constants.py file contains all application constants and is imported as a
library. References are denoted as constants by the use of all caps.
"""

import indigo  # noqa


def __init__():
    pass


DEBUG_LABELS = {
    10: "Debugging Messages",
    20: "Informational Messages",
    30: "Warning Messages",
    40: "Error Messages",
    50: "Critical Errors Only"
}

FILTER_LIST = [
    ("all devices", "All Devices"),
    ("indigo.controller", "indigo.controller"),
    ("indigo.dimmer", "indigo.dimmer"),
    ("indigo.insteon", "indigo.insteon"),
    ("indigo.iodevice", "indigo.iodevice"),
    ("indigo.relay", "indigo.relay"),
    ("indigo.responder", "indigo.responder"),
    ("indigo.sensor", "indigo.sensor"),
    ("indigo.sprinkler", "indigo.sprinkler"),
    ("indigo.thermostat", "indigo.thermostat"),
    ("indigo.x10", "indigo.x10"),
    ("indigo.zwave", "indigo.zwave"),
]

INSTANCE_TO_COMMAND_NAMESPACE = {
    indigo.ActionGroup: indigo.actionGroup,
    indigo.ControlPage: indigo.controlPage,
    indigo.Device: indigo.device,
    indigo.DeviceStateChangeTrigger: indigo.devStateChange,
    indigo.DimmerDevice: indigo.dimmer,
    indigo.EmailReceivedTrigger: indigo.emailRcvd,
    indigo.InsteonCommandReceivedTrigger: indigo.insteonCmdRcvd,
    indigo.InterfaceFailureTrigger: indigo.interfaceFail,
    indigo.InterfaceInitializedTrigger: indigo.interfaceInit,
    indigo.MultiIODevice: indigo.iodevice,
    indigo.PluginEventTrigger: indigo.pluginEvent,
    indigo.PowerFailureTrigger: indigo.powerFail,
    indigo.RelayDevice: indigo.relay,
    indigo.Schedule: indigo.schedule,
    indigo.SensorDevice: indigo.sensor,
    indigo.ServerStartupTrigger: indigo.serverStartup,
    indigo.SpeedControlDevice: indigo.speedcontrol,
    indigo.SprinklerDevice: indigo.sprinkler,
    indigo.ThermostatDevice: indigo.thermostat,
    indigo.Trigger: indigo.trigger,
    indigo.Variable: indigo.variable,
    indigo.VariableValueChangeTrigger: indigo.varValueChange,
    indigo.X10CommandReceivedTrigger: indigo.x10CmdRcvd,
}
