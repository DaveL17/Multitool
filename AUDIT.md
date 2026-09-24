# Multitool Plugin — Code Audit

Audit date: 2026-09-24
Scope: `Multitool.indigoPlugin/Contents/Server Plugin/` (plugin.py, constants.py,
plugin_defaults.py, Tools/*.py, Actions.xml, Devices.xml, Events.xml, MenuItems.xml,
PluginConfig.xml), `tests/`, and top-level project files. `DLFramework/` was read
only for cross-reference (per CLAUDE.md, it's off-limits to modify) and
`tests/shared/` (submodule) was treated as read-only reference material, not
audited for its own quality. `Multitool.wiki/` (a separate git repository per
CLAUDE.md) was not audited, aside from noting where it repeats a stale claim also
found in this repo's own `CLAUDE.md`.

This is a **read-only findings report**. No code was changed. Findings are ordered
roughly by severity within each section. File paths are relative to
`Multitool.indigoPlugin/Contents/Server Plugin/` unless noted otherwise.

Methodology: five parallel focused passes (plugin.py core lifecycle; Tools/ batch 1;
Tools/ batch 2; XML config cross-reference; tests/docs) followed by manual
verification of the highest-impact and most-contested claims against the local
Indigo API documentation and the actual source — including confirming the Critical
findings below by direct grep against `llms-full.txt`, and disproving one
initially-flagged issue (a suspected `.lower()`-on-bool crash at `plugin.py:268`,
which turned out to already be guarded by an `isinstance(raw, str)` check — not a
bug, not included below).

---

## 🔴 Critical — silently broken functionality

### 1. `trigger_start_processing` is misnamed — the offline-ping trigger feature never fires
**Status: ✅ Fixed in v2025.2.13** — renamed to `triggerStartProcessing`, and a
`triggerStopProcessing` override was added to remove stale entries on
delete/disable (also resolves Medium #7 below).

**File:** `plugin.py:290-300`

The method is defined as `trigger_start_processing` (snake_case). Indigo's plugin
host calls this lifecycle hook by its exact, hard-coded camelCase name,
**`triggerStartProcessing(self, trigger)`** (confirmed against the local Indigo
docs: `llms-full.txt` lines 5413-5479, and the fact that every *other* overridden
Indigo lifecycle method in this file — `deviceUpdated`, `variableUpdated`,
`closedPrefsConfigUi`, `validateActionConfigUi`, `startup`, `shutdown` — correctly
uses Indigo's real camelCase names).

Because the name doesn't match, Indigo never calls this method at all; it silently
falls back to `indigo.PluginBase`'s default no-op implementation. The result:
`self.my_triggers` (line 58) is **never populated**, so the "Network Ping Device
Offline" event (`Events.xml`, `ping_offline`) and the trigger-firing logic in
`network_ping_device_action` (`plugin.py:1546-1554`) can never find a matching
trigger — `if dev_id in self.my_triggers` is always `False`. This entire feature
(defined, documented, and even covered by `test_ping_offline_event`) is dead in a
real running plugin.

There is also no `triggerStopProcessing` override, so even if the name were fixed,
deleted/disabled triggers would never be removed from `my_triggers`, leaking stale
trigger references (see also Medium #1 below).

**Fix direction:** rename to `triggerStartProcessing` and add a matching
`triggerStopProcessing` that removes the entry keyed by `offlineDevice`.

### 2. `run_concurrent_thread` is misnamed — network quality results never get logged
**Status: ✅ Fixed in v2025.2.13** — renamed to `runConcurrentThread`.

**File:** `plugin.py:1737-1753`

Same class of bug: Indigo calls `runConcurrentThread(self)` (confirmed:
`llms-full.txt` lines 4406-4451), not `run_concurrent_thread`. Since the name
doesn't match, Indigo never invokes it, so the `nq_queue`-draining loop that logs
network-quality test results never runs.

Concrete failure path: user runs the "Network Quality" menu item →
`network_quality()` (`plugin.py:1680-1705`) logs "Running network quality
test... results will be displayed when the test is complete" and pushes the
command onto `cmd_queue` → the background `command_thread` runs it and pushes the
result onto `nq_queue` → **nothing ever reads `nq_queue`**, because the only
consumer is the never-invoked `run_concurrent_thread`. The promised results never
appear in the log. (The parallel `networkQualityDeviceAction`, which updates
device states directly and synchronously via `subprocess.check_output`, is
unaffected — only the async, menu/action-triggered `network_quality()` path is
broken.)

**Fix direction:** rename to `runConcurrentThread`.

---

## 🟠 High severity

### 3. OS command injection via the Network Ping device's `hostname` field
**Status: ✅ Fixed in v2025.2.13** — replaced `os.system(f"...")` with
`subprocess.run([...], ...)` passing `hostname` as a separate argv element, so it
is never interpreted by a shell regardless of its contents.

**Files:** `Tools/ping_tool.py:58`, `Devices.xml:97-99`

```python
response = os.system(f"/sbin/ping -c 1 -t {timeout} {hostname}")
```

`hostname` comes straight from a free-text `Field id="hostname" type="textfield"`
(Devices.xml, no pattern/validation) or the equivalent menu-item field in
`Actions.xml:164`, and there is **no `validateDeviceConfigUi` method anywhere in
plugin.py** (grep confirms none exists) and no validation for the menu-item's
`hostname` field in `validateMenuItemConfigUi` either. The string is interpolated
directly into a shell command run via `os.system`.

A hostname value such as `example.com; rm -rf ~` (or any string containing `;`,
`` ` ``, `$()`, `|`, `&&`) is executed as shell metacharacters. Since this field is
plain user-supplied text with no server-side allow-listing, this is a real
command-injection vector, not just theoretical.

**Fix direction:** validate/sanitize the hostname (e.g. reject anything but
hostname-safe characters) and/or switch to `subprocess.run([...], shell=False)`
with the hostname as a separate argv element, never through a shell.

### 4. Same device has no numeric validation on `timeout` — crashes on bad input
**Status: ✅ Fixed in v2025.2.13** — added a `_parse_timeout()` helper that
catches `TypeError`/`ValueError`, logs a warning, and falls back to the 5-second
default instead of crashing.

**Files:** `Tools/ping_tool.py:37,51`, `Devices.xml:100-102`

`timeout = int(dev.ownerProps.get('timeout', '5'))` / `int(action.get('timeout',
'5'))` — the field is a free-text `textfield` with no `validateDeviceConfigUi`
backing it. A non-numeric value (blank, "abc", "5s") raises an uncaught
`ValueError` inside `do_the_ping`, which will surface as a generic plugin error
rather than a friendly validation message, for both the device and the "Network
Ping" menu item paths.

### 5. `pip_freeze.py` hard-codes a single Python version's absolute path
**Status: ✅ Fixed in v2025.2.13** — replaced the hard-coded path with
`[sys.executable, '-m', 'pip', 'freeze']`, so it always uses the pip belonging
to whichever interpreter is actually running the plugin.

**File:** `Tools/pip_freeze.py:22`

```python
result = subprocess.run(['/Library/Frameworks/Python.framework/Versions/3.13/bin/pip3', 'freeze'], ...)
```

This hard-codes Python 3.13 specifically. The repo's own build artifacts (compiled
`.pyc` files present for cpython-310, -311, and -313 across `Tools/__pycache__`)
indicate the plugin is expected to run under multiple Python versions. On any
Indigo install running a different Python (3.10, 3.11, or a future 3.14+), this
path doesn't exist and `subprocess.run` raises `FileNotFoundError`, uncaught,
crashing the "Pip Freeze Report" tool. It also silently reports the wrong
interpreter's packages if multiple Python frameworks are installed side by side.

**Fix direction:** use `sys.executable` (or Indigo's own advertised Python path)
instead of a hard-coded version string.

### 6. `modify_numeric_variable` doesn't catch all evaluation errors — validation and execution can both crash
**Status: ✅ Fixed in v2025.2.13** — broadened both `except` clauses to
`except Exception`, consistent with the intent already shown by the existing
error-message branches.

**Files:** `plugin.py:376-390` (`validateActionConfigUi`), `Tools/modify_numeric_variable.py:25-33`

Both the dialog validator and the actual action handler only catch
`(SyntaxError, TypeError)` / `SyntaxError` around
`Eval.eval_expr(var.value + expr)`. A perfectly plausible user formula like `/0`
(divide the variable by zero) raises `ZeroDivisionError`, which is not caught in
either place:

- In `validateActionConfigUi` (`plugin.py:385-390`), an uncaught `ZeroDivisionError`
  propagates out of the dialog-validation callback entirely instead of showing the
  intended "Please enter a valid formula" message — the config dialog would likely
  show a generic/ugly error instead of the graceful one this code was clearly
  designed to produce.
- At actual execution time (`Tools/modify_numeric_variable.py:25`), the same
  exception is uncaught and will surface as an unhandled plugin error rather than
  the "Error modifying variable %s" message the `except SyntaxError` branch is
  meant to produce.

Other likely runtime errors from arbitrary formula text (`NameError`, `IndexError`,
`OverflowError`) have the same gap.

**Fix direction:** broaden both `except` clauses to catch the realistic exception
set from expression evaluation (or a single `except Exception`), consistent with
the intent already shown by the existing error-message branches.

---

## 🟡 Medium severity

### 6b. "Subscribe to Changes" menu item forces a spurious restart-required flag on every save
**Status: ✅ Fixed in v2025.2.13** — both sides of the comparison are now
normalized to `bool` before comparing.

**File:** `Tools/subscribe_to_changes.py:26,33`

The save-time comparison checks whether the new value differs from the current
`indigo.activePlugin.pluginPrefs['enableSubscribeToChanges']`, which by the time
this dialog is saved has already been normalized to a real Python `bool` (by the
migration in `plugin.py:267-270`, confirmed real and correctly guarded with
`isinstance(raw, str)` — see Methodology note above). But the dialog's own
`values_dict['enableSubscribeToChanges']` arrives as the raw dialog value (a
string/checkbox value such as `"true"`/`"false"`), and line 26 compares the two
directly with `==` instead of normalizing both sides the way line 33 does when
*saving* the new value. `bool == str` is always `False` in Python, so
`restart_required` evaluates `True` every single time this dialog is saved —
even when the checkbox wasn't touched — forcing an unnecessary plugin restart
on every save.

**Fix direction:** normalize both sides (e.g. compare
`str(current_pref).lower() == str(new_value).lower()`) before deciding whether a
restart is actually required.

### 6c. `backup_from_action` has no guard around a blank/invalid retention count
**Status: ✅ Fixed in v2025.2.13** — the `int()` conversion is now wrapped in a
try/except that logs the same "Database backup aborted" style message and
returns `False` instead of crashing.

**File:** `Tools/database_backup.py:160-162`

```python
def backup_from_action(action_group: indigo.actionGroup = None) -> bool:
    backup_folder = indigo.activePlugin.substitute(action_group.props['backup_folder']).strip()
    retain_count  = int(action_group.props['retain_count'])
    return backup(backup_folder, retain_count)
```

Unlike `backup()` itself (called here, and which is defensively wrapped in
`try/except Exception`), the `int(...)` conversion happens in the caller,
*outside* that try block. The `retain_count` Action field (`Actions.xml:441`) is a
free-text field defaulting to `"5"` but user-editable/clearable; if a user clears
it and saves, `int('')` raises `ValueError` uncaught, crashing the "Backup Indigo
Database" action with a raw traceback instead of the graceful "Database backup
aborted"-style handling the rest of this module is designed to produce.
(`backup_folder` is safe — `backup()` checks for an empty string and logs/returns
`False`.)

### 6d. `email_battery_level_report` crashes if no Email+ device is configured
**Status: ✅ Fixed in v2025.2.13** — the `int()` conversion is now wrapped in a
try/except that logs a clear message and returns `False` instead of crashing.

**File:** `plugin.py:1060`

```python
email_device = int(action_group.props['email_device'])
```

`email_device` is populated from a `menu` field built from `indigo.devices`
filtered to `com.indigodomo.email` devices. If no Email+ device is installed or
configured on the server, that menu can be empty and the prop an empty string —
`int('')` raises `ValueError` uncaught, so the action fails with a raw traceback
rather than a clear "please configure an Email+ device" message.

### 6e. Corrupted/hand-edited `showDebugLevel` pref can prevent the plugin from starting at all
**Status: ✅ Fixed in v2025.2.13** — both the `__init__` and
`closedPrefsConfigUi` read sites now validate the value is a known debug level
and fall back to 30 (Warning) otherwise.

**File:** `plugin.py:61,105-107`

```python
self.debug_level: int = int(self.pluginPrefs.get('showDebugLevel', '30'))
...
self.indigo_log_handler.setLevel(self.debug_level)
```

and later `DEBUG_LABELS[self.debug_level]` (`constants.py`). Both assume
`showDebugLevel` is always one of the five known values (`10`/`20`/`30`/`40`/`50`).
If plugin prefs are ever corrupted, hand-edited, or carried over incorrectly across
a plugin version change, `int()` can raise `ValueError` or the later
`DEBUG_LABELS[...]` lookup can raise `KeyError` — and because the first occurrence
is in `__init__`, an uncaught exception there would prevent the plugin from
starting at all. Low likelihood, but high impact and easy to guard with a
fallback.

### 6f. `CLAUDE.md` (and the wiki) claim python-dotenv ships with the plugin — it doesn't
**Status: ⚠️ Partially fixed in v2025.2.13** — corrected the claim in this
repo's `CLAUDE.md`. `Multitool.wiki/Home.md` carries the same stale claim but
is a separate git repository per this project's own conventions, so it was
intentionally left untouched here.

**Files:** `Multitool.indigoPlugin/Contents/Server Plugin/requirements.txt`,
project `CLAUDE.md`, `Multitool.wiki/Home.md` (separate repo, noted for
completeness only)

This project's own `CLAUDE.md` states: *"Starting with plugin version 2024.1, one
external dependency will be installed with the plugin which is called
python-dotenv."* This is no longer true. Git history shows `python-dotenv` was
added to `requirements.txt` in commit `6d9c335` (2024-10-06), but the entire file
was deleted the very next day in `3777054` and later recreated from scratch in
`80bc8b5` (2025-03-13, "Adds Lorem Ipsum tool") containing only `lorem==0.1.1` —
confirmed as the file's current, complete contents. `python-dotenv` is in fact only
a **test-time** dependency: it's imported directly in `tests/test_plugin.py` and
declared in the read-only `tests/shared/module-requirements.txt` submodule file,
never in the plugin's own shipped `requirements.txt`. The
`Multitool.Packages/pip-install-log-success.txt` / `3.13-pip-install-log-success.txt`
logs confirm only `lorem` is ever actually installed alongside the shipped plugin.

**Fix direction:** either restore `python-dotenv` to the plugin's `requirements.txt`
if it's genuinely meant to ship, or correct `CLAUDE.md` (and the wiki) to state
it's a test-only dependency installed via the test submodule, not something
end users' installs receive.

### 7. Stale trigger references never cleaned up (compounds Critical #1)
**Status: ✅ Fixed in v2025.2.13** — see #1 above; `triggerStopProcessing` now
removes the entry.

**File:** `plugin.py:290-300`

Even independent of the naming bug above, there is no `triggerStopProcessing`
override at all. Once (if) a trigger is registered in `self.my_triggers`, deleting
or disabling that trigger in Indigo leaves a dangling reference: the `not in
self.my_triggers` guard (line 299) means a *new* trigger created afterward for the
same `offlineDevice` would never overwrite the stale one, and firing against a
deleted trigger ID (`plugin.py:1548`, `indigo.trigger.execute(event_id)`) would
error since that trigger no longer exists.

### 8. `battery_level.report()` silently omits devices at exactly 0% battery
**Status: ✅ Fixed in v2025.2.13** — changed to `if dev.batteryLevel is not None:`.

**File:** `Tools/battery_level.py:29`

```python
for dev in indigo.devices.iter("indigo.zwave"):
    if dev.batteryLevel:
        collection[dev.name] = dev.batteryLevel
```

`if dev.batteryLevel:` is `False` when the battery level is `0` (Python
truthiness), so devices with a fully dead battery — arguably the single most
important case a "Battery Level Report" exists to surface — are silently excluded
from the report, indistinguishable from devices that simply don't report a battery
level (`None`).

**Fix direction:** `if dev.batteryLevel is not None:`.

### 9. `installed_plugins.py` crashes if the "Plugins (Disabled)" folder doesn't exist
**Status: ✅ Fixed in v2025.2.13** — wrapped in try/except, treating a missing
folder as an empty list.

**File:** `Tools/installed_plugins.py:28-29`

```python
for plugin_folder in ('Plugins', 'Plugins (Disabled)'):
    plugins_list = os.listdir(indigo_install_path + '/' + plugin_folder)
```

No try/except. On an Indigo install where no plugin has ever been disabled, this
folder may not exist, and `os.listdir` raises `FileNotFoundError` uncaught,
aborting the whole report (including the `Plugins` half that would have
succeeded).

### 10. `installed_plugins.py` docstring/comment says it excludes itself; the code doesn't
**Status: ✅ Fixed in v2025.2.13** — per the user's decision, resolved by
removing the stale comment rather than changing report behavior; Multitool
continues to list itself like any other installed plugin.

**File:** `Tools/installed_plugins.py:44` (comment) vs. the loop body

```python
# Don't include self (i.e. this plugin) in the plugin list
cf_bundle_display_name = plug_list["CFBundleDisplayName"]
```

The comment claims Multitool excludes itself from the "Installed Plugins" report,
but there is no filtering logic (no check against `CFBundleIdentifier ==
"com.fogbert.indigoplugin.multitool"` or similar) — Multitool lists itself like
any other plugin. Either the comment is stale (feature was removed/never
implemented) or the filter was intended and never written; either way the
docstring is misleading.

### 11. `error_inventory.show_inventory` has no error handling around log-file reads
**Status: ✅ Fixed in v2025.2.13** — reads are now wrapped in try/except
(`OSError`, `UnicodeDecodeError`), skipping unreadable files with a debug log
instead of aborting the whole inventory. Also switched to streaming reads
line-by-line instead of loading whole files into memory (see also #27c).

**File:** `Tools/error_inventory.py:41-49`

`open(..., "r", encoding="utf-8")` / `infile.read()` inside a nested loop over every
file under the logs folder, with no try/except. A single log file that isn't valid
UTF-8 (e.g. a plugin that wrote non-UTF8 bytes, or a binary file that ended up in
the logs folder) raises `UnicodeDecodeError` uncaught, aborting the entire error
inventory before it can process any remaining files.

### 12. `device_last_successful_comm.py` sort can crash if any device never
communicated
**Status: ✅ Fixed in v2025.2.13** — replaced the reversed-tuple sort trick
with two stable sorts (name ascending, then comm descending with `None`
treated as oldest), which also fixes the unintended name-descending tie-break.

**File:** `Tools/device_last_successful_comm.py:33,42`

```python
table = [(dev.id, dev.name, dev.lastSuccessfulComm) for dev in indigo.devices.iter(filter=dev_filter)]
...
table = sorted(table, key=lambda t: t[::-1], reverse=True)
```

If `dev.lastSuccessfulComm` can be `None` for any device in the selected filter
(e.g. a newly created or never-communicated device — the local Indigo docs sample
payloads always show a populated ISO date, so this could not be confirmed either
way from documentation alone), sorting tuples that mix `None` and `datetime` values
for the same tuple position raises `TypeError: '<' not supported between instances
of 'NoneType' and 'datetime.datetime'`, aborting the report. Worth a quick manual
check against a real device that has never successfully communicated before ruling
this out.

Separately, the reversed-tuple sort trick (`t[::-1]`, `reverse=True`) sorts by comm
time descending as intended, but ties are broken by device **name descending**
(Z→A) rather than the more natural ascending order — likely an unintended
side-effect of the trick rather than a deliberate choice.

### 13. `results_output.py` swallows all errors with a bare `except:`
**Status: ✅ Fixed in v2025.2.13** — narrowed to `except (TypeError, ValueError):`.

**File:** `Tools/results_output.py:32-35`

```python
try:
    indigo.server.log(f"\n{dict(thing)}")
except:
    indigo.server.log(f"\n{thing}")
```

A bare `except:` catches everything, including `KeyboardInterrupt`/`SystemExit`
and unrelated bugs, and silently falls back to printing `thing`'s `repr`/`str`
without ever surfacing what actually went wrong. This is the only bare `except:`
found in the Tools/ package (other files consistently use typed excepts or, at
worst, `except Exception:`), so it stands out as inconsistent with the rest of the
codebase's error-handling style.

### 14. Six "print/list selected Indigo object" tools have no validation and can crash on an unselected/stale field
**Status: ✅ Fixed in v2025.2.13** — all six now wrap the lookup in a
try/except, matching `indigo_methods.py`'s existing graceful-degradation
pattern (log a warning and return/return an empty list, rather than crash).

**Files:** `Tools/results_output.py:26`, `Tools/object_directory.py:26`,
`Tools/object_dependencies.py:26,29`, `Tools/inspect_method.py:32`,
`Tools/log_of_method.py:27-28`, `Tools/dict_to_print.py:29` (same pattern, one
level up — `getattr(indigo, values_dict['classOfThing'])` alone, feeding the
`classOfThing` picker itself)

All six share the same unguarded pattern:

```python
thing = getattr(indigo, values_dict['classOfThing'])[int(values_dict['thingToPrint'])]
```

None of these wrap the `getattr`/index lookup in a try/except. Contrast with
`Tools/indigo_methods.py:27-41`, which wraps the equivalent `getattr` in
`try/except (AttributeError, TypeError)` and degrades gracefully to an empty list.
If `classOfThing` is empty/invalid (e.g. dialog opened before a class is picked) or
`thingToPrint` refers to an object that was deleted between dialog-open and
submit, these six callbacks raise `AttributeError`/`KeyError`/`ValueError`
uncaught. This is a real inconsistency across a family of near-identical tools —
worth fixing them all the same way `indigo_methods.py` already does.

### 15. Module-level mutable `indigo.Dict()` reused as scratch state across calls
**Status: ✅ Fixed in v2025.2.13** — each of the three surviving files now
constructs a fresh `indigo.Dict()` inside the function, only when actually
needed, instead of a shared module-level singleton. (The fourth file,
`substitution_generator.py`, was deleted as dead code — see #16.)

**Files:** `Tools/device_beep.py:11`, `Tools/speak_string.py:11`,
`Tools/send_status_request.py:11`, `Tools/substitution_generator.py:13`

```python
ERR_MSG_DICT = indigo.Dict()
```

declared once at import time and mutated in place on every call (`ERR_MSG_DICT['x']
= ...`) instead of constructing a fresh `indigo.Dict()` per call. In a
single-threaded, single-call-at-a-time context this happens to work today, but it
is fragile shared mutable state: entries from a previous error never get cleared,
so if a future code path reads `ERR_MSG_DICT` without first checking whether an
error actually occurred this run, it could see stale keys from an earlier failed
call. It also means these four tools are not safe to call concurrently from
different threads.

### 16. Two duplicate, both-dead "Substitution Generator" implementations
**Status: ✅ Fixed in v2025.2.13** — per the user's decision, deleted both
dead modules along with their commented-out `plugin.py` shims, the orphaned
`generator_state_or_value` shim that only existed to feed them (confirmed via
grep to have no XML references of its own), and the stale `__all__` entries
in `Tools/__init__.py` (including the unrelated dangling `"man_page"` reference).

**Files:** `Tools/generator_substitutions.py`, `Tools/substitution_generator.py`,
`plugin.py:1308-1311,1888-1892`, `Tools/__init__.py:18,41`

There are two separate modules that appear to implement the same never-shipped
feature (build an `%%d:ID:state%%` / `%%v:ID%%` substitution string from a
device/variable picker):

- `generator_substitutions.py` (`return_substitution`) — excluded from
  `Tools/__init__.py`'s `__all__` (line 18, commented out).
- `substitution_generator.py` (`get_substitute`) — *is* in `__all__` (line 41,
  not commented out) but still unused.

Both of their corresponding `plugin.py` callback shims are commented out
(`generator_substitutions` at lines 1308-1311, `substitution_generator` at lines
1888-1892), and no "Substitution Generator" menu item or action exists in
`MenuItems.xml`/`Actions.xml` — confirmed by grep, no match. Neither module is
reachable from any UI. This looks like an abandoned/incomplete feature left in two
different half-finished forms; as-is it's dead code that could confuse future
maintainers into thinking one of them is live. `Tools/__init__.py`'s `__all__`
list is itself inconsistent about this: `"generator_substitutions"` is commented
out (line 18) while `"substitution_generator"` is left active (line 41) — neither
module is actually reachable, so this distinction is meaningless either way. The
same `__all__` list also still references `"man_page"` (commented out, line 27) even
though no `man_page.py` file exists anywhere in the repo — the changelog shows the
"Man Page" tool was deliberately removed (commit `7caecba`, "Removes Man Page tool
as feature deprecated by Apple in Ventura"), so this is a stale leftover from that
removal that was never cleaned out of the module list.

`generator_substitutions.py` also has its own latent bug if it were ever wired
up: `int(values_dict['devVarMenu'])` (line 29) will raise `ValueError` uncaught if
the field is empty (e.g. dialog opened before a selection is made).

### 17. `kDefaultPluginPrefs` is dead, and its one entry isn't a real plugin pref
**Status: ✅ Fixed in v2025.2.13** — deleted `plugin_defaults.py` and the
dead import, per the audit's own conclusion that it was dead code either way.

**Files:** `plugin_defaults.py`, `plugin.py:29`

```python
kDefaultPluginPrefs = {
    'get_attrib_dict': 'bar'
}
```

Imported in `plugin.py:29` with `# noqa` (suppressing the unused-import lint
warning) but **never referenced anywhere else in the file** — confirmed by grep.
Its module docstring claims "The plugin only has one default pref which is logging
level," but the dict doesn't contain a logging-level key (the real one is
`showDebugLevel`, read via `.get('showDebugLevel', '30')` at `plugin.py:61`) — it
contains `get_attrib_dict`, which is the name of an unrelated static method on the
`Plugin` class (`plugin.py:115`). This reads like a leftover placeholder/typo
rather than an intentional default, and the module is effectively dead code either
way.

### 17b. `deviceUpdated`/`variableUpdated` parse the subscribed-items list without a guard
**Status: ✅ Fixed in v2025.2.13** — added a `_parse_id_list()` helper that
skips (and logs) malformed tokens instead of raising; used by both call sites.

**Files:** `plugin.py:163-165` (`deviceUpdated`), `plugin.py:321-323`
(`variableUpdated`)

```python
subscribed_items = [int(_) for _ in track_list.replace(' ', '').split(',')]
```

No try/except around the list comprehension. In normal use `track_list` comes from
a list-selection control that only ever offers valid device/variable IDs, so this
is unlikely to see malformed content in practice — but nothing defends against a
corrupted or hand-edited `subscribedDevices`/`subscribedVariables` pref value, and
this hook fires on *every* device/variable change server-wide while the "Subscribe
to Changes" feature is enabled, so a single bad token would raise repeatedly.

### 17c. `color_picker.picker()` doesn't catch a missing `chosenColor` key
**Status: ✅ Fixed in v2025.2.13** — added `KeyError` to the except clause and
switched the handler's own re-read to `.get()`.

**File:** `Tools/color_picker.py:32,42`

```python
if not values_dict['chosenColor']:
    ...
except (AttributeError, ValueError):
    logger.warning("Can not convert: input value %s is wrong type.", values_dict['chosenColor'])
```

Only `AttributeError`/`ValueError` are caught; if `values_dict` doesn't contain a
`'chosenColor'` key at all, line 32 raises `KeyError` uncaught. The `except`
handler itself also re-reads `values_dict['chosenColor']`, so it isn't a safe
fallback for that scenario either.

### 18. Version-string comparisons use lexicographic string ordering
**Status: ✅ Fixed in v2025.2.13** — added a `_version_at_least()` helper that
compares dotted version strings as integer tuples.

**Files:** `Tools/find_linked_scripts.py:60`, `Tools/database_backup.py` (n/a —
not present there), and the pattern generally

```python
if not indigo.server.version >= "2024.1.0":
```

Comparing version strings with Python's default string ordering works only by
coincidence while all the numeric components stay single-digit. If Indigo (or a
future comparison against something like `"2024.10.0"`) ever has a two-digit minor
or patch number, lexicographic comparison gives the wrong answer (`"2024.9.0" >
"2024.10.0"` is `True` under string comparison, which is semantically backwards).
Low likelihood given Indigo's actual release cadence, but worth a proper version
tuple comparison (e.g. split on `.` and compare as ints) rather than relying on
string luck.

---

## 🟢 Low severity / robustness nits

### 19. `find_embedded_scripts.py` / `find_linked_scripts.py` use a shared module-level list as scratch state
**Status: ✅ Fixed in v2025.2.13** — `obj_list` is now a local variable in
`make_report()`, reset fresh per section and passed explicitly to
`build_report()`; no more module-level state to leak across calls.

**Files:** `Tools/find_embedded_scripts.py:10,27,41`, `Tools/find_linked_scripts.py:11,28,41`

```python
obj_list = []  # Container for objects with embedded scripts [(obj.id, obj.name), ...]
```

is a module-level global, appended to per object-type section and cleared via
`obj_list.clear()` inside `sort_obj_list` after each section's report is built.
Within a single successful `make_report()` call this self-clearing pattern works,
but if an exception is raised partway through one section (e.g. a malformed
`rawServerRequest` entry), `obj_list` is never cleared and the *next* invocation's
first section report will include leftover entries from the aborted previous run.
It's also not safe under concurrent invocation. Low likelihood in practice given
Indigo's typical single-action-at-a-time execution model, but worth converting to
a local variable threaded through the helper functions instead of global state.

### 20. `indigo_inventory.py` uses the root logger instead of the "Plugin" logger
**Status: ✅ Fixed in v2025.2.13** — changed to `logging.getLogger("Plugin")`.

**File:** `Tools/indigo_inventory.py:12`

```python
LOGGER = logging.getLogger()
```

Every other module in `Tools/` uses `logging.getLogger("Plugin")`. This one
requests the root logger instead — almost certainly a copy-paste slip. Harmless in
practice since `LOGGER` is never actually used in this file, but worth fixing for
consistency (or removing the unused variable).

### 21. `indigo_inventory.py` can raise on a genuinely empty Indigo database
**Status: ✅ Fixed in v2025.2.13** — added `default=0` to each `max()` call.

**File:** `Tools/indigo_inventory.py:108-111`

```python
col0 = max(len(f"{item}") for item in col_0) + 2
```

If every one of Action Groups / Control Pages / Devices / Schedules / Triggers /
Variables is empty (a brand-new/minimal Indigo install), `col_0` etc. are empty
lists and `max()` raises `ValueError: max() arg is an empty sequence`, uncaught.
Edge case, but easy to guard with a default.

### 22. Misleading validation error message for "Modify Time Variable"
**Status: ✅ Fixed in v2025.2.13** — message now describes the actual required
format (`YYYY-MM-DD HH:MM:SS.ffffff`) instead of "POSIX timestamp".

**File:** `plugin.py:392-399`

```python
if type_id == "modify_time_variable":
    var = indigo.variables[int(action_dict['list_of_variables'])]
    try:
        dt.datetime.strptime(var.value, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        error_msg_dict['list_of_variables'] = "The variable value must be a POSIX timestamp."
```

The actual required format is a specific datetime string
(`YYYY-MM-DD HH:MM:SS.ffffff`), not a POSIX/Unix timestamp (an integer/float
seconds-since-epoch). Telling a user their variable "must be a POSIX timestamp"
when it must instead exactly match a particular strftime pattern will send them
looking for the wrong kind of value.

### 23. Vestigial `stop_event` flag on `MyThread`
**Status: ✅ Fixed in v2025.2.13** — removed the dead attribute; `stop()` now
just logs, with a comment pointing at the real stop mechanism.

**File:** `plugin.py:2024-2030`

```python
def stop(self) -> None:
    self.logger.debug("Stopping command thread.")
    self.stop_event = True
```

`self.stop_event` is set but never read anywhere (the actual shutdown mechanism is
`self.cmd_queue.put(None)` in `shutdown()`, which unblocks `execute_command`'s
`queue.get()` and lets its `if my_command is None: break` do the real work). Not a
bug, just dead state that suggests a stop mechanism that was never finished or was
superseded and not cleaned up.

### 24. Column-width miscalculation in `device_inventory.py`
**Status: ✅ Fixed in v2025.2.13** — width is now computed from the same
formatted string that's actually printed.

**File:** `Tools/device_inventory.py:50,74`

The `lastChanged` column width (`x_3`) is computed from `len(f"{thing[3]}")` —
the default `str(datetime)` representation, which includes microseconds (up to 26
chars) — but the value actually printed uses
`dt.datetime.strftime(thing[3], '%Y-%m-%d %H:%M:%S')` (fixed 19 chars, no
microseconds). The column ends up wider than necessary. Cosmetic only.

### 25. `modify_time_variable.py` mixes an f-string with `%`-style logging args
**Status: ✅ Fixed in v2025.2.13** — removed the pointless `f` prefix.

**File:** `Tools/modify_time_variable.py:46`

```python
LOGGER.critical(f"Error modifying variable %s.", var.name)
```

The `f""` prefix is pointless here (there's no `{}` interpolation inside it) but
is confusing to read next to the `%s`/`var.name` logging-style substitution — looks
like a half-converted f-string that could mislead a future editor into thinking
`%s` is a literal.

### 26. `networkPing`-only `hostname`/`timeout` fields have no separator visual grouping issue
**Status: ✅ Fixed in v2025.2.13** — removed the dead trailing separator.

**File:** `Devices.xml:103` — `<Field id="sep_1" type="separator"/>` at the very
end of the `ConfigUI`, after the last field, so it renders nothing (a separator
after the last field has no next field to separate from). Purely cosmetic/dead
markup.

### 27b. Stray/dead `method` attribute directly on a `<Field>` element
**Status: ✅ Fixed in v2025.2.13** — removed the stray attribute.

**File:** `MenuItems.xml:344`

```xml
<Field id="classOfThing" type="menu" method="dict_to_print">
```

A `method` attribute placed directly on `<Field>` isn't a recognized location for a
dynamic-list callback in Indigo's dialog schema — the correct pattern (used two
fields later in this same file, on `thingToPrint`) puts `method=` on the nested
`<List class="self" method="...">` element instead. Here, `classOfThing`'s actual
list is a static set of `<Option>` values with `<CallbackMethod>__dummyCallback__
</CallbackMethod>`, so the stray `method="dict_to_print"` attribute does nothing —
Indigo silently ignores unrecognized attributes. Purely dead/misleading markup, not
a functional break, but reads as though `classOfThing` itself drives
`dict_to_print`, which it doesn't (that's actually driven by `thingToPrint`'s
`<List>`).

### 27c. `error_inventory.py` reports accumulate on disk indefinitely and read whole files into memory
**Status: ✅ Fixed in v2025.2.13** — added `_prune_old_reports()`, keeping the
newest 10 report files (mirroring `database_backup.py`'s retention pattern);
input log reads now stream line-by-line (see also #11).

**File:** `Tools/error_inventory.py:41-49` and report-file creation logic

Every run writes a new `Multitool Plugin Error Inventory N.txt` file with no cap or
pruning — unlike `database_backup.py`, which has an explicit `retain_count`
mechanism for exactly this kind of repeated-output accumulation. Repeated use of
this tool silently accumulates files forever. Separately, each log file under the
Indigo logs folder is read fully into memory via `infile.read()` rather than
streamed line-by-line, which could matter on a server with large/verbose logs.

### 27d. README badges are stale relative to the shipped plugin/API version
**Status: ⚠️ Partially fixed in v2025.2.13** — corrected the Indigo badge to
2023.2, the actual minimum version implied by `Info.plist`'s
`ServerApiVersion 3.4` (per Indigo's own docs, API 3.4 shipped in Indigo
2023.2 — an objective, sourced fact). Left the Python badge as-is: the plugin
doesn't declare an explicit minimum Python version anywhere, and picking one
without the maintainer's input risked swapping one guess for another.

**File:** `README.md:2`

```
![indigo-version](.../Indigo-2023.0-blueviolet.svg) ![python-version](.../Python-3.10-darkgreen.svg)
```

`Info.plist` reports `PluginVersion 2025.2.12` / `ServerApiVersion 3.4`, and
compiled `.pyc` caches throughout `Tools/__pycache__` show the plugin has actually
been exercised under Python 3.9, 3.10, 3.11, and 3.13 — these badges read as
leftover from an earlier release and don't appear to have been updated alongside
subsequent version/API bumps.

### 27e. `_to_do_list.md` is a placeholder, not a real backlog
**Status: ⬜ No fix needed** — per the user's decision, left as-is; not a bug.

**File:** `_to_do_list.md`

The entire tracked file content is a single line, `- nothing`. Harmless, but worth
flagging: a tracked file with only a placeholder line is easy to mistake for an
abandoned backlog versus "intentionally empty, tracked elsewhere (e.g. GitHub
Issues)." Consider removing the file if it's not the real to-do mechanism, or
noting where the real backlog lives.

### 27. Offline-trigger device picker isn't filtered to Network Ping devices
**Status: ✅ Fixed in v2025.2.13** — `get_device_list` now filters to
`indigo.devices.iter(filter="self.networkPing")`; confirmed via grep it's the
picker's only caller, so no other dialog is affected.

**File:** `Events.xml:11-14`

```xml
<Field id="offlineDevice" type="menu">
    <List class="self" filter="" method="get_device_list"/>
</Field>
```

`get_device_list` (`plugin.py:204-217`) returns *all* Multitool-owned devices,
including Network Quality devices, not just Network Ping devices. A user can
configure the "Network Ping Device Offline" trigger against a Network Quality
device, which has no `status` state and will never actually go offline in the
sense this trigger checks — an easy-to-make, silently-inert configuration. (Also
currently moot given Critical #1, which means this trigger doesn't fire at all
regardless of which device is picked.)

---

## Test suite observations

The test suite (`tests/test_plugin.py`, 707 lines) is an integration suite that
talks to a live Indigo Web Server instance via `tests/shared`'s `APIBase`/HTTP
helpers — it requires a real, running, configured Indigo server plus
`tests/.env` values (`PLUGIN_ID`, `URL_PREFIX`, `GOOD_API_KEY`, etc.), not a
mocked unit-test harness. That's consistent with the `indigo-plugin-testing`
skill's TestingBase pattern and with CLAUDE.md's description of the test
framework, so this isn't itself a finding — just context for the notes below.

- **Coverage looks broad for wired-up features.** Every action/menu item that is
  actually reachable from `Actions.xml`/`MenuItems.xml` appears to have at least a
  smoke test (`test_multi_tool_reports` alone covers 8 report actions via the
  hidden `menu_item_reports` shim). The two never-wired "Substitution Generator"
  modules (finding #16) have no tests, consistent with them being dead code.
- **`test_multi_tool_reports` only checks `status_code == 200`**, not the actual
  log content/report output. This means it would not catch, for example, the
  battery-level 0%-omission bug (#8) or the misleading "must be a POSIX
  timestamp" message (#22) — it verifies the endpoint doesn't error, not that the
  output is correct. It likely *would* catch the `pip_freeze.py` hard-coded-path
  bug (#5) on any machine/CI runner where Python 3.13 isn't installed at that
  exact framework path, which is worth knowing if that test ever starts failing
  in an environment that isn't the primary dev machine.
- **Nothing in the suite exercises the actual Indigo trigger lifecycle** for
  `test_ping_offline_event` — worth checking what it currently does verify, since
  given Critical #1 (`trigger_start_processing` is never called by a real Indigo
  server), a test that only calls the bridge method directly via
  `plugin.executeAction()` would not surface that the real lifecycle hook is
  misnamed. This is exactly the kind of gap where a naming bug like #1 and #2 can
  hide indefinitely: nothing in this repo's test suite calls
  `triggerStartProcessing`/`runConcurrentThread` by their real names the way the
  Indigo server would.
- `tests/test_plist.py` and `tests/test_xml.py` are structural/shape validators
  (required keys present, bundle ID format, well-formed XML) — useful as a
  regression net for packaging mistakes, but they don't (and aren't meant to)
  validate that callback methods referenced in the XML actually exist and are
  correctly named in `plugin.py`. This audit's cross-check (see "XML ↔
  implementation cross-check" below) is a check this repo doesn't currently
  automate anywhere.
- **Near-total lack of negative/error-path testing.** Of roughly 30 action/menu-item
  tests in `tests/test_plugin.py`, only two explicitly exercise a failure path
  (`test_backup_indigo_database_invalid_retain_count`, and the
  `test_find_object_by_id_*` not-found/invalid-token cases). Every other action —
  `modify_numeric_variable`, `modify_time_variable`, `networkPingDeviceAction`,
  `networkQualityDeviceAction`, `send_status_request`, `subscribe_to_changes`, etc.
  — only exercises the happy path against a valid, pre-configured object ID. Given
  that several of this audit's own findings (#6, #6c, #6d, #14, #17c) are exactly
  "an edge-case input raises an uncaught exception," this looks like a real,
  non-hypothetical coverage gap rather than a hypothetical one.
- The suite is entirely integration-style, requiring 15+ real `.env`-configured
  object IDs against a live Indigo server (`GENERAL_DEVICE_ID`, `SCHEDULE_ID`,
  `PING_OFFLINE_TRIGGER_ID`, etc.), consistent with this project's documented
  `tests/shared`/TestingBase pattern. One consequence worth knowing: if any
  referenced env var is unset, `os.getenv(...)` silently returns `None` rather than
  failing fast with a clear "test environment not configured" error — an
  unconfigured environment can present as mysterious plugin failures rather than
  an obvious setup problem.
- Minor: `_execute_action`/`_assert_response` helpers are duplicated verbatim
  across the `TestPluginActions`/`TestPluginMenuItems`/`TestPluginEvents` classes.
  The `TestPluginMenuItems` copy hardcodes `timeout=90` with a comment noting it's
  needed for the network-quality CLI call, but `TestPluginActions`'s copy of the
  same helper (used by `test_network_quality_action`) has no such override — worth
  checking that the default timeout is actually long enough there too, since the
  comment elsewhere implies it isn't safe to assume.
- Minor: `test_backup_indigo_database_menu_item` writes real backup files to the
  actual `~/Desktop` of whatever machine runs the suite and infers "created" via a
  before/after directory diff filtered by today's date. On a personal dev machine
  where the real plugin might also be manually exercised around the same time,
  there's a narrow but real chance of misattributing or cleaning up a genuine
  manually-created backup in the test's `finally` block.

---

## XML ↔ implementation cross-check

- Every `CallbackMethod`/list-generator `method=` name referenced across
  `Actions.xml`, `MenuItems.xml`, `Devices.xml`, `Events.xml`, and
  `PluginConfig.xml` resolves to an existing method in `plugin.py` (verified via
  diff of grepped names against `def` sites). No orphaned XML references to
  missing methods were found.
- No duplicate field `id`s within the same `<Action>`/`<MenuItem>` element were
  found (cross-element duplicates are normal/expected in Indigo XML and were
  excluded from consideration).
- All five XML files parse as well-formed XML.
- `_changelog.md`'s top entry (`v2025.2.13`) is an in-progress, unreleased
  entry consolidating all fixes from this audit; `Info.plist`'s
  `PluginVersion` was bumped to match.
- `requirements.txt` (`lorem==0.1.1`) does not include `python-dotenv`, which is
  in fact correct for what actually ships — this used to contradict the
  project's own `CLAUDE.md` (see finding #6f, now fixed).

---

## Summary

All findings below were addressed in a single follow-up session
(`v2025.2.13`, still unreleased). ✅ = code/doc fixed as recommended.
⚠️ = fixed within this repo's scope but a related instance was intentionally
left untouched (documented in the finding). ⬜ = no fix applied, per an
explicit user decision that it isn't a bug. Every fix was verified with
`py_compile`/`xmllint` and the static (`test_plist.py`/`test_xml.py`) test
suite; the live-server integration suite (`test_plugin.py`) was not run since
it requires a configured Indigo server, which this environment doesn't have.

| # | Finding | Severity |
|---|---|---|
| 1 | `trigger_start_processing` misnamed — offline-ping trigger never fires ✅ Fixed v2025.2.13 | Critical |
| 2 | `run_concurrent_thread` misnamed — network quality results never logged ✅ Fixed v2025.2.13 | Critical |
| 3 | Command injection via ping device `hostname` field ✅ Fixed v2025.2.13 | High |
| 4 | Unvalidated `timeout` field crashes ping tool on bad input ✅ Fixed v2025.2.13 | High |
| 5 | `pip_freeze.py` hard-codes a Python 3.13-only path ✅ Fixed v2025.2.13 | High |
| 6 | `modify_numeric_variable` doesn't catch `ZeroDivisionError` etc. ✅ Fixed v2025.2.13 | High |
| 6b | "Subscribe to Changes" save always forces a spurious restart-required flag ✅ Fixed v2025.2.13 | Medium |
| 6c | `backup_from_action` crashes on a blank/invalid retention count ✅ Fixed v2025.2.13 | Medium |
| 6d | `email_battery_level_report` crashes with no Email+ device configured ✅ Fixed v2025.2.13 | Medium |
| 6e | Corrupted `showDebugLevel` pref could prevent plugin startup ✅ Fixed v2025.2.13 | Medium |
| 6f | `CLAUDE.md`/wiki falsely claim python-dotenv ships with the plugin ⚠️ Partially fixed v2025.2.13 (CLAUDE.md only; wiki is a separate repo) | Medium |
| 7 | No `triggerStopProcessing` — stale trigger references ✅ Fixed v2025.2.13 | Medium |
| 8 | Battery report omits 0%-battery devices ✅ Fixed v2025.2.13 | Medium |
| 9 | `installed_plugins.py` crashes if "Plugins (Disabled)" folder is missing ✅ Fixed v2025.2.13 | Medium |
| 10 | `installed_plugins.py` comment says it excludes itself; it doesn't ✅ Fixed v2025.2.13 (comment corrected, behavior unchanged — user's choice) | Medium |
| 11 | `error_inventory.py` has no error handling reading log files ✅ Fixed v2025.2.13 | Medium |
| 12 | `device_last_successful_comm.py` sort may crash on `None` comm time ✅ Fixed v2025.2.13 | Medium |
| 13 | Bare `except:` in `results_output.py` ✅ Fixed v2025.2.13 | Medium |
| 14 | 6 "print/list object" tools lack validation present in a sibling tool ✅ Fixed v2025.2.13 | Medium |
| 15 | Shared mutable module-level `ERR_MSG_DICT` in 4 files ✅ Fixed v2025.2.13 | Medium |
| 16 | Two dead, duplicate "Substitution Generator" implementations (+ stale `__all__`) ✅ Fixed v2025.2.13 (deleted — user's choice) | Medium |
| 17 | `kDefaultPluginPrefs` is dead code with a bogus entry ✅ Fixed v2025.2.13 (deleted) | Medium |
| 17b | `deviceUpdated`/`variableUpdated` parse subscribed-items list unguarded ✅ Fixed v2025.2.13 | Low |
| 17c | `color_picker.picker()` doesn't catch a missing `chosenColor` key ✅ Fixed v2025.2.13 | Low |
| 18 | Version comparisons use lexicographic string ordering ✅ Fixed v2025.2.13 | Medium |
| 19 | Global mutable `obj_list` scratch state in 2 script-finder tools ✅ Fixed v2025.2.13 | Low |
| 20 | Wrong logger (`getLogger()` vs `getLogger("Plugin")`) in `indigo_inventory.py` ✅ Fixed v2025.2.13 | Low |
| 21 | `indigo_inventory.py` can crash on an empty database ✅ Fixed v2025.2.13 | Low |
| 22 | Misleading "POSIX timestamp" validation message ✅ Fixed v2025.2.13 | Low |
| 23 | Vestigial unused `stop_event` flag ✅ Fixed v2025.2.13 | Low |
| 24 | Column-width miscalculation in `device_inventory.py` ✅ Fixed v2025.2.13 | Low |
| 25 | Confusing f-string/%-format mix in a log call ✅ Fixed v2025.2.13 | Low |
| 26 | Dead trailing `<Field type="separator">` in Devices.xml ✅ Fixed v2025.2.13 | Low |
| 27 | Offline-trigger device picker not filtered to ping devices ✅ Fixed v2025.2.13 | Low |
| 27b | Stray/dead `method` attribute on a `<Field>` in MenuItems.xml ✅ Fixed v2025.2.13 | Low |
| 27c | `error_inventory.py` reports accumulate on disk with no retention ✅ Fixed v2025.2.13 | Low |
| 27d | README badges stale vs. actual shipped version/API ⚠️ Partially fixed v2025.2.13 (Indigo badge only) | Low |
| 27e | `_to_do_list.md` is a placeholder, not a real backlog ⬜ No fix needed (user's choice) | Low |

**Test suite:** see "Test suite observations" above for coverage gaps (near-total
lack of negative-path testing, report-content assertions that only check HTTP
status, and a few minor flakiness/isolation risks) — not counted in this table
since they're process observations, not code defects.
