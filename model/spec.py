from scripts.utils import get_specs, read_var, store_dict, store_var
import logging
from model.imageDef import DockerImageDef
from scripts.docker_info import get_dependency
import os
from scripts.utils import get_specs, get_prev_tag
pjoin = os.path.join


class BuilderSpec:
    def __init__(self, yml_dict):

        # TODO: Assertions
        self.imageDefs = {}
        self.plans = {}
        self.img_root = None
        self.build_params_list = []
        self.parse_build_plans(yml_dict['plans'])
        self.parse_img(yml_dict['images'])

    def parse_build_plans(self, plan_specs):
        self.plans = plan_specs

    # FIXME: will there be more than 1 root?
    # set up all imageDefs
    def parse_img(self, image_specs):
        root = None
        images = {}
        for key, image in image_specs.items():
            if key not in images:
                curr_image = DockerImageDef(key, image['image_name'])
                images[key] = curr_image
            else:
                curr_image = images[key]
            if 'skip_plans' in image.keys():
                curr_image.skip_plans = image['skip_plans']
            if 'dbuild_env' in image.keys():
                curr_image.dbuildenv = image['dbuild_env']
            if 'depend_on' in image.keys():
                dep_image_name = image['depend_on']
                if dep_image_name not in images:
                    dep_image = DockerImageDef(dep_image_name)
                    images[dep_image_name] = dep_image
                else:
                    dep_image = images[dep_image_name]
                curr_image.depend_on = dep_image
                dep_image.downstream.append(curr_image)
            else:
                root = images[key]
        assert root is not None
        self.imageDefs = images
        self.img_root = root

    def gen_build_args(self, path, git_suffix, img_modified, logger):
        build_order = self.get_build_order(img_modified)
        for imgDef in build_order:
            imgDef.to_build = True
            imgPath = pjoin(path, imgDef.name)
            for plan_name, plan in self.plans.items():
                build_args = {}
                curr_tag = f"{plan['tag_prefix']}-{git_suffix}"
                full_image_tag = f"{imgDef.img_name}:{curr_tag}"
                if plan_name in imgDef.skip_plans:
                    logger.info(f"Skipped {full_image_tag}")
                    continue
                # get base tag
                if imgDef.depend_on is not None:

                    # if dependent img is built in this run
                    if imgDef.depend_on.to_build:
                        base_tag = curr_tag
                    # get previous tag
                    else:
                        # TODO: throw error if prev tag not present
                        # TODO: Further testing on this
                        prev_tag = get_prev_tag(imgDef.img_name, plan_name)
                        base_full_tag = get_dependency(prev_tag)
                        base_tag = base_full_tag.split(':')[1]
                    build_args.update(BASE_TAG=base_tag)

                if len(imgDef.dbuildenv) > 0:
                    if 'common' in imgDef.dbuildenv:
                        build_args.update(imgDef.dbuildenv['common'])
                    if plan_name in imgDef.dbuildenv:
                        build_args.update(imgDef.dbuildenv[plan_name])
                self.build_params_list.append(
                    (imgDef.name, imgPath, build_args, plan_name, full_image_tag))

        return self.build_params_list

    def get_build_order(self, images_changed):
        tree_order = self.img_root.get_level_order()
        image_order = []
        for image in images_changed:
            if image in self.imageDefs:
                image_def = self.imageDefs[image]
                image_order.append((image_def, tree_order[image_def]))
            image_order.sort(key=lambda x: x[1])
        build_order = []
        for idx in range(len(image_order)):
            curr_image_def = image_order[idx][0]
            if image_order[idx][0] not in build_order:
                build_order += (curr_image_def.subtree_order())
        print('build order is', build_order)
        return build_order

    def __str__(self):
        return f'spec({self.imageDefs},{self.plans},{self.img_root})'


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    path = 'images'
    specs = 'spec.yml'
    specs = get_specs(pjoin(path, specs))
    images_changed = ['datascience-notebook',
                      'datahub-base-notebook', 'spec.yml']
    git_suffix = 'cb6be13'
    build_spec = BuilderSpec(specs)
    build_params = build_spec.gen_build_args(
        path, git_suffix, images_changed, logger)
    print(build_spec)
    print(build_params)
