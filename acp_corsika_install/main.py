"""
Install the CORSIKA cosmic-ray and gamma-ray air-shower simulation for the 
Atmospheric Cherenkov Plenoscope (ACP).

Usage: acp_corsika_install -p=INSTALL_PATH --username=USERNAME --password=PASSWORD

Options:
    -p --install_path=INSTALL_PATH      The path to install CORSIKA in
    --username=USERNAME                 Username for the KIT CORSIKA ftp-server
    --password=PASSWORD                 Password fot the KIT CORSIKA ftp-server
"""
import docopt
import sys
import os
from ._api import install

def main():
    try:
        arguments = docopt.docopt(__doc__)

        return_value = install(
            install_path=os.path.abspath(arguments['--install_path']),
            username=arguments['--username'],
            password=arguments['--password'])

        sys.exit(return_value)

    except docopt.DocoptExit as e:
        print(e)

if __name__ == '__main__':
    main()
