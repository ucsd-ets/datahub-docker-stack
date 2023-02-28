from scripts.v2.tester import *
from scripts.v2.tree import *
from unittest.mock import MagicMock


def test_build_and_test_tree():
    test_case = Node('root', '', [
        Node('child1', '', [], {}, rebuild=True),
        Node('child2', '', [], {},  rebuild=True),
        Node('child3', '', [], {}, rebuild=True),
        Node('child4', '', [], {}, rebuild=True)
    ], {}, rebuild=True)

    mock_docker_driver = MagicMock()
    mock_docker_driver.build_image = MagicMock()
    mock_docker_driver.push_image = MagicMock()


    build_and_test_tree(test_case, mock_docker_driver)

    mock_docker_driver.build_image.call_count == 5
    mock_docker_driver.push_image == 5
