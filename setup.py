from setuptools import setup, find_packages

setup(
    name="acdc_fastapi",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "keri",
        "snoop"
    ],
    entry_points={
        'console_scripts': [
            'acdc-fastapi=acdc_fastapi.cli:main',
        ]
    },
)
