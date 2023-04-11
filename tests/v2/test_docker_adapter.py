"""WARNING, be careful with these tests as your token may time out. Dockerhub puts a limit on how many
requests you can make
"""

# our scripts to be tested
from scripts import docker_adapter as internal_docker
from scripts.tree import Node

from unittest.mock import MagicMock, patch
import unittest
import pytest

import docker
import os
import json

# store your test (dummy) account info there. Token is usually empty string
with open('tests/cred.json', 'r') as f:
    data = json.load(f)
username = data["DOCKERHUB_USERNAME"]
password = data["DOCKERHUB_TOKEN"]

class TestDocker(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.docker = docker.from_env()
        internal_docker.set_docker_client(self.docker)
        self.test_node = Node(
            image_name='ucsdets/datahub-docker-stacks',
            image_tag='pushtest',
            filepath='tests/v2',
            children=[],
            rebuild=False,
            image_built=False,
            build_args={},
            integration_tests=False,
            dockerfile='test.Dockerfile'
        )
        self.stable_fullnames = [f"image_{i}:2099.1-stable" for i in range(1,5)]
        self.orig_images = [f"image_{i}:2099.1-deadbeef" for i in range(1,5)]
        self.tag_replace = '2099.1-stable'
    
    def test_build(self):
        resp, report = internal_docker.build(self.test_node)
        assert resp, resp
        assert len(report) > 1, report

        # calling it twice doesn't result in failure
        resp, report = internal_docker.build(self.test_node)
        assert resp, resp
        assert len(report) > 1, report
    
    def test_login(self):

        # don't test not login as this will cause issues
        assert internal_docker.login(username, password)

    def test_push(self):
        internal_docker.login(username, password)
        resp, report = internal_docker.push(self.test_node)
        assert 'docker.io' in report, report
        assert resp, resp

    def test_prune(self):
        resp = internal_docker.prune('ucsdets/datahub-docker-stacks:pushtest')
        assert resp >= 0, resp

    ###### test execution code ######
    def _prepull_images(self):
        # to mock:
        # 1. __docker_client.images.pull()
        # 2. __docker_client.close()

        mock_pull = MagicMock()
        mock_images = MagicMock(pull=mock_pull)
        mock_close = MagicMock()
        
        @patch('scripts.docker_adapter.__docker_client', images=mock_images, close=mock_close)
        def run_test(pos_arg):
            # NOTE: need pos_arg when we @patch with keyword-arg
            return internal_docker.prepull_images(self.orig_images)

        result = run_test()
        return (result, mock_pull, mock_close)
    
    def _tag_stable(self):
        # to mock:
        # 1. __docker_client.images.get()
        # 2. img_obj.tag()
        # 3. __docker_client.close()

        # NOTE: need to mock an Image obj returned by images.get()
        #       and this mock_img_obj should be able to call tag()
        mock_tag = MagicMock()
        mock_img_obj = MagicMock(tag=mock_tag)
        mock_get = MagicMock(return_value=mock_img_obj)
        mock_images = MagicMock(get=mock_get)
        mock_close = MagicMock()

        @patch('scripts.docker_adapter.__docker_client', images=mock_images, close=mock_close)
        def run_test(pos_arg):
            return internal_docker.tag_stable(self.orig_images[0], self.tag_replace)

        stable_name, result = run_test()
        return (stable_name, result, mock_get, mock_tag, mock_close)

    def _push_stable_image(self):
        # to mock:
        # 1. __docker_client.images.get()
        # 2. __docker_client.images.push()
        # 3. __docker_client.close()
        # 4. store_var()

        mock_get = MagicMock()
        mock_push = MagicMock()
        mock_close = MagicMock()
        mock_store_var = MagicMock()

        # NOTE: need an extra MagicMock obj to mock docker submodule (images)
        mock_images = MagicMock(get=mock_get, push=mock_push)
        @patch('scripts.docker_adapter.__docker_client', images=mock_images, close=mock_close)
        @patch('scripts.docker_adapter.store_var', mock_store_var)
        def run_test(pos_arg):
            # NOTE: need pos_arg when we @patch with keyword-arg
            return internal_docker.push_stable_images(self.stable_fullnames)
            
        result = run_test()
        return (result, mock_get, mock_push, mock_close, mock_store_var)

    ###### actual tests ######
    def test_prepull_images(self):
        result, mock_pull, mock_close = self._prepull_images()
        assert result == True, "prepull_images() failed somewhere"
        assert mock_pull.call_count == 4, mock_pull.call_count
        assert mock_close.call_count == 1, mock_close.call_count

    def test_tag_stable(self):
        stable_name, result, mock_get, mock_tag, mock_close = self._tag_stable()
        assert result == True, "prepull_images() failed somewhere"
        assert stable_name == self.stable_fullnames[0], f"Stable name is wrong: {stable_name}"
        assert mock_get.call_count == 1, mock_get.call_count
        assert mock_tag.call_count == 1, mock_tag.call_count
        assert mock_close.call_count == 1, mock_close.call_count

    def test_push_stable_image(self):
        result, mock_get, mock_push, mock_close, mock_store_var = self._push_stable_image()
        assert result == True, "push_stable_image() failed somewhere"
        assert mock_get.call_count == 4, mock_get.call_count
        assert mock_push.call_count == 4, mock_push.call_count
        assert mock_close.call_count == 1, mock_close.call_count
        assert mock_store_var.call_count == 1, mock_store_var.call_count
