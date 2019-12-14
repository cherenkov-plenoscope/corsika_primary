# Installing CORSIKA for the Cherenkov-plenoscope

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Install the [KIT-CORSIKA](https://www.ikp.kit.edu/corsika/) simulation for air-showers of cosmic-rays and gamma-rays for the Cherenkov-plenoscope. This is based on CORSIKA 7.56 with minor modifications to gain more control over the primary particle. 

## Install:
```bash
./corsika_install/install.py --install_path corsika --username=<CORSIKA-username> --password=<CORSIKA-password> --resource_path ./corsika_install/resources
```
This installs both the original CORSIKA 7.56, and our modified CORSIKA-primary to the ```install_path```.

### Credentials
For CORSIKA's credentials (`username` and `password`) follow the instructions on: https://www.ikp.kit.edu/corsika/index.php. Drop the CORSIKA-team an email, and express your interest in CORSIKA to learn about cosmic-rays and air-showers. They will send you an email back with the credentials. They will not spam you.


## CORSIKA-primary-mod
This mod allows you to control the properties of each primary particle. When starting CORSIKA, you provide a steering-card which specifies all properties which can not be changed over a CORSIKA-run.


### Example steering-card
```
RUNNR 1
EVTNR 1
ERANGE 1. 10.
OBSLEV 2300e2
MAGNET 12.5 -25.9
MAXPRT 1
PAROUT F F
ATMOSPHERE 10 T
CWAVLG 250 700
CERQEF F T F
CERSIZ 1.
CERFIL F
TSTART T
NSHOW 1000
PRMFIL /tmp/corsika_primary_o2j62_aw/primary_bytes.f8f8f8f8f8i4
TELFIL /home/my_username/Desktop/test_depth/different_starting_depths.tar
EXIT
```
Note the abscence of steering for directions such as ```PHIP``` and ```THETAP```. ```CSCATT``` for the core-position's scatter, and ```ESLOPE``` for the energy-spectrum are missing, too. Also the ```SEED```s are missing.
Those are now defined for each event seperately in a dedicated file located at the path defined in ```PRMFIL```.

The ```PRMFIL``` is a binary file with number ```NSHOW``` primary-particle-blocks. The mod reads ```NSHOW``` blocks from the ```PRMFIL```, where ```NSHOW``` is defined in the steering-card.

### Primary-particle-block
```
    +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    |             particle id               |            energy in GeV              | -->
    +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
                   float 64 bit                            float 64 bit
               
    +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
--> |        zenith-distnce in rad          |   azimuth rel. to mag. north in rad   | -->
    +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
                   float 64 bit                            float 64 bit
                   
    +----+----+----+----+----+----+----+----+
--> |      starting depth in g cm^{-2}      |  -->
    +----+----+----+----+----+----+----+----+
                   float 64 bit

    +----+----+----+----+----+----+----+----+----+----+----+----+
--> |    SEED seq. 1    |  CALLS seq. 1     |BILLIONS seq. 1    | -->
    +----+----+----+----+----+----+----+----+----+----+----+----+
         int 32 bit          int 32 bit          int 32 bit

    +----+----+----+----+----+----+----+----+----+----+----+----+
--> |    SEED seq. 2    |  CALLS seq. 2     |BILLIONS seq. 2    | -->
    +----+----+----+----+----+----+----+----+----+----+----+----+
         int 32 bit          int 32 bit          int 32 bit

    +----+----+----+----+----+----+----+----+----+----+----+----+
--> |    SEED seq. 3    |  CALLS seq. 3     |BILLIONS seq. 3    | -->
    +----+----+----+----+----+----+----+----+----+----+----+----+
         int 32 bit          int 32 bit          int 32 bit

    +----+----+----+----+----+----+----+----+----+----+----+----+
--> |    SEED seq. 4    |  CALLS seq. 4     |BILLIONS seq. 4    |
    +----+----+----+----+----+----+----+----+----+----+----+----+
         int 32 bit          int 32 bit          int 32 bit
```

## corsika-primary-wrapper
The ```corsika_primary_wrapper``` is a python 3 package to test and call the CORSIKA-primary modification.
```bash
pip install -e ./corsika_primary_wrapper
```
For editing in place you may use pip's ```-e``` option.


### How it is done:
We first set up CORSIKA manually using its own build-tool called coconut. We then save coconut's output ```config.h```.
When we want to build CORSIKA again, we use this ```config.h``` to reproduce our specific build-options.
Further, we include additional atmospheric profiles which are taken from [Konrad Bernloehr's IACT/ATMO-package](https://www.mpi-hd.mpg.de/hfm/~bernlohr/iact-atmo/).
