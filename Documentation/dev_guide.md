# DataHub Docker Stack: Development Guide

## Docker Concepts

Before listing the commands we use, we'd like to give a brief introduction of Docker concepts.

- **Docker**: Docker is a set of platform as a service (PaaS) products that use OS-level virtualization to deliver software in packages called containers. In short, it's a platform that provide you with containerized/isolated software/system.
- **Docker Image**: Image is a static, immutable template that defines the behavior of your software/system. Most of the time, we 'build' an image.
- **Docker Container**: Container is a runtime instance. Most of the time, we 'run' or 'start' a container.
- **Dockerhub**: Dockerhub is a place to store your Docker images just like Github stores your code.

## Docker Commands

Here are the commands (signature + example) you will use often:

- image-related

```bash
# Build an image from a local Dockerfile
# <path> is where the Dockerfile stays in
$ docker build -t <image_name>:<tag> <path>
$ docker build -t rstudio-notebook:myTest ./images/rstudio-notebook

# List images
$ docker images

# Pull an image from Dockerhub
$ docker pull <image_name>:<tag>
$ docker pull ghcr.io/ucsd-ets/rstudio-notebook:2023.2-d3e5619

# Push an local image to Dockerhub
$ docker push <image_name>:<tag>
$ docker push ghcr.io/ucsd-ets/rstudio-notebook:2023.2-d3e5619
```

- container-related

```bash
# Run a (new) container
$ docker run -d -p <host port>:<container port> <image_name>:<tag>
$ docker run -d -p 80:80 rstudio-notebook:myTest

# Start a stopped (not active) container
$ docker start <container ID/Name>
$ docker start 87120d0aefb0  # this is container ID

# Stop a running container
$ docker stop <container ID/Name>
$ docker stop 87120d0aefb0  # this is container ID

# List info of all (running or not) containers
$ docker ps -a

# Remove a container
$ docker rm <image_name>:<tag>
$ docker rm rstudio-notebook:myTest
```

Alternatively, you may use [Docker Desktop](https://www.docker.com/products/docker-desktop/) to save you from typing all these commands. But keep in mind that some options are not supported or hard to find in the UI.

[Official Docs](https://docs.docker.com/engine/reference/run/) is the place with most comprehensive information.

If you are familiar with the concepts already, this [cheatsheet](https://dockerlabs.collabnix.com/docker/cheatsheet/) is also a great reference.

## Setup Virtual Environment

If you want to run any Python code from a project locally, it's always a good habit to create a virtual environment and install all required packages there. You can either use conda environment or python venv. They have some subtle difference but are functionally the same for our purpose

```bash
# create a Python venv locally (root of this repo)
$ python -m venv .

# Each time: activate the venv
$ source bin/activate
```

```bash
# create a conda environment
$ conda create --name <name you choose>

# Each time: activate the environment
$ conda activate <name you choose>
```

After you create the virtual environment, install Python packages used in this repo:

```bash
# assume you are in the project root
$ pip install -r scripts/requirements.txt
```

## Adding a New Image

1. Clone the repository and make a new branch: `git checkout -b dev_***_notebook`.
2. Make a new directory under `./images` with the name being the base-name of the new image. For example, for `ghcr.io/ucsd-ets/scipy-ml-notebook`, make a new directory `./images/scipy-ml-notebook`.
3. Modify `./images/spec.yml`. Add a new key under `/images` with the new base-name. Fill in the full `image_name`, its upstream image base-name `depend_on`. To understand what other fields do, please refer to our [images.md](/Documentation/images.md#L20)
4. Under the new directory, add the Dockerfile and the necessary bits for building the container. For how to write a Dockerfile, please refer to the [official doc](https://docs.docker.com/engine/reference/builder/) or other tutorials.
5. Follow the instructions in [images.md](/Documentation/images.md#recommened-steps-to-follow)

## Modifying an Image (fix bugs or add features)

1. Clone the repository and make a new branch: `$ git checkout -b dev_<image name>`.
2. Under `image/`, find the respective directory for the image you want to change. A manifest of a recent build can be found in the [wiki](https://github.com/ucsd-ets/datahub-docker-stack/wiki) section. An example of a manifest is [here](https://github.com/ucsd-ets/datahub-docker-stack/wiki/ucsdets-datascience-notebook-2021.2-ec12f6b).
3. Follow the instructions in [images.md](/Documentation/images.md#recommened-steps-to-follow). This time step #1 should be editing the existing Dockerfile.

## Running Image Tests

1. Activate the virtual environment `$ source bin/activate`
2. `$ cd images`
3. `$ export TEST_IMAGE=MYIMAGE` replace `MYIMAGE` with your locally built image name
4. `$ pytest tests_common` as an example

## Running Script Tests

Side Note: For `test_wiki.py` to work, please create 3 folders `logs/`, `manifests/`, and `wiki/` under project root. In addition, please copy this [Home_original.md](/tests/Home_original.md) into `wiki/`.

0. (Only do this once) Unzip the `test_resource.zip` and put the 2 folders `wiki/` and `artifacts/` in the root directory
1. Activate the virtual environment `$ source bin/activate`
2. `$ pytest tests/test_<module name>.py` to test a individual module
3. OR `$ pytest tests` to test all modules

## About Python Unit Test: MagicMock

### Unit Test

The purpose of a unit test is to ensure the correctness of the testing component/module/function/class ONLY.
This means all the helper function or API calls within the testing target should not complicate your unit test
and are assumed to be functionally correct. This is opposed to an integration test, which is usually created
after all the unit tests and aims to ensure every module work together correctly.

Unit tests are arguably the first and necessary step in industry standard of software testing. Again, we strongly
recommend you to write the most basic unit test at least in `tests/` of you make any infrastructure change to `scripts/`.
A unit test not only removes the dependency on some untested yet, potentially buggy components of your testing target, but also save the execution time of performing those API calls even if they have been thoroughly tested.

A concrete example can illustrate this better. Suppose you are testing a Media Player which supports input in the form of local image and video files, YouTube links, etc. The actual reading and rendering of the contents of each type of media have been tested by other senior developers and your job is just to make sure the Player recognizes and invokes the matching function call correctly. E.g. `some_youtube_video.mp4` should not be treated as a YouTube link. You created several inputs for each type, but you don't really want to call the actual reading-playing functions, which are definitely an expensive operation. Instead, you only want to know if they are called at the correct time. To achieve this, you need a way to know how many times each reading-playing function has been called.

### Mock: a NO-OP Duplicate

Following the above example, the first thing you may think of is to attach some EventListener to the functions of interest. Congratulations, you are a good developer. But this is not a good testing practice because it unnecessarily
complicates the testing. Instead, we will replace all the actual components we assume are working with some no-op
duplicates of which we have access to the calling count. These duplicates are called ***mocks*** and are included in
`unittest.mock` module in Python. If you would like a general introduction to it, you can read [this blog](https://aaronlelevier.github.io/python-unit-testing-with-magicmock/). For more details, see the [official doc](https://docs.python.org/3/library/unittest.mock.html).

### `MagicMock` and `patch`, 2 Key Components of `mock`

I will briefly go over these 2 in case you haven't read the above blog. Essentially, `MagicMock` is a mock object
whose behavior can be configured and calling information (more than call count) can be read.
And `patch` is a decorator to tell you testing function that "please replace this actual function with a `MagicMock` object."

One thing to notice is "which `MagicMock` exactly to use" when you make the request to `patch`. I found most example
code says "I will give it later in the function argument list.", like the following:

```Python
# code from the blog post linked above
@patch("bar.requests.get")
@patch("bar.requests.put")
def test_foo(self, mock_put, mock_get):
    Bar.sync(id=42, query_first=False)

    self.assertFalse(mock_get.called)
    self.assertTrue(mock_put.called)
```

This has 2 limitations. First, all mock objects are passed in via the argument list, and if we need
a lot, we will have an undesirably long list. Secondly, you can see the order of mock objects should
be the reverse of the `patch` decorator order, which is often a source of error. Thus, we suggest the
other approach that says "I will give you all the `MagicMock` to the actual functions now."

```Python
# with my change
mock_get = MagicMock()
mock_put = MagicMock()
@patch("bar.requests.get", mock_get)
@patch("bar.requests.put", mock_put)
def test_foo(self):
    Bar.sync(id=42, query_first=False)

    self.assertFalse(mock_get.called)
    self.assertTrue(mock_put.called)
```

### More Examples in our Tests

Finally, let's look at the usage in our script tests. I think understanding [`test_docker_adapter.py::TestDocker::_tag_stable()`](/tests/test_docker_adapter.py#L87) alone is enough for you to understand all the flexibility we need for `MagicMock` configuration.

```python
# test definition
def _tag_stable(self):
    # to mock:
    # 1. __docker_client.images.get()
    # 2. img_obj.tag()
    # 3. __docker_client.close()

    # NOTE: need to mock an Image obj returned by images.get()
    #       and this mock_img_obj should be able to call tag()
    mock_tag = MagicMock()
    mock_img_obj = MagicMock(tag=mock_tag)
    mock_get = MagicMock(return_value=mock_img_obj)
    mock_images = MagicMock(get=mock_get)
    mock_close = MagicMock()

    @patch('scripts.docker_adapter.__docker_client', images=mock_images, close=mock_close)
    def run_test(pos_arg):
        return internal_docker.tag_stable(self.orig_images[0], self.tag_replace)

    stable_name, result = run_test()
    return (stable_name, result, mock_get, mock_tag, mock_close)

# run the test and check values
def test_tag_stable(self):
    stable_name, result, mock_get, mock_tag, mock_close = self._tag_stable()
    assert result == True, "prepull_images() failed somewhere"
    assert stable_name == self.stable_fullnames[0], f"Stable name is wrong: {stable_name}"
    assert mock_get.call_count == 1, mock_get.call_count
    assert mock_tag.call_count == 1, mock_tag.call_count
    # .args gives argument; .kwargs gives keyword arguments
    arg_list = [arg.kwargs for arg in mock_tag.call_args_list]
    assert arg_list == [{'repository': 'image_1', 'tag': '2099.1-stable'}], arg_list
    assert mock_close.call_count == 1, mock_close.call_count
```

This example has several important points to help you become an insider.

1. A `MagicMock` object can serve as a mock component of another `MagicMock` object. This is often useful when we need to mock both the object and the function it calls in `some_obj.some_f()`, like our `img_obj.tag(repository=repo, tag=tag_replace)`
2. The most commonly config option is the `return_value`, which can also be set as another `MagicMock`.
3. In addition to mock an object entirely, you can also mock only some functions it calls or some attributes it accesses. This can be easily done by passing in keyword arguments in the `patch` decorator. For example, our `scripts.docker_adapter.__docker_client` is of type `docker.DockerClient` which has attributes `images` and function `close()`.
4. Besides `call_count`, we can check a lot more attributes of a `MagicMock` object. Here we look at the call_args_list which gives a list of length n if the mock function has been called n times. To see what attributes are available, you can use `mock_obj.__dir__()` to list them all and go to the [official doc](https://docs.python.org/3/library/unittest.mock.html#the-mock-class) and search for their usage.
5. It's a good idea to separate test definition and test executioner. This can be particularly helpful if we want to test a function several times using different inputs. In our case, we can easily modify the code and test against multiple input like this:

```python
def _tag_stable(self, orig_fullname: str, tag_replace: str):
    # to mock:
    # 1. __docker_client.images.get()
    # 2. img_obj.tag()
    # 3. __docker_client.close()

    # NOTE: need to mock an Image obj returned by images.get()
    #       and this mock_img_obj should be able to call tag()
    mock_tag = MagicMock()
    mock_img_obj = MagicMock(tag=mock_tag)
    mock_get = MagicMock(return_value=mock_img_obj)
    mock_images = MagicMock(get=mock_get)
    mock_close = MagicMock()

    @patch('scripts.docker_adapter.__docker_client', images=mock_images, close=mock_close)
    def run_test(pos_arg):
        return internal_docker.tag_stable(orig_fullname, tag_replace)

    stable_name, result = run_test()
    return (stable_name, result, mock_get, mock_tag, mock_close)

def test_tag_stable1(self):
    orig_fullname, tag_replace = "some_name", "latest"
    stable_name, result, mock_get, mock_tag, mock_close = self._tag_stable()

def test_tag_stabl2(self):
    orig_fullname, tag_replace = "other", "dev"
    stable_name, result, mock_get, mock_tag, mock_close = self._tag_stable()

def test_tag_stable3(self):
    orig_fullname, tag_replace = "unknown", "production"
    stable_name, result, mock_get, mock_tag, mock_close = self._tag_stable()
```
