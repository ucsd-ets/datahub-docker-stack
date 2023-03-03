from scripts.v2.runner import *
from scripts.v2.tree import *
from unittest.mock import MagicMock
import unittest
import pytest


class TestRunner(unittest.TestCase):
    def run_build_and_test_containers(self, root: Node):
        mock_build = MagicMock(return_value=(True, 'myreport'))
        mock_login = MagicMock()
        mock_push = MagicMock()
        mock_tester = MagicMock(return_value=pytest.ExitCode.OK)

        build_and_test_containers(
            root=root,
            username='fake',
            password='fakepw',
            tag_prefix='2039',
            build=mock_build,
            push=mock_push,
            login=mock_login,
            test_runner=mock_tester)

        return (
            mock_login, mock_build, mock_push, mock_tester
        )

    def test_get_basic_tests(self):
        res = get_basic_test_locations(self.test_case.children[0])
        should_be = ['images/tests_common', 'images/image1']
        assert res == should_be

        # filepath should be there
        with self.assertRaises(RunnerError):
            get_basic_test_locations(self.test_case)

    def test_build_all(self):
        c1 = Node(
            image_name='datascience-notebook',
            git_suffix='test',
            filepath='images'
        )
        c2 = Node(
            image_name='scipy-ml-notebook',
            git_suffix='test',
            filepath='images',
            integration_tests=True
        )
        c3 = Node(
            image_name='rstudio-notebook',
            git_suffix='test',
            filepath='images'
        )
        root = Node(
            image_name='datahub-base-notebook',
            git_suffix='test',
            filepath='images',
            children=[
                c1, c2, c3
            ],
            rebuild=True
        )

        login, build, push, tester = self.run_build_and_test_containers(root)

        login.assert_called_with('fake', 'fakepw')
        imgs_looped_through = ['datahub-base-notebook', 'datascience-notebook',
                                'scipy-ml-notebook', 'rstudio-notebook']
        images_built = [arg.args[0].image_name for arg in build.call_args_list]
        assert images_built == imgs_looped_through, images_built

        images_pushed = [arg.args[0].image_name for arg in push.call_args_list]
        assert images_pushed == imgs_looped_through, images_pushed

        # single integration test + 4 images basic tested
        assert tester.call_count == 5, tester.call_count

    def test_build_some(self):
        c1 = Node(
            image_name='datascience-notebook',
            git_suffix='test',
            filepath='images'
        )
        c2 = Node(
            image_name='scipy-ml-notebook',
            git_suffix='test',
            filepath='images',
            integration_tests=True
        )
        c3 = Node(
            image_name='rstudio-notebook',
            git_suffix='test',
            filepath='images',
            rebuild=True
        )
        root = Node(
            image_name='datahub-base-notebook',
            git_suffix='test',
            filepath='images',
            children=[
                c1, c2, c3
            ],
            rebuild=False
        )

        login, build, push, tester = self.run_build_and_test_containers(root)

        login.assert_called_with('fake', 'fakepw')
        imgs_looped_through = ['rstudio-notebook']
        images_built = [arg.args[0].image_name for arg in build.call_args_list]
        assert images_built == imgs_looped_through, images_built

        images_pushed = [arg.args[0].image_name for arg in push.call_args_list]
        assert images_pushed == imgs_looped_through, images_pushed

        # single basic test
        assert tester.call_count == 1, tester.call_count
    
    def test_build_none(self):
        c1 = Node(
            image_name='datascience-notebook',
            git_suffix='test',
            filepath='images',
            rebuild=False
        )
        c2 = Node(
            image_name='scipy-ml-notebook',
            git_suffix='test',
            filepath='images',
            integration_tests=True,
            rebuild=False
        )
        c3 = Node(
            image_name='rstudio-notebook',
            git_suffix='test',
            filepath='images',
            rebuild=False
        )
        root = Node(
            image_name='datahub-base-notebook',
            git_suffix='test',
            filepath='images',
            children=[
                c1, c2, c3
            ],
            rebuild=False
        )
        login, build, push, tester = self.run_build_and_test_containers(root)
        login.assert_called_with('fake', 'fakepw')
        assert build.call_count == 0
        assert push.call_count == 0
        assert tester.call_count == 0