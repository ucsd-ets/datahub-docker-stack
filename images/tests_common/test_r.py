import subprocess
import re
import pytest
import subprocess
import logging

from packaging import version

LOGGER = logging.getLogger('datahub_docker_stacks')

from helpers import CondaPackageHelper

# Hardcoded path (TODO: Change to where you copy tests in Docker img)
commonPath = "/opt/manual-tests/"

# List of "fatal" terms from Rscript
errorList = ["Failed", "Fatal", "Error"]

def test_required_r_packages_installed(container):
    # Run Rscript inside of container
    c = container.run(
        tty=True,
        command=["start.sh"],
        ports={'8888/tcp':8899} # key is port inside container; value is local (github runtime) port
    )
    cmd = c.exec_run("sh -c \"Rscript " + commonPath + "test_r_dump_packages.R\"")
    # cmd = c.exec_run(cmd=[
    #     'sh', '-c',
    #     f'"Rscript {commonPath}test_r_dump_packages.R"'
    # ])
    output = cmd.output.decode("utf-8")
    
    c.stop()

    # Make sure result query actually captured libraries
    check_r_errors(output)

    # Lowercase all output
    output = output.lower()

    # Get packages that R itself recognizes
    installed = get_installed_r_packages(container)

    # Shear off r- parts of r packages
    installed = [s.replace("r-", "") for s in installed]

    # Ensure that all packages listed by conda are recognized by R
    for package in installed:
        print(package)
        try:
            assert package in output
        except:
            # Uh oh spaghettio
            raise Exception(
                package + " is not in R's list of installed packages")

    print("All Conda R packages are detected by R")
    c.remove()

# https://docker-py.readthedocs.io/en/stable/containers.html
def get_installed_r_packages(container):
    # Get R packages from conda inside container
    c = container.run(
        tty=True,
        command=["start.sh"],
        ports={'8888/tcp':8897} # key is port inside container; value is local (github runtime) port
    )
    # cmd = c.exec_run("sh -c \"conda list | grep -E 'r-.+'\"")
    cmd = c.exec_run("sh -c \"conda list | grep -E '^r-.*'\"")
    result = cmd.output.decode("utf-8")
    
    c.stop()
    
    # Check exit code
    # TODO: If this does not work, remove. Will not match with R if it fails regardless
    if cmd.exit_code != 0:
        raise RuntimeError(f"Error ({cmd.output[0]}) executing command: {result}")

    # Get newline - r package name
    installed_packages = set(re.findall(
        r"(r-[a-z0-9_]+)", result, re.IGNORECASE))

    c.remove()
    
    return installed_packages

def test_r_func(container):
    # Run basic functions in R, ensure that env is functional
    c = container.run(
        tty=True,
        command=["start.sh"],
        ports={'8888/tcp':8896} # key is port inside container; value is local (github runtime) port
    )
    cmd = c.exec_run("sh -c \"Rscript " + commonPath + "test_r_func.R\"")
    output = cmd.output.decode("utf-8")
    
    c.stop()

    check_r_errors(output)
    
    c.remove()
        
@pytest.mark.skip(reason="Internal method to check R when we run it")
# R does not seem to return bash exit codes.
# This is our workaround for that.
def check_r_errors(strToCheck):
    for error in errorList:
        assert error not in strToCheck
        assert error.lower() not in strToCheck