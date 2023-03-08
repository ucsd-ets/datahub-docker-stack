# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.


def test_secured_server(container, http_client):
    try:
        """Notebook server should eventually request user login."""
        container.run()
        resp = http_client.get("http://localhost:8888")
        resp.raise_for_status()
        assert "login_submit" in resp.text, "User login not requested"
    except Exception as e:
        print(e)
        import docker
        d = docker.from_env()
        print(f"**** Docker images {d.images.list()} ***")
        print(f"**** Docker containers {d.containers.list()} ***")
        raise e
