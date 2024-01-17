import logging
import subprocess
import sys

from importlib.util import find_spec
from importlib import import_module

logging.basicConfig(format="\033[1m\033[31mVoicesynth - %(asctime)s - %(message)s\033[0m", datefmt="%Y-%b-%d %H:%M:%S",
                    level=logging.INFO)


def install(package: str, output: bool = True, auto_upgrade: bool = True, configure: bool = True):
    """
    Function for installing specified packages inside a python script

    :param package: name of the package to install from PyPi
    :param output: surpasses console output if set False
    :param auto_upgrade: upgrades the package to the last available version if the package is already installed
    :param configure: checks whether the package was imported successfully and returns it if yes

    :return: Returns a module if installation was successful and tests were run, True if installation is supposed to be successful, False otherwise
    """
    packages_installed = installed(package)
    # running a commands using the same environment
    if not (packages_installed and not auto_upgrade):
        subprocess.run(
            args=[sys.executable, "-m", "pip", "install", "-U", package],
            stdout=subprocess.DEVNULL if not output else None,  # DEVNULL surpasses console output
            stderr=subprocess.STDOUT
        )
    try:
        if configure:
            import_module(package)
            logging.info(f"Tests for {package} installation succeeded")
        # checking whether the package was installed and importing it into the code
        else:
            logging.info(f"Tests for {package} were not implemented, install confirmation can be false")
        if not (packages_installed and not auto_upgrade):
            logging.info(
                f"{package} {'installation succeeded' if not packages_installed else 'was already installed, updated successfully'}")
        else:
            logging.info(f"{package} is already installed")
        if configure:
            return import_module(package)  # installation or upgrade succeeded
        return True
    except ModuleNotFoundError:
        logging.info(f"{package} installation failed")
        return False  # installation failed


def installed(name: str) -> bool:
    """
    A function for checking if the specified package is installed in venv
    :param name: name of the package
    :return: True if package is installed False otherwise
    """
    return False if not find_spec(name) else True
