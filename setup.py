from setuptools import setup, find_packages

setup(
    name="acdc_fastapi",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn"
    ],
    entry_points={
        'console_scripts': [
            'start-server=acdc_fastapi.cli:main',
        ]
    },
)
