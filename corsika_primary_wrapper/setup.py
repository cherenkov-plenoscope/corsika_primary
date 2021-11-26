import setuptools
import os

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="corsika_primary_wrapper",
    version="0.0.8",
    description="Call the modified CORSIKA-primary in a thread safe way.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fact-project/corsika_wrapper.git",
    author="Sebastian Achim Mueller",
    author_email="sebastian-achim.mueller@mpi-hd.mpg.de",
    packages=["corsika_primary_wrapper",],
    package_data={"corsika_primary_wrapper": ["tests/resources/*",]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
)
