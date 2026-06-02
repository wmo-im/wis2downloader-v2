import os
import re
from setuptools import setup, find_packages


def get_version():
    init = os.path.join(os.path.dirname(__file__), '..', 'shared', 'shared', '__init__.py')
    with open(init) as f:
        m = re.search(r"^__version__ = ['\"]([^'\"]+)['\"]", f.read(), re.M)
    if m:
        return m.group(1)
    raise RuntimeError("Cannot find __version__ in shared/__init__.py")


setup(
    name='subscriber',
    version=get_version(),
    description='WIS2 MQTT Subscriber for wis2downloader',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'paho-mqtt>=2.0.0',
        'redis>=4.0.0',
        'python-magic>=0.4.27'
    ],
    entry_points={
        'console_scripts': [
            'subscriber_start=subscriber.__main__:main',
        ],
    },
    python_requires='>=3.10',
)
