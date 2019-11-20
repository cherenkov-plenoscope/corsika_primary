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
import hashlib


CORSIKA_75600_TAR_GZ_HASH_HEXDIGEST = '9ef453eebc4bf5b8b04209b1acdebda2'


def md5sum(path):
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def call_and_save_std(target, stdout_path, stderr_path, stdin=None):
    with open(stdout_path, 'w') as stdout, open(stderr_path, 'w') as stderr:
        subprocess.call(target, stdout=stdout, stderr=stderr, stdin=stdin)


def download_corsika_tar(
    output_dir,
    username,
    password,
    ftp_path,
    corsika_tar_filename,
):
    # download CORSIKA from KIT
    # wget uses $http_proxy environment-variables in case of proxy
    call_and_save_std(
        target=[
            'wget',
            '--directory-prefix', output_dir,
            'ftp://' + username + ':' + password + '@' + ftp_path +
            corsika_tar_filename],
        stdout_path=join(output_dir, corsika_tar_filename+'.wget.stdout'),
        stderr_path=join(output_dir, corsika_tar_filename+'.wget.stderror'))


def install(corsika_tar_path, install_path, resource_path, modify):
    install_path = os.path.abspath(install_path)
    resource_path = os.path.abspath(resource_path)
    os.makedirs(install_path, exist_ok=True)

    # untar, unzip the CORSIKA download
    tar = tarfile.open(corsika_tar_path)
    tar.extractall(path=install_path)
    tar.close()

    # Go into CORSIKA dir
    corsika_basename = os.path.basename(
        os.path.splitext(
            os.path.splitext(corsika_tar_path)[0])[0])
    corsika_path = join(install_path, corsika_basename)
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

    if modify:
        shutil.copyfile(
            join(resource_path, 'corsikacompilefile_modified.f'),
            join('src', 'corsikacompilefile.f'))
        shutil.copy(
            join(resource_path, 'iact.c'),
            join('bernlohr', 'iact.c'))
        shutil.copy(
            join(resource_path, 'microtar.h'),
            join('bernlohr', 'microtar.h'))

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

    assert os.path.isfile('run/corsika75600Linux_QGSII_urqmd')



def main():
    try:
        args = docopt.docopt(__doc__)
        ftp_path = 'ikp-ftp.ikp.kit.edu/old/v750/'
        corsika_tar_filename = 'corsika-75600.tar.gz'

        install_path = os.path.abspath(args['--install_path'])
        resource_path = os.path.abspath(args['--resource_path'])
        os.makedirs(install_path, exist_ok=True)

        corsika_tar_path = join(install_path, corsika_tar_filename)

        if not os.path.exists(corsika_tar_path):
            download_corsika_tar(
                output_dir=install_path,
                username=args['--username'],
                password=args['--password'],
                ftp_path=ftp_path,
                corsika_tar_filename=corsika_tar_filename)

        assert CORSIKA_75600_TAR_GZ_HASH_HEXDIGEST == md5sum(
            corsika_tar_filename)

        if not os.path.exists(join(install_path, "original")):
            install(
                corsika_tar_path=corsika_tar_path,
                install_path=join(install_path, "original"),
                resource_path=resource_path,
                modify=False)

        if not os.path.exists(join(install_path, "modified")):
            install(
                corsika_tar_path=corsika_tar_path,
                install_path=join(install_path, "modified"),
                resource_path=resource_path,
                modify=True)

    except docopt.DocoptExit as e:
        print(e)


if __name__ == '__main__':
    main()
