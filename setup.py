from distutils.core import setup
import os

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths

setup_py_path = os.path.realpath(__file__)
setup_py_dir = os.path.dirname(setup_py_path)
extra_files = package_files(os.path.join(setup_py_dir,'acp_corsika_install','resources'))


setup(
    name='acp_corsika_install',
    version='0.0.0',
    description='Install CORSIKA for the Atmospheric Cherenkov Plenoscope (ACP).',
    url='https://github.com/TheBigLebowSky/acp_corsika_install.git',
    author='Sebastian Achim Mueller, Axel Engels',
    author_email='sebmuell@phys.ethz.ch',
    license='MIT',
    packages=[
        'acp_corsika_install',
    ],
    package_data={'acp_corsika_install': extra_files},
    install_requires=[
        'docopt',
    ],
    entry_points={'console_scripts': [
        'acp_corsika_install = acp_corsika_install.__init__:main',
    ]},
    zip_safe=False,
)
