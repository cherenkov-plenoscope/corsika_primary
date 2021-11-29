# Installing CORSIKA for the Cherenkov-plenoscope

<p align="center">
<img
    alt="License: GPL v3"
    src="https://img.shields.io/badge/License-GPL%20v3-blue.svg"
>
<img
    alt="Code style: black"
    src="https://img.shields.io/badge/code%20style-black-000000.svg"
>
</p>

Install the [KIT-CORSIKA](https://www.ikp.kit.edu/corsika/) simulation for air-showers of cosmic-rays and gamma-rays for the Cherenkov-plenoscope. This is based on CORSIKA 7.56 with minor modifications to gain more control over the primary particle. 
This repository contains:
- The installer for the CORSIKA-primary-modification
- A python-3 wrapper to call and test the CORSIKA-primary-modification

## CORSIKA-primary-modification

### Install
```bash
./corsika_install/install.py --install_path corsika --username=<CORSIKA-username> --password=<CORSIKA-password> --resource_path ./corsika_install/resources
```
This installs both the original CORSIKA 7.56, and our CORSIKA-primary-modification to the ```install_path```.
For CORSIKA's credentials (`username` and `password`), drop the [CORSIKA-team](https://www.ikp.kit.edu/corsika/index.php) an email, and express your interest in cosmic-rays. They will send you the credentials.

This modification allows you to control the:
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
Note the abscence of steering for properties which can be changed from event to event. Such as ```PHIP```, ```THETAP```, ```CSCATT```, and ```ESLOPE```. Also the ```SEED```s are missing. Such properties are now explicitly defined for each primary particle seperately in a dedicated file located at the path defined in ```PRMFIL```.

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
This mod always outputs all Cherenkov-photons emitted in an air-shower.
The photon's coordinate-frame is with respect to the observation-level ```OBSLEV```, and the primary particle always starts at ```x=0, y=0```. There is no scattering of the core-position. There is no concept for multiple telescopes and detector-spheres as it is in Konrad Bernloehr's IACT-packege. This mod writes a tape-archive ```.tar```. Each file in the tape-archive contains the same payload as the containers in the event-io-format in the IACT-packege. Only difference: This mod outputs photons in CORSIKA's coordinate-frame, i.e. relative to the observation-level, and the IACT-packege outputs photons in the coordinate-frames of predefined telescopes (detecor-spheres).
The tape-archive contains no folders, and can be streamed just like event-io.

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
The wrapper can call CORSIKA thread safe to run multiple instances in parallel. Also it provies a simplified interface to steer the simulation with a single dictionary.

### Install
```bash
pip install -e ./corsika_primary_wrapper
```
I use pip's ```-e``` option to modify the wrapper in place.

### Steering-dictionary
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
        "energy_range_GeV": [1.0, 2.0],
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
This run will create two showers. One gamma-ray ```particle_id=1```, and one electron ```particle_id=3```. The gamma-ray will start at CORSIKA's edge of the atmosphere at a depth of 0.0 g/cm^{-2} corresponding to ~115km a.s.l., but the electron will start lower in tha atmosphere at a depth of 3.6 g/cm^{-2}.

### Call
In python do:
```python
import corsika_primary_wrapper as cpw

cpw.corsika_primary(
    corsika_path="/path/to/my/modified/corsika-75600/run/corsika75600Linux_QGSII_urqmd",
    steering_dict=EXAMPLE_STEERING_DICT,
    output_path="/path/to/my/output/run.tar")
```
The std-out, and std-error of CORSIKA are written into text-files next to ```output_path``` with postfixes.
The std-error is expected to be empty. The ```corsika_path``` must be the executable within its "run"-directory.
The call will NOT write to the "run"-directory in ```corsika_path```. Instead the "run"-directory is copied to a temporary directory from which the CORSIKA call is made. This allows thread safety.

### Test
The installer installs both the original and the modified CORSIKA to allow testing for equality of both versions with input parameters which are accesible to both versions.

To run the tests, you have to explicitly provide the paths to the corsika executables, and the merlict-eventio-converter. There are defaults which allow to call the tests in the Cherenkov-plenoscope's starter-kit-directory.

```bash
py.test ./corsika_primary_wrapper/corsika_primary_wrapper/tests/
    --corsika_path /path/to/original/corsika/executable
    --corsika_primary_path /path/to/modified/corsika/executable
    --merlict_eventio_converter /path/to/merlict_eventio_converter/executable
```
Thers is also an option ```--non_temporary_path``` which will write the files created during the tests to the path specified in ```non_temporary_path``` to allow debugging and inspection.

See all options defined in: ```./corsika_primary_wrapper/corsika_primary_wrapper/tests/conftest.py```

### Codestyle
```bash
black -l 79 .
```

