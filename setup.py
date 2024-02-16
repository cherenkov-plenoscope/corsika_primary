import setuptools
import os

with open("README.rst", "r", encoding="utf-8") as f:
    long_description = f.read()


with open(os.path.join("corsika_primary", "version.py")) as f:
    txt = f.read()
    last_line = txt.splitlines()[-1]
    version_string = last_line.split()[-1]
    version = version_string.strip("\"'")


setuptools.setup(
    name="corsika_primary",
    version=version,
    description="Install and call the CORSIKA-primary mod.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/cherenkov-plenoscope/corsika_primary",
    author="Sebastian Achim Mueller",
    author_email="sebastian-achim.mueller@mpi-hd.mpg.de",
    packages=[
        "corsika_primary",
        "corsika_primary.I",
        "corsika_primary.particles",
        "corsika_primary.random",
    ],
    package_data={
        "corsika_primary": [
            os.path.join("tests", "resources", "*"),
            os.path.join("scripts", "install.py"),
        ]
    },
    install_requires=["spherical_coordinates"],
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
