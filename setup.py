from distutils.core import setup

setup(
    name='acp_corsika_install',
    version='0.0.1',
    description='Install CORSIKA for the Atmospheric Cherenkov Plenoscope (ACP).',
    url='https://github.com/TheBigLebowSky/acp_corsika_install.git',
    author='Sebastian Achim Mueller, Axel Engels',
    author_email='sebmuell@phys.ethz.ch',
    license='GPL v3',
    packages=[
        'acp_corsika_install',
    ],
    package_data={'acp_corsika_install': ['resources/*', 'resources/atmprofs/*']},
    install_requires=[
        'docopt',
    ],
    entry_points={'console_scripts': [
        'acp_corsika_install = acp_corsika_install.main:main',
    ]},
    zip_safe=False,
)
