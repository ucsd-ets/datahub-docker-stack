## Dir structure

```
.github/
|-- workflows/
|   |-- main.yml (only push successful changes on main branch)
images/
|-- datahub-base-notebook/
|   |-- requirements.txt
|   |-- Dockerfile.template (args replace e.g. python=3.8) FROM XXX:${TAG}
|-- scipy-ml-notebook/
|   |-- requirements.txt
|   |-- Dockerfile
|-- specs.yml (dependency, tags, version_args) 2021.2 2021.3
```

## Notes

- staging or push-after-tests-complete?
- how to refer to pushed tags
- migration
- proposal: change conda dir persmission to `$NB_GID`(`:100`), allow writes after launch instead of writing to `~/.local/lib/python3.X/site-packages` which can cause some issues switching images. Could also reduce number of images served (auto-run scripts on startup)

## Pipeline

| Step 	| Description                                                            	| Implemented in                       	|
|------	|------------------------------------------------------------------------	|--------------------------------------	|
| 1    	| Determine which image definitions are changed compared to last commit  	| `git_helper.py`                      	|
| 2    	| Output build order according to dependency and changed images          	| `order.py`, `docker_builder.py`      	|
| 3    	| Update base tags in Dockerfile to latest version                       	| thru `{build_args}`                  	|
| 4    	| Use new git-hash[:7] for new tags. Build the tree in the correct order 	| `git_helper.py`, `docker_builder.py` 	|
| 5    	| Push new images to Dockerhub with git-hash tags                        	| `docker_pusher.py`                   	|
| 6    	| Run manifests in each newly built images                               	| `docker_runner.py`, `manifests.py`   	|
| 7    	| Run tests in each newly built images                                   	|                                      	|
| 8    	| ? If tests success, tag all newly built images to stable and push ?    	|                                      	|

## Tagging Tradeoffs Analysis

### Docker bakery

- incremental tagging feature looks great
- no way to do revert

### Re-tag to `latest` on build / Tag templating

- Ditch numbered tags
- Instead we can tag using git hash for incremental updates, e.g. `:2021.2-d02157`
- And tag the latest version as `-stable`
- This is also to ensure that all past versions of an image is persisted on dockerhub
- So a version of an image can have multiple tags at once, just like jupyter-docker-stacks
- If we were to revert, we will retag the specific version as stable.
- This retag could be manually triggered with some custom input using github actions
- For reproducability, we will store a copy of the Dockerfile inside the wiki
- The `FROM` statement of that Dockerfile will be using the specific git-tagged image when that image is being built.
- For more reference, we also keep history of what `image:tag` pair are bases of each other.
- Will need on-demand pre-puller / script to clear cache of `-stable`-tagged images on nodes for pulling down/syncing new versions. Enable new users to use latest version of images.

- question: if would like to skip certain images

### Monolithic build

- Clean structure with clear dependency. At any point in time, every image will have the same git-tagged tag. So no worry for dependency across builds.
- Could take a long time to build. 

## Other nice-to-haves

- Separation of system and python packages, and in turn
- Enable read/write access to conda environment `/opt/conda`, gid 100
- Keeping system root locked
- Pip/conda package version pinning
