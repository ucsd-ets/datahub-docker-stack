import pytest
import os
import shutil
import docker

import dodo
from doit.cmd_base import ModuleTaskLoader
from doit.doit_cmd import DoitMain


@pytest.fixture(scope="session")
def docker_client():
    """Docker client configured based on the host environment"""
    return docker.from_env()


@pytest.fixture
def doit_handler(scope="session"):
    handler = DoitMain(ModuleTaskLoader(dodo))
    return handler


@pytest.fixture(scope='function')
def root_dir(tmp_path, doit_handler, stack_dir):
    """
    Change current working directory to temp path and change it back after. 
    Also copies the test stack_dir into temp path for easy access
    """
    cwd = os.getcwd()
    shutil.copytree(stack_dir, tmp_path / stack_dir)
    os.chdir(tmp_path)
    doit_handler.run(['prep'])
    # assert tmp_path == 0
    yield tmp_path
    os.chdir(cwd)
