from distutils.core import setup

setup(
    name='custom_corsika',
    version='0.0.0',
    description='Install CORSIKA for the Atmospheric Cherenkov Plenoscope (ACP).',
    url='https://github.com/TheBigLebowSky/custom_corsika.git',
    author='Sebastian Achim Mueller, Axel Engels',
    author_email='sebmuell@phys.ethz.ch',
    license='MIT',
    packages=[
        'custom_corsika',
    ],
    install_requires=[
        'docopt',
    ],
    entry_points={'console_scripts': [
        'custom_corsika = custom_corsika.main:main',
    ]},
    zip_safe=False,
)
