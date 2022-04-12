from distutils.core import setup
from setuptools import find_packages
import codecs
import os.path


# https://packaging.python.org/guides/single-sourcing-package-version/
def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

setup(name='gpu_tester',
      version=get_version('gpu_tester/__init__.py'),
      description='',
      author='',
      author_email='',
      url='',
      packages=find_packages(),
     )