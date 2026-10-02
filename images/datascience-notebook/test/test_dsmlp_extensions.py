import logging

LOGGER = logging.getLogger('datahub_docker_stacks')


def _exec(container, cmd):
    c = container.run(tty=True, command=["start.sh"])
    result = c.exec_run(["bash", "-c", cmd])
    output = result.output.decode("utf-8")
    LOGGER.debug(output)
    return result.exit_code, output


def test_jupyterlab_status_plugin_installed(container):
    """The DSMLP status plugin (cloned from a private repo at build time) shall be
    installed as a Python package and registered as an enabled labextension."""
    code, output = _exec(
        container,
        "python -c 'import importlib.metadata as m; print(m.version(\"dsmlp-jupyterlab-status-plugin\"))'"
        " && jupyter labextension list 2>&1",
    )
    assert code == 0, output
    status_lines = [line for line in output.splitlines() if "status" in line.lower()]
    assert status_lines, f"status plugin not listed by `jupyter labextension list`:\n{output}"
    assert any("enabled" in line and "OK" in line for line in status_lines), output


def test_vscode_status_extension_sources_present(container):
    """The VS Code status extension sources shall be copied to /opt with the
    .git dir (which carried the clone token) stripped and readable by jovyan."""
    code, output = _exec(
        container,
        "test -f /opt/dsmlp-vscode-status/package.json"
        " && test ! -e /opt/dsmlp-vscode-status/.git"
        " && ! find /opt/dsmlp-vscode-status ! -readable | grep -q .",
    )
    assert code == 0, output
