from scripts.wiki import *      # functions that we run tests on
from scripts.docker_adapter import *
from scripts.tree import *
from scripts.fs import *

from unittest.mock import MagicMock, patch
import unittest
import pytest

class TestWiki(unittest.TestCase):
    # Setup
    @classmethod
    def setUpClass(self):
        self.test_node = Node(
            image_name='ucsdets/datahub-docker-stacks',
            image_tag='pushtest',
            filepath='tests',
            children=[],
            rebuild=False,
            image_built=False,
            build_args={},
            integration_tests=False,
            dockerfile='test.Dockerfile',
            info_cmds=['PY_VER', 'CONDA_INFO', 'CONDA_LIST']
        )
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
            }
        }
        self.sample_output = "sample_output"


    ###### test execution code ######
    def run_run_outputs(self):
        # for testing run_outputs()
        mock_run_command = MagicMock(return_value=("sample_output", True))


        # run_simple_command() HAS BEEN IMPORTED INTO wiki.py!!!
        @patch('scripts.wiki.run_simple_command', mock_run_command)
        def run_test():
            run_outputs(self.test_node, self.all_info_cmds)

        run_test()

        return mock_run_command

        
    def run_write_reports(self):
        output_list = [
            dict(description='Python Version', output=self.sample_output),
            dict(description='Conda Info', output=self.sample_output),
            dict(description='Conda Packages', output=self.sample_output)
        ]
        mock_run_outputs = MagicMock(return_value=output_list)
        mock_markdown_table = MagicMock(return_value="Table Placeholder")

        @patch('scripts.wiki.run_outputs', mock_run_outputs)
        @patch('scripts.wiki.get_layers_md_table', mock_markdown_table)
        def run_test():
            write_report(
                self.test_node, 
                docker.from_env().images.get(self.test_node.full_image_name), 
                self.all_info_cmds
            )

        run_test()

        return (mock_run_outputs, mock_markdown_table)
    

    ###### actual tests ######

    # @pytest.mark.skip(reason="MagicMock failed to mock scripts.docker_adapter.run_simple_command")
    def test_run_outputs(self):
        
        mock_run_command = self.run_run_outputs()
        
        expected = [
            dict(description='Python Version', output=self.sample_output),
            dict(description='Conda Info', output=self.sample_output),
            dict(description='Conda Packages', output=self.sample_output)
        ]
        # assert result == expected, result
        assert mock_run_command.call_count == 3, mock_run_command.call_count
        

    def test_write_reports(self):
        mock_run_outputs, mock_markdown_table = self.run_write_reports()
        assert mock_run_outputs.call_count == 1, mock_run_outputs.call_count
        assert mock_markdown_table.call_count == 1, mock_markdown_table.call_count


    def test_update_Home(self):
        # trick to make this test repeatable:
        # keep a clean Home.md and rename it "Home_original.md"
        with open(path.join('wiki', 'Home_original.md'), 'r') as f:
            doc_str = f.read()
        with open(path.join('wiki', 'Home.md'), 'w') as f:
            f.write(doc_str)

        images_full_names = [f"test_image_{i}:test_tag" for i in range(1, 5)]
        git_short_hash = "TestCommit"
        success = update_Home(images_full_names, git_short_hash)
        assert success
