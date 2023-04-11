# datahub-docker-stack

This Github repository builds and maintains the [standard suite of Docker containers](https://support.ucsd.edu/services?id=kb_article_view&sysparm_article=KB0032173&sys_kb_id=e61b198e1b74781048e9cae5604bcbe0) supported by UC San Diego Educational Technology Services.

## Usage

For students and instructors, check out the offical [FAQ](https://support.ucsd.edu/services?id=kb_article_view&sysparm_article=KB0030470&sys_kb_id=aee8868b1b15f810506f64e8624bcb5e) for running containers on the DSMLP platform.

## Maintenance

For people who are trying to modify the image stack, here are some scenarios and instructions on each.

**Important**: for all changes, it is advised to make a new branch with the name `dev_***` for developing and testing before merging it to the `main` branch for the official update. And also make sure all the changes are in **one** commit when you push to Github. This can be done by changing the first commit continuously: `git add . && git commit --amend`. Failure to do so may break the dependency between images. 

### Adding a New Image

1. Clone the repository and make a new branch: `git checkout -b dev_***_notebook`.
2. Make a new directory under `./images` with the name being the base-name of the new image. For example, for `ucsdets/scipy-ml-notebook`, make a new directory `./images/scipy-ml-notebook`.
3. Under the new directory, add the Dockerfile and the neccessary bits for building the container.
4. Modify `./images/spec.yml`. Add a new key under `/images` with the new base-name. Fill in the full `image_name`, its upstream base image key `depend_on`.
5. Push the commit to Github. Make a pull request from the new branch to `main` through the Github interface. Do not merge right now and wait for the workflow ([Github Action](https://github.com/ucsd-ets/datahub-docker-stack/actions)) to finish. It will build the image stack and test each image for features, but it will not push any changes to Dockerhub.
6. If the workflow failed, go to the action details page and debug the issue. Push a new change by amending the first commit `git add . && git commit --amend`.
7. If the workflow completed successfully (a green check to the left of the commit), you can now safely merge the pull request to the `main` branch.
8. The workflow will now run again and push the images to Dockerhub.

### Modifying an Image

1. Clone the repository and make a new branch: `git checkout -b dev_***_notebook`.
2. Under `image/`, find the respective directory for the image you want to change. A manifest of a recent build can be found in the [wiki](https://github.com/ucsd-ets/datahub-docker-stack/wiki) section. An example of a manifest is [here](https://github.com/ucsd-ets/datahub-docker-stack/wiki/ucsdets-datahub-base-notebook-2021.2-ec12f6b).
3. Make the changes and commit to Github. Note, that putting the words "full rebuild" in your commit message will trigger all of the images to rebuild within the workflow.
4. Make a pull request from the new branch to `main` through the Github interface. Do not merge right now and wait for the workflow ([Github Action](https://github.com/ucsd-ets/datahub-docker-stack/actions)) to finish. It will build the image stack and test each image for features, but it will not push any changes to Dockerhub.
5. If the workflow failed, go to the action details page and debug the issue. Push a new change by amending the first commit `git add . && git commit --amend`.
6. If the workflow completed successfully (a green check to the left of the commit), you can now safely merge the pull request to the `main` branch.
7. The workflow will now run again and push the images to Dockerhub.

### GitHub Action Build Pipeline Behavior
To save build time, not all images necessarily build with every change to the repository.

The current behavior can be found under `scripts/get_helper.py` under the `get_changed_items()` function. Typically, if a file under any of the `images/` subdirectories is changed, that image will be slated for rebuilding.

Normally, the commit will check the files that were changed between the current commit being tested and the last commit. If a change is detected in the DataHub Base Notebook, then all child images are rebuilt. If a child image is changed, the parent needs to be rebuilt so that the child has an image to pull from, but the siblings will not be changed.

If the commit was made in main, all images will be rebuilt so that the Tag Images action will have 4 rebuilt images to push to stable. Ideally we shouldn't be making changes to main very often, so full rebuilds on this branch shouldn't result in much time loss.

Sometimes you might want to make changes in scripts or other underlying config files that would alter the build behavior but wouldn't normally trigger a rebuild. If the commit message has "full rebuild" in it, then all of our images will be rebuilt.

### Overview of the Repository
We Use github workflow to builds new images if their is any change in the images or addtional images are added.
.github:-
        The main.yml file contains the steps to build the image
            - Initial download required for the images are installed
            - Doit module is used to run the tasks
                1) install all the requirments for the images
                2) Use doit unit build to build,test and push the image to DataHub repo
                3) Update the wiki  
                4) Store the artifacts and logs
        The Tag.yml file is used to tag the latest build. It requires test_gpu.yml passes.
        Test_Gpu.yml is used to test an image with a specified tag for the scipy-ml notebook. It can be triggered manually.

Images:-
        1) Folder containing the images and each images has its own docker file, test folder for test scripts.
        2) Spec.yml file is important file where the dependecy of the image and build information specified for an image

Model:-
        1) Spec.py used for reading the spec file and prepare build parameters
        2) imagedef.py pydantic object used by spec.py
scripts:-
        1) dataojects.py contains the pydantic class
        2) docker_unit.py used to build,test and push images
            - ContainerFacade class controls the flow of the code
            - build_test_push_containers method is used for building,test and push image
        3) githelper has code for git related task
        4) manifests.py has utils methods to maintain the manifests
        5) Other docker file will be deprecated except for manifest
Tests:-
        1) Contains the test file for testing the submodule
        2) used with pytest can be called with pytest test_*.py
dodo.py:-
        1) We use doit python module to call the submodule 

Steps to build locally:
    1) Clone the Repository
    2) Install the requirments in scripts folder
    3) Provide permission to build the Docker images
    4) Use doit list to list all the commands
    5) To build images locally use doit unit_build
    6) TO run the pytest use pytest tests/test_*.py
        - pytest tests test_docker_unit.py -m "not webtest"
        - to test push functionality edit cred.json with datahub credentials
        - to run test with push functionality use flag 
            pytest tests test_docker_unit.py -m webtest


