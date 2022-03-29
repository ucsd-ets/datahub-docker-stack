import yaml
from pydantic import BaseModel
from typing import List,Dict

class DockerImageDef(BaseModel):
    name:str
    image_name:str
    depend_on:str=None
    to_build:bool=False
    downstream: List = []
    dbuildenv: Dict = {}
    skip_plans: List = []

