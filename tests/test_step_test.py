import pytest

from scripts.utils import store_var, read_var
from scripts.docker_tester import _tests_collector


class TestStepTest():
    @pytest.mark.parametrize(
        "stack_dir,imgs_built,expected_items",
        [
            (
                "tests/data/stack_2", 
                ['fakeuser/base:latest', 'fakeuser/branch:latest', 'fakeuser/leaf:latest'],
                {
                    'fakeuser/base:latest': [
                        'tests/data/stack_2/tests_common',
                        'tests/data/stack_2/base/test'
                    ],
                    'fakeuser/branch:latest': [
                        'tests/data/stack_2/tests_common',
                        'tests/data/stack_2/branch/test',
                        'tests/data/stack_2/base/test'
                    ],
                    'fakeuser/leaf:latest': [
                        'tests/data/stack_2/tests_common',
                        'tests/data/stack_2/leaf/test',
                        'tests/data/stack_2/branch/test',
                        'tests/data/stack_2/base/test'
                    ]
                }
            ),
        ],
    )
    def test_collection(
        self, root_dir, stack_dir,
        imgs_built, expected_items
    ):
        store_var('IMAGES_BUILT', imgs_built)
        collected = _tests_collector(stack_dir, imgs_built)
        assert collected == expected_items
