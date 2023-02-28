from scripts.v2.runner import *
from scripts.v2.tree import *
from scripts.v2 import docker
from unittest.mock import MagicMock
import unittest
import os


test_dockerfile = """
FROM busybox
"""

class TestRunner(unittest.TestCase):
    def setUp(self):
        self.test_case = Node(image_name='root', image_tag='test', rebuild=True, children=[
            Node(image_name='child1', image_tag='test', rebuild=True, filepath='images/image1'),
            Node(image_name='child2', image_tag='test', rebuild=True),
            Node(image_name='child3', image_tag='test', rebuild=True),
            Node(image_name='child4', image_tag='test', rebuild=False),
        ])

    def test_get_basic_tests(self):
        res = get_basic_test_locations(self.test_case.children[0])
        should_be = ['images/tests_common', 'images/image1']
        assert res == should_be

        # filepath should be there
        with self.assertRaises(RunnerError):
            get_basic_test_locations(self.test_case)

    # def test_run_basic_tests(self):
    #     # TODO MARK integration test, this one is long
    #     node = self.test_case.children[0]
    #     node.filepath='images/datahub-base-notebook'
    #     node.image_tag = 'test'

    #     # docker.build(node)

    #     # TODO TEST_IMAGE shouldn't be necessary in future version and instead should
    #     # be passed in somehow

    #     # This is used by tests_common, individual container tests to know which container
    #     # to test
    #     os.environ['TEST_IMAGE'] = node.image_name + ':' + node.image_tag
    #     exit_code = run_basic_tests(node)
    #     assert exit_code.OK == pytest.ExitCode.OK



# def test_build_and_test_tree():
#     test_case = Node('root', '', [
#         Node('child1', '', [], {}, rebuild=True),
#         Node('child2', '', [], {},  rebuild=True),
#         Node('child3', '', [], {}, rebuild=True),
#         Node('child4', '', [], {}, rebuild=True)
#     ], {}, rebuild=True)

#     mock_docker_driver = MagicMock()
#     mock_docker_driver.build_image = MagicMock()
#     mock_docker_driver.push_image = MagicMock()


#     build_and_test_tree(test_case, mock_docker_driver)

#     mock_docker_driver.build_image.call_count == 5
#     mock_docker_driver.push_image == 5

