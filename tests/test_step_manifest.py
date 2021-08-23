import pytest
import os
import json

from scripts.utils import store_var, read_var

HOMEPAGE_STR = """
Welcome to the datahub-docker-stacks wiki!


| Commit | Image | Manifest |
|--------|-------|----------|
"""


@pytest.fixture(scope='function')
def prep_wiki(root_dir):
    # prep 'wiki' under root; normally cloned in prod
    wiki_path = os.path.join(root_dir, 'wiki')
    if not os.path.exists(wiki_path):
        os.mkdir(wiki_path)

    # fill wiki home page with empty table
    homepage_path = os.path.join(wiki_path, 'Home.md')
    with open(homepage_path, 'w') as f:
        f.write(HOMEPAGE_STR)

    # Set github env and yield back for tests
    os.environ['GITHUB_REPOSITORY'] = 'github_user/repo_name'
    yield
    del os.environ['GITHUB_REPOSITORY']


@pytest.fixture(scope='function')
def prep_img_dep(root_dir, deps_table):
    dep_json_path = os.path.join(root_dir, 'artifacts', 'image-dependency.json')
    with open(dep_json_path, 'w') as f:
        json.dump(deps_table, f)
    return


class TestStepManifest():
    """Integration test for doit task `manifest`"""

    @pytest.mark.parametrize(
        "stack_dir,deps_table,imgs_built",
        [
            (
                "tests/data/stack_0", 
                {
                    "fakeuser/branch:latest": "fakeuser/base:latest",
                    "fakeuser/leaf:latest": "fakeuser/branch:latest"
                },
                ['fakeuser/base:latest', 'fakeuser/branch:latest', 'fakeuser/leaf:latest']
            ),
        ],
    )
    def test_integration(
        self, doit_handler, root_dir, stack_dir, prep_wiki, prep_img_dep,
        deps_table, imgs_built
    ):
        store_var('IMAGES_BUILT', imgs_built)
        store_var('GIT_HASH_SHORT', '1a2b3c')

        assert doit_handler.run(['-s', 'manifest', '--stack_dir', stack_dir]) == 0

        manifests_path = os.path.join(root_dir, 'manifests')
        assert len(os.listdir(manifests_path)) - 1 == len(imgs_built)  # exclude ".empty"
