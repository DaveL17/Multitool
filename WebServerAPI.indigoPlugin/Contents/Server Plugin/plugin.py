#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

"""
"""

# =================================== TO DO ===================================


# ================================== IMPORTS ==================================

# Built-in modules
import datetime as dt
import inspect
import logging
import operator
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
__title__     = 'Web Server API Plugin for Indigo Home Control'
__version__   = '0.1.1'

# =============================================================================

# kDefaultPluginPrefs = {}


class Plugin(indigo.PluginBase):

    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        self.pluginIsInitializing = True
        self.pluginIsShuttingDown = False

        self.error_msg_dict = indigo.Dict()
        log_format = '%(asctime)s.%(msecs)03d\t%(levelname)-10s\t%(name)s.%(funcName)-28s %(msg)s'
        self.plugin_file_handler.setFormatter(logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S'))
        self.debugLevel = int(self.pluginPrefs.get('showDebugLevel', '30'))
        self.indigo_log_handler.setLevel(self.debugLevel)

        # ====================== Initialize DLFramework =======================

        self.Fogbert = Dave.Fogbert(self)
        self.Eval = Dave.evalExpr(self)

        # Log pluginEnvironment information when plugin is first started
        self.Fogbert.pluginEnvironment()

        # ================ Subscribe to Indigo Object Changes =================
        if self.pluginPrefs.get('enableSubscribeToChanges', False):
            self.logger.warning(u"You have subscribed to device and variable changes. Disable this feature if not in "
                                u"use.")
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

    def handle_some_action(self, action, dev=None, callerWaitingForResult=None):
        """
        This is the message handler that returns HTML.

        https://YOUR_REFLECTOR_NAME.indigodomo.net/message/com.YOUR_PLUGIN.indigoplugin.IDENTIFIER/handle_message/

        -----
        :param action: action object that contains the properties
        :param dev: unused
        :param callerWaitingForResult: always True
        :return: reply_dict (a Python dict that will be converted to an indigo.Dict instance)
        """
        self.logger.debug("variable_actions API call received")
        reply_dict = {"status": 200,
                      "headers": {"Content-Type": "text/html; charset=UTF-8", }
                      }
        props = dict(action.props)
        request_method = props["incoming_request_method"]

        try:
            # ================================== Load CSS ==================================
            with open('my_css.css', 'r') as in_file:
                style = in_file.read()
            my_css = "<style>\n{0}\n    </style>".format(style)

            # ============================= GET Request Method =============================
            if request_method == "GET":
                with open('web_server_api.html', 'r') as api_input:
                    out_file = api_input.read()

                reply_dict["content"] = out_file.replace('<style></style>', my_css)

            # ============================ POST Request Method =============================
            if request_method == "POST":

                # =============================== Update Device ================================
                dev = indigo.devices[697065899]
                dev.updateStateOnServer('slider_value', value=props['body_params'].get('slider', -1))

                # ============================ Generate Return HTML ============================
                with open('handle_return.html', 'r') as handle_return:
                    text_box =  props['body_params'].get('textbox', None)
                    slider =    props['body_params']['slider']
                    check_box = props['body_params'].get('checkbox', 'false')
                    radio =     props['body_params']['radio']
                    drop_down = props['body_params']['dropdown']
                    color =     props['body_params'].get('color', None)
                    file_link = props['body_params'].get('file', None)
                    date_val =  props['body_params']['date']

                    if text_box == "":
                        text_box = u"Unspecified"
                    if date_val == "":
                        date_val = dt.datetime.now().date()

                    outputs = [text_box, slider, check_box, radio, drop_down, color, file_link, date_val]
                    out_file = handle_return.read().format(*outputs)

                    reply_dict["content"] = out_file.replace('<style></style>', my_css)

            return reply_dict

        except KeyError as exc:
            reply_dict["status"] = "error"
            if exc.args[0] == "request_body":
                if exc.args[0] == "request_body":
                    self.logger.error("request_body couldn't be retrieved from the props dictionary")
                else:
                    self.logger.error("unknown key error: {}".format(str(exc)))
            reply_dict["reason"] = "An unexpected error occurred, check your Indigo Event Log for details."

        except ValueError:
            # TODO for PY3: update exception catch to json.decoder.JSONDecodeError
            reply_dict["status"] = "error"
            reply_dict["reason"] = "An unexpected error occurred, check your Indigo Event Log for details."
            self.logger.error("couldn't decode JSON from the request_body")
            self.logger.error("\n{}".format(traceback.format_exc()))

        # Return the dict to the Web Server
        return reply_dict
