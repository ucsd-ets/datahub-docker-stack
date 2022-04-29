import logging
import pytest

LOGGER = logging.getLogger(__name__)
    
    
@pytest.mark.parametrize(
    "expected_server",
    [
        ("notebook"),
    ],
)
def test_jupyter_lab_exists(container, http_client, expected_server):
    """Check that the jupyter lab endpoint exists"""
    LOGGER.info(f"Checking that jupyter lab endpoint exists when using jupyter {expected_server}")
    c = container.run(
        tty=True,
        command=["start-notebook.sh"],
    )
    resp = http_client.get("http://localhost:8888/lab")
    logs = c.logs(stdout=True).decode("utf-8")
    LOGGER.debug(logs)
    assert resp.status_code == 200, "Jupyter lab is not running"
    assert (
        f"Executing the command: jupyter {expected_server}" in logs
    ), f"Not the expected command (jupyter {expected_server}) was launched"

@pytest.mark.parametrize(
    "expected_server",
    [
        ("notebook"),
    ],
)
def test_jupyter_notebook_exists(container, http_client, expected_server):
    """Check that the jupyter notebook endpoint exists"""
    LOGGER.info(f"Checking that jupyter notebook endpoint exists when using jupyter {expected_server}")
    c = container.run(
        tty=True,
        command=["start-notebook.sh"],
    )
    resp = http_client.get("http://localhost:8888/tree")
    logs = c.logs(stdout=True).decode("utf-8")
    LOGGER.debug(logs)
    assert resp.status_code == 200, "Jupyter notebook(/tree) is not running "
    assert (
        f"Executing the command: jupyter {expected_server}" in logs
    ), f"Not the expected command (jupyter {expected_server}) was launched"