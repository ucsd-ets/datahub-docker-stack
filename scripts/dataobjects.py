from dataclasses import dataclass

@dataclass
class imagespec():
  image_tag: str
  path: str
  parameters:dict
  python_version: str
  image_tag:str

@dataclass
class build_params_object():
    images: list
