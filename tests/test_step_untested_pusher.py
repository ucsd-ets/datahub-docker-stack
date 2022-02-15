import pytest
from unittest.mock import MagicMock

from scripts.utils import store_var, read_var
from scripts.docker_untested_pusher import push_images


@pytest.fixture(scope='function')
def mock_client():
    client = MagicMock()
    client.images.push = MagicMock(return_value={})
    return client

class TestUntestedPusher():
    @pytest.mark.parametrize(
        "stack_dir,pairs,externally_tested_images",
        [
            ("tests/data/stack_0",[('some','some:tag'),('invalid','invalid'),('image','images:tag')],[]),
            ("tests/data/stack_0",[('some','some:tag'),('invalid','invalid'),('image','images:tag')],['fake1','fake']),
            ("tests/data/stack_0",[('valid','valid:hash'),('valid2','valid2'),('invalid','invalid:hash')],['valid','valid2']),
        ],
    )
    def test_push_images(self,root_dir, mock_client,pairs,externally_tested_images):
        push_images(mock_client,pairs,externally_tested_images)
        
        calls = 0
        imgs_expected=[]
        for image,full_tag in pairs:
            if image in externally_tested_images:
                calls +=0
                imgs_expected.append(full_tag)

        assert mock_client.images.push.call_count == calls
        imgs_pushed = read_var('IMAGES_UNTESTED_PUSHED')
        assert imgs_pushed == imgs_expected