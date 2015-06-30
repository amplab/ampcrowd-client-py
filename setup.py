#!/usr/bin/env python2.7
try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
from setuptools import setup, find_packages
import ampcrowd_client

setup(name="ampcrowd_client",
      version=ampcrowd_client.__version__,
      description="A python client for using the AMPCrowd service.",
      license="Apache License 2.0",
      author="Daniel Haas",
      author_email="dhaas@cs.berkeley.edu",
      url="http://github.com/amplab/ampcrowd-client-py",
      packages = find_packages(),
      include_package_data = True,
      package_dir = {'ampcrowd_client' : 'ampcrowd_client'},
      scripts = [
      ],
      install_requires = [
        'tornado'
      ],
      keywords= "")
