import setuptools
from pathlib import Path

with open(Path(__file__).parent / "README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="splatlog",
    version="0.2.0",
    author="nrser",
    author_email="neil@neilsouza.com",
    description="Python logger that accepts ** values and prints 'em out.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nrser/splatlog",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
    ],
    python_requires=">=3",
    install_requires=[
        # Pretty terminal printing
        "rich>=9",
    ],
    license="BSD License",
    license_files=[
        "LICENSE",
    ],
)
