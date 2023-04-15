import subprocess
import re
import pytest
import subprocess


def get_installed_r_packages():
    command = "conda list | grep -E 'r-.+'"
    result = subprocess.run(command, shell=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        raise RuntimeError(f"Error executing command: {result.stderr}")

    # Get newline - r package name
    installed_packages = set(re.findall(
        r"\n(r-[a-z0-9_]+)", result.stdout, re.IGNORECASE))

    return installed_packages


def test_required_r_packages_installed():
    result = subprocess.run(
        ["Rscript", "dump_r_packages.R"], capture_output=True, text=True)
    output = result.stdout

    # Make sure result query actually captured libraries
    assert "Fatal" not in output

    # Lowercase all output
    output = output.lower()

    installed = get_installed_r_packages()

    # Shear off r- parts of r packages
    installed = [s.replace("r-", "") for s in installed]

    for package in installed:
        print(package)
        try:
            assert package in output
        except:
            # Uh oh spaghettio
            raise Exception(
                package + " is not in R's list of installed packages")

    print("All Conda R packages are detected by R")


def test_r_func():

    # List of "fatal" terms from Rscript
    errorList = ["Failed", "Fatal", "Error"]

    result = subprocess.run(["Rscript", "test_func.R"],
                            capture_output=True, text=True)

    status = False
    for error in errorList:
        assert error not in result.stdout
