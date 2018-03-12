import os
import ftplib
import tarfile
import shutil
import pkg_resources
import glob
from . import tools


def install(install_path, username, password):
    """
    Installs the KIT CORSIKA for the Atmospheric Cherenkov Plenoscope (ACP) into 
    the 'install_path'. 

    During the installation, the stdout and stderr of the 'coconut_configure' 
    and 'coconut_make' procedures are written into text files in the install 
    path.  

    Visit the CORSIKA homepage: https://www.ikp.kit.edu/corsika/
    You can test your username and password in the download section of the 
    KIT CORSIKA webpages. If you do not have yet the CORSIKA username and 
    password, then drop the CORSIKA developers an e-mail and kindly ask for it.

    Parameters
    ----------
    install_path        The path where this CORSIKA instance will be downloaded 
                        to and build in.

    username            The current KIT CORSIKA username.

    password            The current KIT CORSIKA password.
    """
    os.mkdir(install_path)
    os.chdir(install_path)

    # download CORSIKA from KIT 
    corsika_tar = 'corsika-75600.tar.gz'
    ftp = ftplib.FTP('ikp-ftp.ikp.kit.edu') 
    ftp.login(username, password) 
    ftp.cwd('old/v750/')
    ftp.retrbinary('RETR '+corsika_tar, open(corsika_tar, 'wb').write)
    ftp.quit()

    # untar, unzip the CORSIKA download
    tar = tarfile.open(corsika_tar)
    tar.extractall(path=install_path)
    tar.close()

    # Go into CORSIKA dir
    corsika_path = os.path.splitext(os.path.splitext(corsika_tar)[0])[0]
    os.chdir(corsika_path)

    # Provide the ACP coconut config.h
    corsika_config_path = pkg_resources.resource_filename(
            'acp_corsika_install', 
            'resources/config.h')
    shutil.copyfile(corsika_config_path, 'include/config.h')

    # coconut configure 
    tools.call_and_save_std(
        ['./coconut'], 
        os.path.join(install_path, 'coconut_configure.stdout'),
        os.path.join(install_path, 'coconut_configure.stderr'),
        stdin=open('/dev/null', 'r'))

    # coconut build
    tools.call_and_save_std(
        ['./coconut', '-i'], 
        os.path.join(install_path, 'coconut_make.stdout'),
        os.path.join(install_path, 'coconut_make.stderr'))

    # Copy std ATMPROFS to the CORSIKA run directory
    for atmprof in glob.glob('bernlohr/atmprof*'):                                                                                                                                      
        shutil.copy(atmprof, 'run')

    # Copy additional ATMPROFS from sim tel array to the CORSIKA run directory
    add_atmprofs_path = pkg_resources.resource_filename(
        'acp_corsika_install', 
        'resources/atmprofs/atmprof*')
    for atmprof in glob.glob(add_atmprofs_path):                                                                                                                                      
        shutil.copy(atmprof, 'run')

    if os.path.isfile('run/corsika75600Linux_QGSII_urqmd'):
        return 0
    else:
        return 1
