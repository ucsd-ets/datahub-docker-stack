from scripts.docker_unit import *
import pytest
from unittest.mock import MagicMock


@pytest.fixture()
def setup_container_facade_for_testing():
    # setup fake buildinforetrieval
    mock_build_info = BuildInfo(
        images_changed=['im1', 'im2'],
        git_suffix='mysuffix'
    )

    get_build_info_from_filesystem = MagicMock(return_value=BuildInfo)
    build_retrieval = BuildInfoRetrieval(retrieval_func=get_build_info_from_filesystem)

    store_images_on_filesystem = MagicMock()
    build_units = MagicMock()
    container_test = MagicMock()
    container_push = MagicMock()
    container_delete = MagicMock()

    build_info_storage = BuildInfoStorage(images_built_func=store_images_on_filesystem)
    container_builder = ContainerBuilder(container_builder_func=build_units)
    container_tester = ContainerTester(container_tester_func=container_test)
    container_pusher = ContainerPusher(container_pusher_func=container_push)
    container_deleter = ContainerDeleter(container_deleter_func=container_delete)

    container_facade = ContainerFacade(
        build_retrieval,
        container_builder,
        container_tester,
        container_pusher,
        container_deleter,
        build_info_storage
    )

def test_container_facade_build_container():
    pass

# def test_container_facade_container_test():
#     get_build_info_from_filesystem = MagicMock()
#     store_images_on_filesystem = MagicMock()
#     build_units = MagicMock()
#     container_test = MagicMock()
    
#     build_retrieval = BuildInfoRetrieval(retrieval_func=get_build_info_from_filesystem)
#     build_info_storage = BuildInfoStorage(images_built_func=store_images_on_filesystem)
#     container_builder = ContainerBuilder(container_builder_func=build_units)
#     container_tester = ContainerTester(container_tester_func=container_test)
    

    
#     container_pusher = ContainerPusher
    
#     container_facade = ContainerFacade(
#         build_retrieval,
#         container_builder,
#         container_tester,
#         build_info_storage
#     )

#     stack_dir = '/dir'
#     images_built = ['fakeimages']
#     container_facade.container_test(stack_dir, images_built)
#     container_test.assert_called_with(stack_dir, images_built)
    


