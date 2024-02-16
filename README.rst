############################
CORSIKA primary modification
############################

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

Install the [KIT-CORSIKA](https://www.ikp.kit.edu/corsika/) simulation for air-showers of cosmic-rays and gamma-rays. This is based on CORSIKA-7.56 with minor modifications to gain more control over the primary particle.

The mod overcomes two limitations of vanilla CORSIKA-7.56:
- Export all Cherenkov-photons (dedicated format EventTape allows TBytes of output).
- Control every primary particle's direction, energy, type, and starting-depth.

This repository:
- Installs vanilla CORSIKA-7.56
- Installs the CORSIKA-primary-modification
- Provides a `python`-package to call and test the CORSIKA-primary-modification

## CORSIKA-primary-modification

### Install
```bash
./corsika_primary/scripts/install.py --install_path corsika --username=<CORSIKA-username> --password=<CORSIKA-password> --resource_path ./corsika_install/resources
```
This installs both the vanilla CORSIKA-7.56, and our CORSIKA-primary-modification to the ```install_path```.
For CORSIKA's credentials (`username` and `password`), drop the [CORSIKA-team](https://www.ikp.kit.edu/corsika/index.php) an email, and express your interest in cosmic-rays. They will send you the credentials.

This modification allows you to control the:
```python
{
    "particle_id": 1,
    "energy_GeV": 1.32,
    "zenith_rad": 0.0,
    "azimuth_rad": 0.0,
    "depth_g_per_cm2": 0.0,
}
```
of each primary particle. When starting CORSIKA, you provide a steering-card which specifies all properties which can not be changed over a CORSIKA-run, and a second additional file which lists all the properties of the primary particles.

### Steering-dictionary
A CORSIKA-run is fully described by a steering-dictionary:

```python
STEERING_DICT = {
    "run": {
        "run_id": 1,
        "event_id_of_first_event": 1,
        "observation_level_altitude_asl": 2300,
        "earth_magnetic_field_x_muT": 12.5,
        "earth_magnetic_field_z_muT": -25.9,
        "atmosphere_id": 10,
        "energy_range": {"start_GeV": 1.0, "stop_GeV": 2.0},
        "random_seed": [
            {"SEED": 0, "CALLS": 0, "BILLIONS": 0},
            {"SEED": 1, "CALLS": 0, "BILLIONS": 0},
            {"SEED": 2, "CALLS": 0, "BILLIONS": 0},
            {"SEED": 3, "CALLS": 0, "BILLIONS": 0}
        ]
    },
    "primaries": [
        {
            "particle_id": 1,
            "energy_GeV": 1.32,
            "zenith_rad": 0.0,
            "azimuth_rad": 0.0,
            "depth_g_per_cm2": 0.0,
        },
        {
            "particle_id": 3,
            "energy_GeV": 1.52,
            "zenith_rad": 0.1,
            "azimuth_rad": 0.2,
            "depth_g_per_cm2": 3.6,
        },
    ],
}
```
This run will create two showers. One gamma-ray ```particle_id=1```, and one electron ```particle_id=3```. The gamma-ray will start at CORSIKA's edge of the atmosphere at a depth of 0.0 g/cm^{-2} corresponding to ~115km a.s.l., but the electron will start lower in tha atmosphere at a depth of 3.6 g/cm^{-2}.


### EventTape
Our primary-mod always outputs all Cherenkov-photons.
The photon's coordinate-frame is w.r.t the observation-level ```OBSLEV```, and the primary particle always starts at ```x=0, y=0```. There is no scattering of the core-position. This mod writes a tape-archive ```.tar```.

Tape-archive:
```
   |
   |--> 000000001/RUNH.float32
   |--> 000000001/000000001/EVTH.float32
   |--> 000000001/000000001/000000001.cer.x8.float32
   |--> 000000001/000000001/000000002.cer.x8.float32
   |--> 000000001/000000001/EVTE.float32
   |--> 000000001/000000002/EVTH.float32
   |--> 000000001/000000002/000000001.cer.x8.float32
   |--> 000000001/000000002/000000002.cer.x8.float32
   |--> 000000001/000000002/000000003.cer.x8.float32
   .
   .
   .
   |--> 000000001/000000010/000000005.cer.x8.float32
   |--> 000000001/000000010/000000006.cer.x8.float32
   |--> 000000001/000000010/EVTE.float32
   |--> 000000001/RUNE.float32
```

Both ```RUNH.float32```, ```rrrrrrrrr/eeeeeeeee/EVTH.float32```, ```rrrrrrrrr/eeeeeeeee/EVTE.float32```, and ```rrrrrrrrr/RUNE.float32``` are the classic 273-float32-binary-blocks. And the ```rrrrrrrrr/eeeeeeeee/bbbbbbbbb.cer.x8.float32``` are the photon-bunches with eight float32s per bunch.

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

## corsika-primary
The ```corsika_primary``` is a `python` package to test and call the CORSIKA-primary-modification.
The wrapper can call CORSIKA thread safe to run multiple instances in parallel. Also it provies a simplified interface to steer the simulation with a single dictionary.

### Install
```bash
pip install -e ./corsika_primary
```
Use pip's ```-e``` option if you want to modify the package in place.


### Call
In python do:
```python
import corsika_primary as cpw

cpw.corsika_primary(
    corsika_path="/path/to/my/modified/corsika-75600/run/corsika75600Linux_QGSII_urqmd",
    steering_dict=STEERING_DICT,
    output_path="/path/to/my/output/run.tar")
```
The std-error is expected to be empty. The ```corsika_path``` must be the executable within its "run"-directory.


### Test
The installer installs both the vanilla and the modified CORSIKA to allow testing for equality of both versions.
The tests need the explicit paths to the corsika executables, and the merlict-eventio-converter.

```bash
py.test ./corsika_primary/corsika_primary/tests/
    --debug_dir /path/to/a/non/temporary/directory/for/debugging
    --corsika_vanilla_path /path/to/vanilla/corsika/executable
    --corsika_primary_path /path/to/modified/corsika/executable
    --merlict_eventio_converter /path/to/merlict_eventio_converter/executable
```

See all options defined in: ```./corsika_primary/corsika_primary/tests/conftest.py```


### Example steering-card
```
RUNNR 1
EVTNR 1
PRMPAR 1 <-- unused
ERANGE 1. 10.
OBSLEV 2300e2
MAGNET 12.5 -25.9
SEED 1 0 0
SEED 2 0 0
SEED 3 0 0
SEED 4 0 0
MAXPRT 1
PAROUT F F
ATMOSPHERE 10 T
CWAVLG 250 700
CERQEF F T F
CERSIZ 1.
CERFIL F
TSTART T
NSHOW 1000
TELFIL /some/path/different_starting_depths.tar
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
```
The ```PRMFIL``` contains ```NSHOW``` of such blocks.


### Codestyle
```bash
black -l 79 .
```

