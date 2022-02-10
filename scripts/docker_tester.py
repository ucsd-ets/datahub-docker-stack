from os import path, environ
import pytest

from scripts.utils import get_specs, read_var, store_var
from model.spec import BuilderSpec


def _tests_collector(stack_dir, IMAGES_BUILT):
    specs = get_specs(path.join(stack_dir, 'spec.yml'))
    build_spec = BuilderSpec(specs)

    fulltag_to_key = {}
    for image_to_test in IMAGES_BUILT:
        # hacky solution for now
        image_key = next(filter(lambda key: key in image_to_test, build_spec.imageDefs.keys()))
        fulltag_to_key[image_to_test] = image_key

    # Process test folders including parent nodes
    test_params = {}
    for image_to_test in IMAGES_BUILT:
        test_dirs = []
        image_key = fulltag_to_key[image_to_test]
        _f_image_test_dir = lambda key: path.join(stack_dir, key, 'test')

        while True:
            if path.isdir(_f_image_test_dir(image_key)):
               test_dirs.append(_f_image_test_dir(image_key))
            if 'depend_on' not in specs['images'][image_key]:
                break
            image_key = specs['images'][image_key]['depend_on']

        common_test_dir = path.join(stack_dir, 'tests_common')
        if path.exists(common_test_dir):
            test_dirs.insert(0, common_test_dir)
        test_params[image_to_test] = test_dirs
    return test_params


def run_test(stack_dir):
    IMAGES_BUILT = 'ucsdets/scipy-ml-notebook:2021.3-stable' #read_var('IMAGES_BUILT')
    test_params = _tests_collector(stack_dir, IMAGES_BUILT)

    IMAGES_TEST_PASSED = []
    IMAGES_TEST_ERROR = []

    for image_tag, test_dirs in test_params.items():
        print(f'*** Testing {image_tag} ***')
        environ['TEST_IMAGE'] = image_tag
        exit_code = pytest.main([
            '-x',       # exit instantly on first error or failed test
            *test_dirs  # test dirs
        ])

        if exit_code is pytest.ExitCode.OK:
            IMAGES_TEST_PASSED.append(image_tag)
        else:
            IMAGES_TEST_ERROR.append(image_tag)
            
        store_var('IMAGES_TEST_PASSED', IMAGES_TEST_PASSED)
        store_var('IMAGES_TEST_ERROR', IMAGES_TEST_ERROR)

    assert len(IMAGES_TEST_ERROR) == 0, f"Images did not pass tests: {IMAGES_TEST_ERROR}"
