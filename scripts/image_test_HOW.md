# Github Workflow: How do image acceptence tests work (Quick Notes)

## Some Observation:
`run_test(stack_dir:str)` in *docker_tester.py* is functionally the same as `image_test(image_tag:str,test_dirs:Path)` in *docker_unit.py*

`run_test()` seems not be called anywhere.


## Function-call Tracing `image_test()`

In *dodo.py*, `task_unit_build()` creates and returns a **ContainerFacade**, which contains a **ContainerTester**, which contains a member function `container_test()` in *docker_unit.py*

In the workflow from top level, pytest/doit will call `build_unit(ContainerFacade)`, where **ContainerFacade** will run `build_test_push_containers()`, which runs `container_test(stack_dir, build_info.images_built)`

## What is `images_built` of `build_info`
`build_info` is of class **BuildInfo**, and `images_built` is a List[str] attribute.

But the actual constructor is the static function `get_build_info_from_filesystem(stack_dir:str,spec_file='spec.yml')`, which is passed in as a class member `retrieval_func` to a **BuildInfoRetrieval**

## What is `stack_dir`
Finally, `stack_dir` is just a string, and would always take default value 'images'. (See *dodo.py* `task_unit_build()` return)


## `build_units()`: the function that actually builds images
NOTE: the values(), i.e. `build_param.full_image_tag`, of the returned Dict are meaningful and would later be used.  
Each is like *ucsdets/datahub-base-notebook:2023.1-c11a915*

```Python
def build_units(build_params:Buildargs,stack_dir:str)->Dict:
    '''
    This Function build image and it dependecies
        build_params:
        stack_dirs:
    '''
    images = {}
    for build_param in build_params:
        #image_name, build_path, build_args, plan_name, image_tag = build_param
        print('image building {}'.format(build_param.full_image_tag))
        image, meta = dbuild(
                            path=build_param.imgPath,
                            build_args=build_param.build_args,
                            image_tag=build_param.full_image_tag,
                            nocache=False
                        )
        images[build_param.imgDef] = build_param.full_image_tag     
    return images
```

## What will happen in `build_test_push_containers()`
`build_unit(ContainerFacade)` is just a static function wrapper around `ContainerFacade.build_test_push_containers()`  
It does the following 3 major tasks:
1. Create a local var `build_info` of type **BuildInfo**
2. For each image that has been detected changed, but not been built yet:
   - get build parameters of this single image
   - build
   - store built images
   - push externally tested images
   - test container
   - push the container
   - delete the container
3. Store the `images_dep: Dict` with the (key: value) of (image name: its dependency/PARENT)


## QUESTION & CONCERN
### 1.
In *dodo.py*, we construct a **ContainerFacade** as the following:
```Python
def task_unit_build():
    """Build docker image and test it unit wise"""
    # at runtime, configure real objects
    build_retrieval = BuildInfoRetrieval(retrieval_func=get_build_info_from_filesystem)
    build_info_storage = BuildInfoStorage(images_built_func=store_images_on_filesystem)
    container_builder = ContainerBuilder(container_builder_func=build_units)
    container_tester = ContainerTester(container_tester_func=container_test)  # line 113
    pusher_func=setup_pusher_func("etsjenkins", os.environ['DOCKERHUB_TOKEN'])
    container_pusher = ContainerPusher(container_pusher_func=pusher_func)
    container_deleter = ContainerDeleter(container_deleter_func=delete_docker_containers)

    container_facade = ContainerFacade(
        build_retrieval,
        container_builder,
        container_tester,   # tester: ContainerTester
        container_pusher,
        container_deleter,
        build_info_storage
    )
```
But the class definition of **ContainerFacade** in *docker_unit.py* doesn't match
```Python
class ContainerFacade:
    def __init__(self, 
                 build_info: BuildInfo, 
                 builder: ContainerBuilder, 
                 tester: ContainerTester, 
                 pusher: ContainerPusher,
                 deleter: ContainerDeleter,
                 build_info_storage: BuildInfoStorage):
        self.build_info = build_info
        self.builder = builder
        self.tester = tester
        self.pusher = pusher
        self.deleter = deleter
        self.build_info_storage = build_info_storage
```

### 2.
What is the significance of doing both `push_untested_container()` and `push_container()`
in `build_test_push_containers()`

Now we have 13 builds if all 4 images are changed (ideally only 4 builds):  
[base, img1, base, img2, base, img3], base, [base, img1, base, img2, base, img3]

Could it be caused by pushing untested & tested?

UPDATE: untested image is only built for scipy-ml.
ALL of the following 3 lines exist in the workflow log:  
```pushed <Image: 'ucsdets/scipy-ml-notebook:2023.1-c11a915'> to ucsdets/scipy-ml-notebook:2023.1-c11a915-untested```  
AND  
```pushed <Image: 'ucsdets/scipy-ml-notebook:2023.1-c11a915', 'ucsdets/scipy-ml-notebook:2023.1-c11a915-untested'> to ucsdets/scipy-ml-notebook:2023.1-c11a915```  
AND  
```pushed <Image: 'ucsdets/scipy-ml-notebook:2023.1-c11a915', 'ucsdets/scipy-ml-notebook:2023.1-c11a915-untested'> to ucsdets/scipy-ml-notebook:2023.1-c11a915-untested```  

## EXPECT BEHAVIOR: 
This `container_test()` runs `image_test()` on EACH IMAGE ONCE.


# Tree Structure refractor
What to do with `images/spec.yml`?

Shall we add `children` (OPPOSITE of `depend_on`) field to each image?

Each time we should build the complete tree containing all images?

```python
class Node:  
    image_name: str  
    filepath: str  
    rebuild: bool  
    children: list[Node]
```

Components
1. tree builder
2. tree pruner
3. tree test runner

In tree builder: we process `spec.yml` and create nodes on-the-fly by checking `IMAGES_CHANGED` to set boolean *rebuild*. 

How to LINK parent node and children nodes together? Shall we store actual child Node object in children[], or just the image_name? 

These nodes should be stored in a `Dict` with key: value being name_str: image_node.