### v2025.1.3
- Reduces duplicate code
- Fixes bug in Indigo Inventory tool.

### v2025.1.2
- Minor change to menu item order.
- Performance and stability improvements.
- Code refinements.

### v2024.1.0
- Adds tool to find Indigo objects with embedded scripts.
- Adds tool to find Indigo objects with linked scripts.
- Adds tool to ping an IP or hostname to determine its online status.
  - User creates Indigo Device to track ping status.
  - User creates Indigo Action to cause the ping to occur.
  - User creates optional Indigo Trigger to take action when the ping target is offline.
- Removes the Substitution Generator Tool (substitutions can now be generated directly from the Indigo UI.)
- Improves functional testing at startup when logging set to debug.
- Code cleanup

### v2023.2.2
- Fixes bug in network quality os test, "could not convert string to float".

### v2023.2.1
- Adds Network Quality Device tool.
- Adds Network Quality Report Menu item.

### v2023.1.1
- Fixes bug causing Test Action Return to appear in Indigo UI (it is now hidden.)
- Fixes bug in Battery Level Report that kept the report from being output to the log.

### v2023.1.0
- Adds plugin action for testing callback requests (see docs for more information).
- Removes Man Page tool as feature deprecated by Apple in Ventura.
- Code refinements

### v2022.1.10
- Updates plugin to API `3.2`.
- Notes that Indigo 2021.2 added ability to create a substitution string natively.
 
### v2022.1.9
- Adds trap to `object_dependencies.py` to account for unsupported object types.
- Updates Object Inspection Tool in plugin Wiki to include expanded dependency inspection.

### v2022.1.8
- Adds feature to print object dependencies to Object Inspection Tool, and removes Device Dependencies Tool from 
  plugin menu.
- Fixes minor validation bug in Color Picker tool.

### v2022.1.7
- Adds **Battery Level Report** Tool.

### v2022.1.6
- Combines "Object Dictionary" and "Object Directory" and renames as "Object Inspection".
- Adds foundation for Indigo API `3.1`.

### v2022.1.5
- Adds new tool: "Print Object Directory".
- Adds filter to "Device Last Comm" tool, and makes it so multiple reports can be generated without reopening the tool.
- Adds filter to "Error Inventory" tool to select either `Errors` or `Errors and Warnings`.

### v2022.1.4
- Fixes bug in "Substitution Generator" -- "Module not callable."
- Refines list of devices and variables returned with the 'Device / Variable' dropdown menu.
- Updates WiKi for latest changes.

### v2022.1.3
- "Modify Numeric Variable" and "Modify Time Variable" now support Indigo substitutions.
- Change "Subscribe to Changes" object selector from textfield to list.
- Adds `_to_do_list.md` and changes changelog to markdown.
- Moves plugin environment logging to plugin menu item (log only on request).
- Refactors code into `Tools.py` custom module.
- Improves validation for "Speak String" tool.
- Lays initial groundwork for unit testing.

### v2022.1.2
- Fixes bug where plugin ID was inadvertently changed from `com.fogbert.indigoplugin.multitool` to
  `com.fogbert.indigoplugin.Multitool`

### v2022.1.1
- Fixes bug in "Indigo Inventory" tool `(unhashable type: 'list')`.

### v2022.0.1
- Updates plugin for Indigo 2022.1 and Python 3.
- Hides hidden methods for "Methods - Indigo Base..." and "Methods - Plugin Base..." tools by default.
- Adds enabled state to device inventory output.
- Standardizes Indigo method implementation.

### v1.0.36
- Fixes embedded plugin package error.

### v1.0.35
- Fixes error in order of plugin menu items not listed in alphabetical order.

### v1.0.34
- Fixes bug in some tools (unexpected keyword argument 'filter').

### v1.0.33
- Fixes bug in Indigo Substitution Generator

### v1.0.32
- Adds tool to view man pages in Preview.
- Updates license file.

### v1.0.31
- Fixes broken link to readme logo.

### v1.0.30
- Further integration of DLFramework.

### v1.0.29
- Better integration of DLFramework.

### v1.0.28
- Clarifies instructions for color picker tool.
- Fixes bug in Device Ping tool.

### v1.0.27
- Improvements to configuration validation.
- Code refinements.

### v1.0.26
- Adds the "Modify Numeric Variable" and "Modify Time Variable" Action items.

### v1.0.25
- Removes all references to legacy version checking.

### v1.0.24
- Ensures plugin is compatible with the Indigo server version.
- Standardizes SupportURL behavior across all functions.

### v1.0.23
- Device Dependencies Tool - Added 'List Dependencies' button; the dialog no longer closes after dependencies are
  logged (allowing users to run multiple queries before closing the tool.)
- Device Dependencies Tool - Changed button title from 'Execute' to 'Close'.
- Device Ping Tool - Added 'Ping Device' button; the dialog no longer closes after ping is sent (allowing users to
  ping multiple devices before closing the tool.)
- Device Ping Tool - Changed button title from 'Execute' to 'Close'.
- Error Inventory Tool - renamed the output file and included facility to automatically name the output file so that
  prior output is not over-written.
- Indigo Inventory Tool [NEW] - outputs a listing of all Indigo Actions, Control Pages, Devices, Schedules, Triggers
  and Variables (and their folder locations.)
- Methods - Indigo Base Tool - renamed the tool and dramatically increased the scope of tool.
- Object Dictionary Tool - Added 'Print Dict' button; the dialog no longer closes after the object dictionary is
  output to the log (allowing users to query multiple objects before closing the tool.)
- Object Dictionary Tool - Changed button title from 'Execute' to 'Close'.
- Plugin Inventory Tool - Prettier log output.
- Serial Ports Tool - Prettier log output.
- Serial Ports Tool - Added setting to ignore BlueTooth ports.
- Speak String Tool - Added 'Speak String' button; the dialog no longer closes after string is spoken (allowing users
  to adjust and copy the string before closing the tool.)
- Speak String Tool - Changed button title from 'Execute' to 'Close'
- Substitution Generator Tool - Changed button title from 'Execute' to 'Close'.
- Removes plugin update notifications.

### v1.0.22
- Synchronize self.pluginPrefs in closedPrefsConfigUi().
- 
### v1.0.22
- Synchronize self.pluginPrefs in closedPrefsConfigUi().

### v1.0.21
- Removes plugin update checker.

### v1.0.20
- Changes Python lists to tuples where possible to increase performance.

### v1.0.19
- Adds tool to list `indigo.server` methods.

### v1.0.18
- Fixes bug in naming of PluginConfig.xml (which caused problems on systems set up as case-sensitive).

### v1.0.17
- Increments API version requirement to API 2.0.

### v1.0.16
- Adds Subscribe to Changes tool for devices and variables.
- Improves code commenting and adds Sphinx compatibility to docstrings.
- Code refinements.

### v1.0.15
- Adds menu item to check for plugin updates.
