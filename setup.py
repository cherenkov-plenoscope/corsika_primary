import setuptools
import os

with open("README.md", "r") as f:
    long_description = f.read()

version = {}
with open(os.path.join("corsika_primary/version.py")) as f:
    exec(f.read(), version)

setuptools.setup(
    name="corsika_primary",
    version=version["__version__"],
    description="Call the modified CORSIKA-primary in a thread safe way.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cherenkov-plenoscope/corsika_install.git",
    author="Sebastian Achim Mueller",
    author_email="sebastian-achim.mueller@mpi-hd.mpg.de",
    packages=[
        "corsika_primary",
    ],
    package_data={
        "corsika_primary": ["tests/resources/*", "scripts/install.py"]
    },
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
