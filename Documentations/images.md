# DataHub Docker Stack: Images (TODO)

## Image Stack Details

For the pipeline to recognize the stack, there should be a dedicated directory
preferably called `images/` that contains sources for images in the stack.

- One sub-directory under `images/` equals one unique docker image
- Under sub-directory, there should be a `Dockerfile` with the steps to build the image
- `Dockerfile` should be using build-args to dynamically point to arbitary base
image (see sample for details)
- Test can be provided for each image as `test` under their source folder and
for all images (`tests_common` under `images/`). Include the provided
`conftest.py` for them to work
- A `spec.yml` file detailing how the images are structured
- The image sub-directories created should be equal to the keys under `images` in the yaml spec
- Plans can be enabled to serve two or more tracks/versions of the same image
at the same time under one docker image name. Custom tag prefix are used to
identify them
- Manifests are a way to list out information about an image. These can be
defined by a name and a corresponding command to run inside the container.
- Different images can include different sets of manifests.

## Image Customization

- Build args are expected to be used in dynamic image tags for base refs
- They can also be used for swapping out variables for different plans
- Can put custom variables in spec yaml file.

## Image Update Details

- Every newly pushed images will get a git-hash stamp at the end of the tag
(`ucsdets/datahub-base-notebook:2021.2-5f71d3b`)
- The `FROM` statement in `Dockerfile` will include `ARG` in the image ref to
support arbitary tags at run-time. This allows for fixating the Dockerfile
while changing the base ref at any time.
- When a dependent images gets its source updated, instead of building the base
image again, only build the dependent image by changing the base ref to the
old remote tag of the image and build from there.
- `stable` tags will be given to the lastest built image in each image/plan for
use in production.
