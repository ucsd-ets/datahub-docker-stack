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
3. Make the changes and commit to Github. Make a pull request from the new branch to `main` through the Github interface. Do not merge right now and wait for the workflow ([Github Action](https://github.com/ucsd-ets/datahub-docker-stack/actions)) to finish. It will build the image stack and test each image for features, but it will not push any changes to Dockerhub.
4. If the workflow failed, go to the action details page and debug the issue. Push a new change by amending the first commit `git add . && git commit --amend`.
5. If the workflow completed successfully (a green check to the left of the commit), you can now safely merge the pull request to the `main` branch.
6. The workflow will now run again and push the images to Dockerhub.


### Overview of the Repository
We Use github workflow to builds new images if their is any change in the images or addtional images are added.
.github:-
The main.yml file contains the steps to build the image
+ Initial download required for the images are installed
+ Doit module is used to run the tasks
    - install all the requirments for the images 
    - Use doit unit build to build,test and push the image to DataHub repo
    - Update the wiki  
    - Store the artifacts and log    
The Tag.yml file is used to tag the latest build <br>

Image:- 
- Folder containing the images and each images has its own docker file, test folder for test scripts.
- Spec.yml file is important file where the dependecy of the image and build information specified for an image.
Model:-
- Spec.py used for reading the spec file and prepare build parameters
- imagedef.py pydantic object used by spec.py

scripts:-
- dataojects.py contains the pydantic class
- docker_unit.py used to build,test and push images
    - ContainerFacade class controls the flow of the code
    - build_test_push_containers method is used for building,test and push image
- githelper has code for git related task
- manifests.py has utils methods to maintain the manifests
- Other docker file will be deprecated except for manifest
Tests:-
- Contains the test file for testing the submodule
- used with pytest can be called with pytest test_*.py

dodo.py:-
- We use doit python module to call the submodule 
- Each task is called with parameters and expected outputs

