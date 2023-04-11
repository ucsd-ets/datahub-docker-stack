from scripts.runner import *
from scripts.tree import *
from scripts.fs import *
from scripts.wiki import *
from unittest.mock import MagicMock, patch
import unittest
import pytest


class TestRunner(unittest.TestCase):
    def run_build_and_test_containers(self, root: Node):
        mock_login = MagicMock()

        # for each node
        mock_build = MagicMock(return_value=(True, 'myreport'))
        mock_tester = MagicMock(return_value=[pytest.ExitCode.OK, ""])  # multiple
        mock_push = MagicMock(return_value=(True, 'my push'))
        _mock_img_obj = MagicMock()
        mock_get = MagicMock(return_value=_mock_img_obj)
        mock_wiki_write_report = MagicMock()
        mock_prune = MagicMock(resp=100)
        mock_store = MagicMock(return_value=True)   # multiple

        mock_wiki_update_Home = MagicMock()
        


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

        @patch('scripts.docker_adapter.build', mock_build)
        @patch('scripts.runner.run_tests', mock_tester)
        @patch('scripts.docker_adapter.login', mock_login)
        @patch('scripts.docker_adapter.push', mock_push)
        @patch('scripts.fs.store', mock_store)
        @patch('scripts.docker_adapter.get_image_obj', mock_get)
        @patch('scripts.wiki.write_report', mock_wiki_write_report)
        @patch('scripts.wiki.update_Home', mock_wiki_update_Home)
        @patch('scripts.docker_adapter.prune', mock_prune)
        def run_test():
            return build_and_test_containers(root, 'fake', 'fakepw', 'test', self.all_info_cmds)

        res = run_test()

        return (
            mock_login, mock_build, mock_tester, mock_push, 
            mock_get, mock_wiki_write_report, 
            mock_prune, mock_store, mock_wiki_update_Home,
            res
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

        (
            mock_login, mock_build, mock_tester, mock_push, 
            mock_get, mock_wiki_write_report, 
            mock_prune, mock_store, mock_wiki_update_Home,
            res
        ) = self.run_build_and_test_containers(root)
        
        assert res, "build_and_test_containers() returns False"

        mock_login.assert_called_with('fake', 'fakepw')

        imgs_looped_through = ['datahub-base-notebook', 'datascience-notebook',
                                'scipy-ml-notebook', 'rstudio-notebook']

        images_built = [arg.args[0].image_name for arg in mock_build.call_args_list]
        assert images_built == imgs_looped_through, images_built

        # single integration test + 4 images basic tested
        assert mock_tester.call_count == 5, mock_tester.call_count

        images_pushed = [arg.args[0].image_name for arg in mock_push.call_args_list]
        assert images_pushed == imgs_looped_through, images_pushed

        images_gotten = [arg.args[0].image_name for arg in mock_get.call_args_list]
        assert images_gotten == imgs_looped_through, images_gotten

        assert mock_wiki_write_report.call_count == 4, mock_wiki_write_report.call_count

        assert mock_prune.call_count == 4, mock_prune.call_count

        # a build log file, test log file, and a yaml file per image
        assert mock_store.call_count == 12, mock_store.call_count

        assert mock_wiki_update_Home.call_count == 1, mock_wiki_update_Home.call_count

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
            # NOTE: with current design using git-hash in tag,
            # root must be rebuilt if any child is rebuilt, 
            # even root itself has no change
            # Thus, we set rebuild=False and expect it to be rebuilt
            rebuild=False
        )

        (
            mock_login, mock_build, mock_tester, mock_push, 
            mock_get, mock_wiki_write_report, 
            mock_prune, mock_store, mock_wiki_update_Home,
            res
        ) = self.run_build_and_test_containers(root)

        assert res, "build_and_test_containers() returns False"

        mock_login.assert_called_with('fake', 'fakepw')
        imgs_looped_through = ['datahub-base-notebook', 'rstudio-notebook']
        
        images_built = [arg.args[0].image_name for arg in mock_build.call_args_list]
        assert images_built == imgs_looped_through, images_built

        # root + 1 child basic test, no integration tests
        assert mock_tester.call_count == 2, mock_tester.call_count

        images_pushed = [arg.args[0].image_name for arg in mock_push.call_args_list]
        assert images_pushed == imgs_looped_through, images_pushed

        images_gotten = [arg.args[0].image_name for arg in mock_get.call_args_list]
        assert images_gotten == imgs_looped_through, images_gotten

        assert mock_wiki_write_report.call_count == 2, mock_wiki_write_report.call_count

        assert mock_prune.call_count == 2, mock_prune.call_count

        # 4 yamls, 2 build log file & 2 test log file for actually built image
        assert mock_store.call_count == 8, mock_store.call_count

        assert mock_wiki_update_Home.call_count == 1, mock_wiki_update_Home.call_count

    
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
        (
            mock_login, mock_build, mock_tester, mock_push, 
            mock_get, mock_wiki_write_report, 
            mock_prune, mock_store, mock_wiki_update_Home,
            res
        ) = self.run_build_and_test_containers(root)

        assert res, "build_and_test_containers() returns False"
        mock_login.assert_called_with('fake', 'fakepw')
        assert mock_build.call_count == 0
        assert mock_tester.call_count == 0
        assert mock_push.call_count == 0
        assert mock_get.call_count == 0
        assert mock_wiki_write_report.call_count == 0
        # no rebuild, thus no prune()
        assert mock_prune.call_count == 0
        # update_Home() check whether any update is needed and will always be called. 
        assert mock_wiki_update_Home.call_count == 1

        should_be = [
            Result(success=True, full_image_name='datahub-base-notebook:test-test', container_details={'image_built': False}),
            Result(success=True, full_image_name='datascience-notebook:test-test', container_details={'image_built': False}),
            Result(success=True, full_image_name='scipy-ml-notebook:test-test', container_details={'image_built': False}),
            Result(success=True, full_image_name='rstudio-notebook:test-test', container_details={'image_built': False})
        ]
        should_be_filepaths = [r.safe_full_image_name + '.yaml' for r in should_be]
        got_filepaths = [arg.args[0] for arg in mock_store.call_args_list]

        assert got_filepaths == should_be_filepaths, got_filepaths
