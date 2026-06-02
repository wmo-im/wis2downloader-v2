import os
import re
from setuptools import setup, find_packages


def get_version():
    init = os.path.join(os.path.dirname(__file__), 'shared', '__init__.py')
    with open(init) as f:
        m = re.search(r"^__version__ = ['\"]([^'\"]+)['\"]", f.read(), re.M)
    if m:
        return m.group(1)
    raise RuntimeError("Cannot find __version__ in shared/__init__.py")


setup(
    name='shared',
    version=get_version(),
    description='Shared utilities for wis2downloader modules',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'redis>=4.0.0',
        'shapely>=2.0.0',
    ],
    python_requires='>=3.10',
)
