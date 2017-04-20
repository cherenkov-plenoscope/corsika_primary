from distutils.core import setup

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
    package_data={'acp_corsika_install': ['resources/*']},
    install_requires=[
        'docopt',
    ],
    entry_points={'console_scripts': [
        'acp_corsika_install = acp_corsika_install.__init__:main',
    ]},
    zip_safe=False,
)
