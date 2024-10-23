# Copyright (c) SCITT Authors.
# Licensed under the MIT License.

from setuptools import setup, find_packages

setup(
    name="scitt-software-supply-chain-middleware",
    version="0.0.1",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "aiohttp",
    ],
)
