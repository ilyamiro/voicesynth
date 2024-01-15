import subprocess
import sys

from importlib.util import find_spec


def redprint(text, **kwargs):
    print(f"\033[1m\033[31m{text}\033[0m", **kwargs)


def install(*args: str, output: bool = True, auto_upgrade: bool = True) -> None:
    """
    Function for installing specified packages inside a python script

    :param package: name of the package to install from PyPi
    :param output: surpasses console output if set False
    :param auto_upgrade: upgrades the package to the last available version if the package is already installed
    """
    package_installed = installed(package)
    # running a commands using the same environment
    if not (package_installed and not auto_upgrade):
        subprocess.run(
            args=[sys.executable, "-m", "pip", "install", "-U", *args],
            stdout=subprocess.DEVNULL if not output else None,  # DEVNULL surpasses console output
            stderr=subprocess.STDOUT
        )
    try:
        globals()[package] = __import__(
            package)  # checking whether the package was installed and importing it into the code
        if not (package_installed and not auto_upgrade):
            redprint(
                f"{package} {'installation succeeded' if not package_installed else 'was already installed, updated successfully'}")
        else:
            redprint(f"{package} is already installed")
    except ModuleNotFoundError:
        redprint(f"{package} installation failed")


def installed(name: str) -> bool:
    """
    A function for checking if the specified package is installed in venv
    :param name: name of the package
    :return: True if package is installed False otherwise
    """
    return False if not find_spec(name) else True


