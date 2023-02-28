"""WARNING, be careful with these tests as your token may time out. Dockerhub puts a limit on how many
requests you can make
"""

from scripts.v2 import docker as internal_docker
from scripts.v2.tree import Node
import unittest
import docker
import os

username = os.environ.get('DOCKERHUB_USERNAME', None)
password = os.environ.get('DOCKERHUB_TOKEN', None)

class TestDocker(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.docker = docker.from_env()
        internal_docker.set_docker_client(self.docker)
        self.test_node = Node(
            image_name='ucsdets/datahub-docker-stacks',
            image_tag='pushtest',
            repo_name='fakerepo',
            filepath='tests/v2',
            children=[],
            rebuild=False,
            image_built=False,
            build_args={},
            integration_tests=False,
            dockerfile='test.Dockerfile'
        )
    
    def test_build(self):
        resp = internal_docker.build(self.test_node)
        assert resp

        # calling it twice doesn't result in failure
        resp = internal_docker.build(self.test_node)
        assert resp
    
    def test_login(self):

        # don't test not login as this will cause issues
        assert internal_docker.login(username, password)


    def test_push(self):
        internal_docker.login(username, password)
        internal_docker.push(self.test_node)
    
