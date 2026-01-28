from setuptools import setup, find_packages

setup(
    name='subscriber',
    version='0.1.0',
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
