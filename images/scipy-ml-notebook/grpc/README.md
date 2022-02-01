# gpu-tester

## Development

Open Dockerfile inside a vscode container. That will put you at path `workspaces/datahub-docker-stack/images/scipy-ml-notebook/grpc`

Install the app with `pip install -e .`

Run the tests with `pytest --noconftest test/unit`

For the integration test `pytest --noconftest test/integration_tests`
