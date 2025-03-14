"""
Print a list of running plugins to the Indigo events log

The running_plugins method prints a table of Indigo plugins that are currently enabled. It includes system and other
information that is useful for troubleshooting purposes.

Display the uid, pid, parent pid, recent CPU usage, process start time, controlling tty, elapsed CPU usage, and the
associated command.  If the -u option is also used, display the username rather than the numeric uid.  When -o or -O is
used to add to the display following -f, the command field is not truncated as severely as it is in other formats.

:return:
"""
import logging
import subprocess
import indigo  # noqa

LOGGER = logging.getLogger("Plugin")


def __init__():
    pass


def show_running_plugins(no_log: bool = False) -> None:
    """
    Generate a list of running plugins and output it to the Indigo Events log

    :param bool no_log: If True, no output is logged.
    :return:
    """
    report = ""
    with subprocess.Popen(
            "/bin/ps -ef | grep 'MacOS/IndigoPluginHost' | grep -v grep",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE) as proc:
        response = proc.communicate()[0]
        response = response.decode('utf-8')

        # Build the report
        report += f"{' Running Plugins (/bin/ps -ef) ':{'='}^225}\n"
        report += (f"  uid - pid - parent pid - recent CPU usage - process start time - controlling tty - elapsed CPU "
                   f"usage - associated command\n")
        report += "=" * 225 + "\n"
        report += f"{response}"
        report += "=" * 225 + "\n"

    if not no_log:

        # We write to `indigo.server.log` to ensure that the output is visible regardless of the plugin's current
        # logging level.
        indigo.server.log(f"\n{report}")
