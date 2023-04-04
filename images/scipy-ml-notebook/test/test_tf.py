# Adapted from datascience-notebook/test/test_notebooks.py
import logging

import pytest
import os

LOGGER = logging.getLogger('datahub_docker_stacks')
THIS_DIR = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "test_file",
    ["test_tf"],
)
def test_tf(container, test_file):
    """ test_tf.ipynb checks
    1. tensorboard extention can be loaded.
    2. tf version and tf.keras version match
    """
    host_data_dir = os.path.join(THIS_DIR, "data")
    cont_data_dir = "/home/jovyan/data"
    output_dir = "/tmp"
    timeout_sec = 600
    LOGGER.info(f"Test that {test_file} notebook can be executed ...")
    command = (
        "jupyter nbconvert --to markdown "
        + f"--ExecutePreprocessor.timeout={timeout_sec} "
        + f"--output-dir {output_dir} "
        + f"--execute {cont_data_dir}/{test_file}.ipynb"
    )

    """ container.ports.update({
        "5132/tcp": 5132
    }) """

    c = container.run(
        volumes={host_data_dir: {"bind": cont_data_dir, "mode": "ro"}},
        tty=True,
        command=["start.sh", "bash", "-c", command],
    )

    rv = c.wait(timeout=timeout_sec//10 + 10)
    logs = c.logs(stdout=True).decode("utf-8")
    LOGGER.debug(logs)
    print(logs)
    assert rv == 0 or rv["StatusCode"] == 0, f"Command {command} failed"