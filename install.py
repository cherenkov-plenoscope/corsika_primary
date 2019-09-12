#!/usr/bin/env python
# Copyright 2017-2019 Sebastian A. Mueller
"""
Download and install CORSIKA for the Cherenkov-plenoscope.

Usage: install.py --install_path=PATH \
                  --username=USERNAME \
                  --password=PASSWORD \
                  [--resource_path=PATH]

Options:
    --install_path=PATH     Install-path for CORSIKA.
    --username=USERNAME     Username for the KIT CORSIKA ftp-server.
    --password=PASSWORD     Password fot the KIT CORSIKA ftp-server.
    --resource_path=PATH    [default: ./resources] The resources for this
                            particular flavor of CORSIKA.

Std-out and std-error of 'coconut_configure' and 'coconut_make' are written to
text-files in the install-path.

Visit CORSIKA: https://www.ikp.kit.edu/corsika/
You can test your username and password in the download-section of the
KIT-CORSIKA-webpages.

If you do not have the CORSIKA username and password, go and drop the
CORSIKA-developers an e-mail and kindly ask for the password.
"""
import docopt
import os
from os.path import join
import tarfile
import shutil
import subprocess
import glob


def call_and_save_std(target, stdout_path, stderr_path, stdin=None):
    with open(stdout_path, 'w') as stdout, open(stderr_path, 'w') as stderr:
        subprocess.call(target, stdout=stdout, stderr=stderr, stdin=stdin)


def install(install_path, username, password, resource_path):
    install_path = os.path.abspath(install_path)
    resource_path = os.path.abspath(resource_path)
    os.mkdir(install_path)
    os.chdir(install_path)

    # download CORSIKA from KIT
    # wget uses $http_proxy environment-variables in case of proxy
    corsika_tar = 'corsika-75600.tar.gz'
    call_and_save_std(
        target=[
            'wget',
            'ftp://' + username + ':' + password + '@' +
            'ikp-ftp.ikp.kit.edu/old/v750/' + corsika_tar],
        stdout_path='wget-ftp-download.o',
        stderr_path='wget-ftp-download.e')

    # untar, unzip the CORSIKA download
    tar = tarfile.open(corsika_tar)
    tar.extractall(path=install_path)
    tar.close()

    # Go into CORSIKA dir
    corsika_path = os.path.splitext(os.path.splitext(corsika_tar)[0])[0]
    os.chdir(corsika_path)

    # Provide the ACP coconut config.h
    corsika_config_path = join(resource_path, 'config.h')
    shutil.copyfile(corsika_config_path, 'include/config.h')

    # coconut configure
    call_and_save_std(
        target=['./coconut'],
        stdout_path=join(install_path, 'coconut_configure.stdout'),
        stderr_path=join(install_path, 'coconut_configure.stderr'),
        stdin=open('/dev/null', 'r'))

    # coconut build
    call_and_save_std(
        target=['./coconut', '-i'],
        stdout_path=join(install_path, 'coconut_make.stdout'),
        stderr_path=join(install_path, 'coconut_make.stderr'))

    # Copy default ATMPROFS to the CORSIKA run directory
    for atmprof in glob.glob(join('bernlohr', 'atmprof*')):
        shutil.copy(atmprof, 'run')

    # Copy additional ATMPROFS from sim-tel-array to the CORSIKA run directory
    add_atmprofs_path = join(resource_path, 'atmprofs', 'atmprof*')
    for atmprof in glob.glob(add_atmprofs_path):
        shutil.copy(atmprof, 'run')

    if os.path.isfile('run/corsika75600Linux_QGSII_urqmd'):
        return 0
    else:
        return 1


def main():
    try:
        args = docopt.docopt(__doc__)
        return install(
            install_path=args['--install_path'],
            username=args['--username'],
            password=args['--password'],
            resource_path=args['--resource_path'],)
    except docopt.DocoptExit as e:
        print(e)


if __name__ == '__main__':
    main()
