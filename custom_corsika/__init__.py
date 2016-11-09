"""
Install a custom CORSIKA for the Atmospheric Cherenkov Plenoscope (ACP)

Usage: install_corsika_acp -p=INSTALL_PATH --username=USERNAME --password=PASSWORD

Options:
    -p --path=INSTALL_PATH      The path to install CORSIKA in
    --username=USERNAME         Username for the KIT CORSIKA ftp-server
    --password=PASSWORD         Password fot the KIT CORSIKA ftp-server
"""
import docopt
import os
import ftplib
import subprocess
import tarfile
import shutil
import pkg_resources
import glob


def call_and_save_std(target, stdout_path, stderr_path, stdin=None):
    stdout = open(stdout_path, 'w')
    stderr = open(stderr_path, 'w')
    subprocess.call(
        target,
        stdout=stdout, 
        stderr=stderr,
        stdin=stdin)
    stdout.close()
    stderr.close()


def main():
    try:
        arguments = docopt.docopt(__doc__)
        install_path = os.path.abspath(arguments['--path'])
        username = arguments['--username']
        password = arguments['--password']

        os.mkdir(install_path)
        os.chdir(install_path)

        # download CORSIKA from KIT 
        corsika_tar = 'corsika-75600.tar.gz'
        ftp = ftplib.FTP('ikp-ftp.ikp.kit.edu') 
        ftp.login(username, password) 
        ftp.cwd('corsika-v750/')
        ftp.retrbinary('RETR '+corsika_tar, open(corsika_tar, 'wb').write)
        ftp.quit()

        # untar, unzip the CORSIKA download
        tar = tarfile.open(corsika_tar)
        tar.extractall(path=install_path)
        tar.close()

        # Go into CORSIKA dir
        corsika_path = os.path.splitext(os.path.splitext(corsika_tar)[0])[0]
        os.chdir(corsika_path)

        # Provide coconut config.h
        corsika_config_path = pkg_resources.resource_filename(
                'custom_corsika', 
                'resources/config.h')
        shutil.copyfile(corsika_config_path, 'include/config.h')

        # coconut configure 
        call_and_save_std(
            ['./coconut'], 
            os.path.join(install_path, 'coconut_configure.stdout'),
            os.path.join(install_path, 'coconut_configure.stderr'),
            stdin=open('/dev/null', 'r'))

        # Extend the IACT.c buffer sizes
        iact_diff_path = pkg_resources.resource_filename(
                'custom_corsika', 
                'resources/iact.c.diff')

        call_and_save_std(
            ['patch', 'bernlohr/iact.c', iact_diff_path], 
            os.path.join(install_path, 'iact_patch.stdout'),
            os.path.join(install_path, 'iact_patch.stderr'))

        # coconut build
        call_and_save_std(
            ['./coconut', '-i'], 
            os.path.join(install_path, 'coconut_make.stdout'),
            os.path.join(install_path, 'coconut_make.stderr'))

        # Copy std ATMPROFS to the CORSIKA run directory
        for atmprof in glob.glob('bernlohr/atmprof*'):                                                                                                                                      
            shutil.copy(atmprof, 'run')

        # Copy additional ATMPROFS from sim tel array to the CORSIKA run directory
        add_atmprofs_path = pkg_resources.resource_filename(
            'custom_corsika', 
            'resources/atmprofs/atmprof*')
        for atmprof in glob.glob(add_atmprofs_path):                                                                                                                                      
            shutil.copy(atmprof, 'run')

    except docopt.DocoptExit as e:
        print(e)

if __name__ == '__main__':
    main()