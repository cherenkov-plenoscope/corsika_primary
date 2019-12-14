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
This mod allows you to control the:

- particle (gamma, electron, proton...)
- energy
- direction (zenith, and azimuth)
- starting depth in atmosphere
- random-seed

of each primary particle. When starting CORSIKA, you provide a steering-card which specifies all properties which can not be changed over a CORSIKA-run, and a second additional file which lists all the properties of the primary particles.

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

### Primary-particle-block
The ```PRMFIL``` is a binary file. It contains a series of blocks. Each block describes a primary particle.
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
The ```PRMFIL``` contains ```NSHOW``` of such blocks.

### Cherenkov-output
This mod always outputs ALL Cherenkov-photons emitted in an air-shower.
The photon's coordinate-frame is with respect to the observation-level ```OBSLEV```, and the primary particle always starts at ```x=0, y=0```. There is no scattering of the core-position.
This mod writes a tape-archive ```.tar```. Each file in the tape-archive contains the same payload as the containers in the event-io-format. The tape-archive contains no folders, and can be streamed just like event-io.

Tape-archive:
```
   |
   |--> runh.float32
   |--> 000000001.evth.float32
   |--> 000000001.cherenkov_bunches.Nx8_float32
   |--> 000000002.evth.float32
   |--> 000000002.cherenkov_bunches.Nx8_float32
   .
   .
   .
   |-->     NSHOW.evth.float32
   |-->     NSHOW.cherenkov_bunches.Nx8_float32
```
Both ```runh.float32``` and ```XXXXXXXXX.evth.float32``` are the classic 273 float32 binary blocks. And the ```XXXXXXXXX.cherenkov_bunches.Nx8_float32``` is the classic binary block of ```N``` photon-bunches of 8 float32.

Photon-bunch:
```
    +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    |      x / cm       |      y / cm       |      cx / rad     |      cy / rad     | -->
    +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
         float 32            float 32            float 32            float 32

    +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
--> |     time / ns     |  z-emission / cm  |  bunch-size / 1   |  wavelength / nm  |
    +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
         float 32            float 32            float 32            float 32
```

## corsika-primary-wrapper
The ```corsika_primary_wrapper``` is a python-3 package to test and call the CORSIKA-primary-modification. 
The wrapper can call CORSIKA thread safe to run multiple instances in parallel. Also it provies a simplified interface to steer the simulation with a single dictionary. It then creates the CORSIKA steering-card, and the additional ```PRMFIL```, and feeds both into CORSIKA.

### install 
```bash
pip install -e ./corsika_primary_wrapper
```
I use pip's ```-e``` option to modify the wrapper in place.

## Steering-dictionary
A CORSIKA-run is fully described in steering-dictionary. The example shows all possible options.

```python
EXAMPLE_STEERING_DICT = {
    "run": {
        "run_id": 1,
        "event_id_of_first_event": 1,
        "observation_level_altitude_asl": 2300,
        "earth_magnetic_field_x_muT": 12.5,
        "earth_magnetic_field_z_muT": -25.9,
        "atmosphere_id": 10,
    },
    "primaries": [
        {
            "particle_id": 1,
            "energy_GeV": 1.32,
            "zenith_rad": 0.0,
            "azimuth_rad": 0.0,
            "depth_g_per_cm2": 0.0,
            "random_seed": [
                {"SEED": 0, "CALLS": 0, "BILLIONS": 0},
                {"SEED": 1, "CALLS": 0, "BILLIONS": 0},
                {"SEED": 2, "CALLS": 0, "BILLIONS": 0},
                {"SEED": 3, "CALLS": 0, "BILLIONS": 0}
            ]
        },
        {
            "particle_id": 3,
            "energy_GeV": 1.52,
            "zenith_rad": 0.1,
            "azimuth_rad": 0.2,
            "depth_g_per_cm2": 3.6,
            "random_seed": [
                {"SEED": 2, "CALLS": 0, "BILLIONS": 0},
                {"SEED": 3, "CALLS": 0, "BILLIONS": 0},
                {"SEED": 4, "CALLS": 0, "BILLIONS": 0},
                {"SEED": 5, "CALLS": 0, "BILLIONS": 0}
            ]
        },
    ],
}
```
This run will create two showers. Ine gamma-ray ```particle_id=1```, and one electron ```particle_id=3```. The gamma-ray will start at CORSIKA's edge of the atmosphere at a depth of 0.0 g/cm^{-2} corresponding to ~115km a.s.l., but the electron will start lower in tha atmosphere at a depth of 3.6 g/cm^{-2}.
