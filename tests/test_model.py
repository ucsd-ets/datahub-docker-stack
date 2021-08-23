import pytest
from os import path

from scripts.utils import get_specs
from model.spec import BuilderSpec


# @pytest.fixture
# def stack_spec(stack_dir):
#     specs = get_specs(path.join(stack_dir, 'spec.yml'))
#     yield BuilderSpec(specs)


@pytest.fixture
def stack_spec(spec_fp):
    specs = get_specs(spec_fp)
    yield BuilderSpec(specs)


class TestModelInit:
    """Test all valid stacks are initializable from BuilderSpec()"""
    @pytest.mark.parametrize(
        "spec_fp",
        [
            "tests/data/specs/spec_0.yaml",
            "tests/data/specs/spec_1.yaml",
            "tests/data/specs/spec_2.yaml",
        ],
    )
    def test_init(self, stack_spec, spec_fp):
        assert isinstance(stack_spec, BuilderSpec)


class TestModelStackAll:
    @pytest.mark.parametrize(
        "spec_fp,length",
        [
            ("tests/data/specs/spec_0.yaml", 3),
            ("tests/data/specs/spec_1.yaml", 6),
            ("tests/data/specs/spec_2.yaml", 3),
        ],
    )
    def test_img_length(self, stack_spec, spec_fp, length):
        assert len(stack_spec.imageDefs) == length


    @pytest.mark.parametrize(
        "spec_fp,root",
        [
            ("tests/data/specs/spec_0.yaml", 'base'),
            ("tests/data/specs/spec_1.yaml", 'base'),
            ("tests/data/specs/spec_2.yaml", 'base'),
        ],
    )
    def test_img_root(self, stack_spec, spec_fp, root):
        root = stack_spec.imageDefs[root]
        assert stack_spec.img_root == root


    @pytest.mark.parametrize(
        "spec_fp,img,base_img",
        [
            ('tests/data/specs/spec_0.yaml', 'branch', 'base'),
            ('tests/data/specs/spec_0.yaml', 'leaf', 'branch'),
            ('tests/data/specs/spec_1.yaml', 'branch-A', 'base'),
            ('tests/data/specs/spec_1.yaml', 'branch-B', 'base'),
            ('tests/data/specs/spec_1.yaml', 'leaf-A1', 'branch-A'),
            ('tests/data/specs/spec_1.yaml', 'leaf-B1', 'branch-B'),
            ('tests/data/specs/spec_1.yaml', 'leaf-B1', 'branch-B'),
        ],
    )
    def test_img_depend_on(self, stack_spec, spec_fp, img, base_img):
        img = stack_spec.imageDefs[img]
        base_img = stack_spec.imageDefs[base_img]
        assert img.depend_on is base_img


    @pytest.mark.parametrize(
        "spec_fp,img,dependents",
        [
            ('tests/data/specs/spec_0.yaml', 'base', ['branch']),
            ('tests/data/specs/spec_0.yaml', 'branch', ['leaf']),
            ('tests/data/specs/spec_1.yaml', 'base', ['branch-A', 'branch-B']),
            ('tests/data/specs/spec_1.yaml', 'branch-A', ['leaf-A1']),
            ('tests/data/specs/spec_1.yaml', 'branch-B', ['leaf-B1', 'leaf-B2']),
        ],
    )
    def test_img_downstream(self, stack_spec, spec_fp, img, dependents):
        img = stack_spec.imageDefs[img]
        dependents = [stack_spec.imageDefs[img] for img in dependents]
        assert img.downstream == dependents


    @pytest.mark.parametrize(
        "spec_fp,imgs_changed,img_pre,img_post",
        [
            ('tests/data/specs/spec_0.yaml', ['base'], 'base', 'branch'),
            ('tests/data/specs/spec_0.yaml', ['base'], 'branch', 'leaf'),
            ('tests/data/specs/spec_1.yaml', ['base'], 'base', 'branch-A'),
            ('tests/data/specs/spec_1.yaml', ['base'], 'base', 'branch-B'),
            ('tests/data/specs/spec_1.yaml', ['base'], 'branch-A', 'leaf-A1'),
            ('tests/data/specs/spec_1.yaml', ['base'], 'branch-B', 'leaf-B1'),
            ('tests/data/specs/spec_1.yaml', ['base'], 'branch-B', 'leaf-B2'),
            ('tests/data/specs/spec_1.yaml', ['base'], 'base', 'leaf-A1'),
            ('tests/data/specs/spec_1.yaml', ['base'], 'base', 'leaf-B1'),
            ('tests/data/specs/spec_1.yaml', ['base'], 'base', 'leaf-B2'),
            ('tests/data/specs/spec_1.yaml', ['branch-A'], 'branch-A', 'leaf-A1'),
        ],
    )
    def test_img_build_order(
        self, stack_spec, spec_fp,
        imgs_changed, img_pre, img_post
    ):
        build_order = stack_spec.get_build_order(imgs_changed)
        img_pre = stack_spec.imageDefs[img_pre]
        img_post = stack_spec.imageDefs[img_post]
        img_pre_i = build_order.index(img_pre)
        img_post_i = build_order.index(img_post)
        assert img_pre_i < img_post_i


    @pytest.mark.parametrize(
        "spec_fp,image_key,plan_key,env_key,env_value",
        [
            ('tests/data/specs/spec_2.yaml', 'base', 'PLAN_0', 'TEST_COMMON', 'DEADBEEF'),
            ('tests/data/specs/spec_2.yaml', 'base', 'PLAN_1', 'TEST_COMMON', 'DEADBEEF'),
            ('tests/data/specs/spec_2.yaml', 'base', 'PLAN_0', 'TEST_PLAN_0_A', 'A'),
            ('tests/data/specs/spec_2.yaml', 'leaf', 'PLAN_0', 'TEST_PLAN_0_A', 'AA'),
        ],
    )
    def test_img_dbuild_env(
        self, stack_spec, spec_fp,
        image_key, plan_key, env_key, env_value
    ):
        images_changed = ['base']
        git_suffix = 'a1b2c3d4'
        path = 'fakepath'
        build_params = stack_spec.gen_build_args(
            path, git_suffix, images_changed
        )
        selected = list(filter(
            lambda x: x[0] == image_key and x[3] == plan_key,
            build_params
        ))
        assert len(selected) == 1
        image_build_params = selected[0]
        assert image_build_params[2][env_key] == env_value


    @pytest.mark.parametrize(
        "spec_fp,image_key, plan_skipped",
        [
            ('tests/data/specs/spec_3.yaml', 'leaf', 'PLAN_0'),
        ],
    )    
    def test_img_skip(self, stack_spec, spec_fp, image_key, plan_skipped):
        images_changed = ['base']
        git_suffix = 'a1b2c3d4'
        path = 'fakepath'
        build_params = stack_spec.gen_build_args(
            path, git_suffix, images_changed
        )
        selected = list(filter(
            lambda x: x[0] == image_key and x[3] == plan_skipped,
            build_params
        ))
        assert len(selected) == 0
