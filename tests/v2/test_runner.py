from scripts.v2.runner import *
from scripts.v2.tree import *
from scripts.v2.fs import *
from scripts.v2.wiki import *
from unittest.mock import MagicMock, patch
import unittest
import pytest


class TestRunner(unittest.TestCase):
    def run_build_and_test_containers(self, root: Node):
        mock_build = MagicMock(return_value=(True, 'myreport'))
        mock_login = MagicMock()
        mock_push = MagicMock(return_value=(True, 'my push'))
        mock_tester = MagicMock(return_value=[pytest.ExitCode.OK, ""])
        mock_store = MagicMock(return_value=True)
        mock_wiki = MagicMock()
        mock_prune = MagicMock(resp=100)


        self.all_info_cmds = {
            'PY_VER': {
                'description': 'Python Version',
                'command': 'python --version'
            },
            'CONDA_INFO': {
                'description': 'Conda Info',
                'command': 'conda info'
            },
            'CONDA_LIST': {
                'description': 'Conda Packages',
                'command': 'conda list'
            },
        }

        @patch('scripts.v2.docker_adapter.build', mock_build)
        @patch('scripts.v2.runner.run_tests', mock_tester)
        @patch('scripts.v2.docker_adapter.login', mock_login)
        @patch('scripts.v2.docker_adapter.push', mock_push)
        @patch('scripts.v2.fs.store', mock_store)
        @patch('scripts.v2.wiki', mock_wiki)
        @patch('scripts.v2.docker_adapter.prune', mock_prune)
        def run_test():
            build_and_test_containers(root, 'fake', 'fakepw', 'test', self.all_info_cmds)

        run_test()

        return (
            mock_login, mock_build, mock_push, mock_tester, mock_store, mock_wiki, mock_prune
        )
    
    def test_build_all(self):
        c1 = Node(
            image_name='datascience-notebook',
            filepath='images'
        )
        c2 = Node(
            image_name='scipy-ml-notebook',
            filepath='images',
            integration_tests=True
        )
        c3 = Node(
            image_name='rstudio-notebook',
            filepath='images'
        )
        root = Node(
            image_name='datahub-base-notebook',
            filepath='images',
            git_suffix='test',
            children=[
                c1, c2, c3
            ],
            rebuild=True
        )

        mock_login, mock_build, mock_push, mock_tester, mock_store, mock_wiki, mock_prune \
            = self.run_build_and_test_containers(root)
        # build_and_test_containers(root, 'fake', 'fakepw', 'test')

        mock_login.assert_called_with('fake', 'fakepw')

        imgs_looped_through = ['datahub-base-notebook', 'datascience-notebook',
                                'scipy-ml-notebook', 'rstudio-notebook']

        images_built = [arg.args[0].image_name for arg in mock_build.call_args_list]
        assert images_built == imgs_looped_through, images_built

        images_pushed = [arg.args[0].image_name for arg in mock_push.call_args_list]
        assert images_pushed == imgs_looped_through, images_pushed

        # # single integration test + 4 images basic tested
        assert mock_tester.call_count == 5, mock_tester.call_count

        # a build log file, test log file, and a yaml file per image
        assert mock_store.call_count == 12, mock_store.call_count

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

        mock_login, mock_build, mock_push, mock_tester, mock_store, mock_wiki, mock_prune \
            = self.run_build_and_test_containers(root)
        mock_login.assert_called_with('fake', 'fakepw')
        imgs_looped_through = ['rstudio-notebook']
        
        images_built = [arg.args[0].image_name for arg in mock_build.call_args_list]
        assert images_built == imgs_looped_through, images_built

        images_pushed = [arg.args[0].image_name for arg in mock_push.call_args_list]
        assert images_pushed == imgs_looped_through, images_pushed

        # single basic test
        assert mock_tester.call_count == 1, mock_tester.call_count
        # 4 yamls, 1 build log file & 1 test log file for actually built image
        assert mock_store.call_count == 6, mock_store.call_count
    
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
        login, build, push, tester, store, wiki, prune = self.run_build_and_test_containers(root)
        login.assert_called_with('fake', 'fakepw')
        assert build.call_count == 0
        assert push.call_count == 0
        assert tester.call_count == 0
        assert wiki.call_count == 0
        assert prune.call_count == 0

        should_be = [
            Result(success=True, full_image_name='datahub-base-notebook:test-test', container_details={'image_built': False}),
            Result(success=True, full_image_name='datascience-notebook:test-test', container_details={'image_built': False}),
            Result(success=True, full_image_name='scipy-ml-notebook:test-test', container_details={'image_built': False}),
            Result(success=True, full_image_name='rstudio-notebook:test-test', container_details={'image_built': False})
        ]
        should_be_filepaths = [r.safe_full_image_name + '.yaml' for r in should_be]
        got_filepaths = [arg.args[0] for arg in store.call_args_list]

        assert got_filepaths == should_be_filepaths, got_filepaths
