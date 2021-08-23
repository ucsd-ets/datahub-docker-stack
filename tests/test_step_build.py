import pytest
import docker

from scripts.utils import store_var, read_var


class TestStepBuild():
    """Integration test for doit task `build`"""

    @pytest.mark.parametrize(
        "stack_dir,imgs_changed,imgs_expected",
        [
            (
                "tests/data/stack_0", ['base'], 
                ['fakeuser/base:latest', 'fakeuser/branch:latest', 'fakeuser/leaf:latest']
            ),
        ],
    )
    def test_integration(
        self, doit_handler, root_dir, stack_dir, docker_client,
        imgs_changed, imgs_expected
    ):
        store_var('IMAGES_CHANGED', imgs_changed)
        # single task execution used for not running dependent tasks
        assert doit_handler.run(['-s', 'build', '--stack_dir', stack_dir]) == 0
        imgs_built = read_var('IMAGES_BUILT')
        assert imgs_built == imgs_expected

        # test each image exists
        for img in imgs_built:
            docker_client.images.get(img)
