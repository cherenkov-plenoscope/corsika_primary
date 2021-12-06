# CORSIKA-primary

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A wrapper for the [CORSIKA](https://www.ikp.kit.edu/corsika/) simulation of air-shower initiated by cosmic-rays. Originally written by the [Karlsruhe Institute for Technology](https://www.kit.edu/)

The CORSIKA simulation is certainly one of the most advanced simulation tools in astroparticle physics. This wrapper makes the CORSIKA call thread safe and wrapps Sebastian's primary-modification for explicit control over the primary particle. The CORSIKA-primary mod and this wrapper allows you to:

- Call multiple CORSIKA instances in parallel (thread safe)
- Have explicit control over every primary particle.
- Output ALL Cherenkov-photon-bunches.

## run
```python
import corsika_primary_wrapper as cpw

steering_dict = {
    "run": {
        "run_id": 1,
        "event_id_of_first_event": 1,
        "observation_level_altitude_asl": 2300,
        "earth_magnetic_field_x_muT": 12.5,
        "earth_magnetic_field_z_muT": -25.9,
        "atmosphere_id": 10,
        "energy_range_GeV": [1.0, 20],
    },
    "primaries": [
        {
            "particle_id": 1,
            "energy_GeV": 1.32,
            "zenith_rad": 0.0,
            "azimuth_rad": 0.0,
            "depth_g_per_cm2": 0.0,
            "random_seed": 0,
        },
        {
            "particle_id": 1,
            "energy_GeV": 1.52,
            "zenith_rad": 0.1,
            "azimuth_rad": 0.2,
            "depth_g_per_cm2": 3.6,
            "random_seed": 1,
        },
        {
            "particle_id": 1,
            "energy_GeV": 11.4,
            "zenith_rad": 0.1,
            "azimuth_rad": 0.25,
            "depth_g_per_cm2": 102.2,
            "random_seed": 2,
        },
    ],
}

cpw.corsika(
    corsika_path="my/modified/corsika-75600/run/corsika75600Linux_QGSII_urqmd",
    steering_dict=steering_dict,
    output_path="my_events.tar")

```