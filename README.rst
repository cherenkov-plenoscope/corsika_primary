############################
CORSIKA primary modification
############################
|BlackStyle| |BlackPackStyle| |MITLicenseBadge|

Install the `KIT-CORSIKA`_ simulation for air-showers of cosmic-rays and gamma-rays. This is based on CORSIKA-7.56 with minor modifications to gain more control over the primary particle.



The mod overcomes two limitations of vanilla CORSIKA-7.56:

- Export all Cherenkov-photons (dedicated format EventTape allows TBytes of output).

- Control every primary particle's direction, energy, type, and starting-depth.

This repository:

- Installs vanilla CORSIKA-7.56

- Installs the CORSIKA-primary-modification

- Provides a `python`-package to call and test the CORSIKA-primary-modification

*******
Install
*******
The installation has three steps.

First, you must install the python package ``corsika_primary``.

.. code-block:: bash

    pip install -e ./corsika_primary

The ``-e`` (editable) is only needed for development when you want to modify the local sources.

Second, you must build the CORSIKA executable itself. There is a script which does this in a reproducible manner for the specific use of the Cherenkov plenoscope.

Make sure you have a ``Fortran 77`` compiler. If you use the ``gfortran`` from the gnu compiler collection (gcc) it might be necessary to create an alias ``F77`` or ``f77`` for the ``gfortran``.

.. code-block:: bash

    ./corsika_primary/scripts/install.py \
        --install_path /path/to/build/corsika \
        --corsika_tar /path/to/corsika-75600.tar.gz \
        --resource_path ./corsika_primary/resources

This builds both the vanilla CORSIKA-7.56, and our CORSIKA-primary modification to the ``install_path`` named ``/path/to/build/corsika``.
The script ``./corsika_primary/scripts/install.py`` can either be provided the path ``--corsika_tar`` to the ``corsika-75600.tar.gz``, OR it can be provided with the CORSIKA credentials to download the `corsika-75600.tar.gz`` all by itself. See the parameters ``--username`` and ``--password``. However, this second option is error prone as it depends on the latest known ``URL``.
For CORSIKA's credentials (`username` and `password`), drop the `CORSIKA team`_ an email, and express your interest in cosmic-rays. They will send you the credentials.

Thrird, you must tell the python package where it can find the CORSIKA executables. This is done using a configfile ``~/.corika_primary.json`` which lives in the user's home. See the modue ``coriska_primary.configfile``.

.. code-block:: bash

    vim ~/.corika_primary.json
    {
        "corsika_primary": "/path/to/build/corsika/modified/corsika-75600/run/corsika75600Linux_QGSII_urqmd",
        "corsika_vanilla": "/path/to/build/corsika/vanilla/corsika-75600/run/corsika75600Linux_QGSII_urqmd"
    }

*******
Testing
*******
The main goal of the tests is to make sure that the CORSIKA primary mod creates the same (bit equall) output as the vanilla CORSIKA when it is called with the corresponing steering card.
The ``install.py`` always builds both the vanilla and the modified CORSIKA to allow testing for equality of both versions.
The tests need the explicit paths to the CORSIKA executables, and the ``merlict-eventio-converter``.

.. code-block:: bash

    py.test ./corsika_primary/corsika_primary/tests/
        --debug_dir /path/to/a/non/temporary/directory/for/debugging
        --corsika_vanilla_path /path/to/vanilla/corsika/executable
        --corsika_primary_path /path/to/modified/corsika/executable
        --merlict_eventio_converter /path/to/merlict_eventio_converter/executable


See all options defined in: ``./corsika_primary/corsika_primary/tests/conftest.py``

*******************
Coordinates systems
*******************

|img_frame|

CORSIKA has a mindset of particles running down in the
atmosphere towards the surface of the earth. This is, the particles have
(mostly) momentum into negative ``z`` direction and are running towards the
``xy`` plane.
Because of this, the spherical coordinates used by CORSIKA point towards the
negative ``z`` direction by default (for phi=0, theta=0).

On the other hand, astronomy has a mindset of looking up into the sky, into
positive ``z`` direction away from the ``xy`` plane.
Because of this, the spherical coordiantes used in astronomy point towards the
positive ``z`` direction by default (for azimuth=0, zenith distance=0).

CORSIKA's spherical coordinates are ``phi``-``theta``. They are used in e.g. the
input of CORSIKA and can be defined in the steering card as ``PHIP`` and
``THETAP``. Note in the figure how ``theta`` starts to open from the negative
``z`` axis.

On the other hand, astronomy's spherical coordinates are
``azimuth``-``zenith distance``. (Astronomy has many coordinate systems but to
discuss the pointing of a telescope on earth, azimuth and zenith are rather
common).
Note in the figure how ``zenith`` starts to open from the positive ``z`` axis.

See also our package on `spherical coordinates`_

*****
Usage
*****

``corsika_primary`` is a python package to test and call the CORSIKA-primary modification.
The wrapper can call CORSIKA thread safe to run multiple instances in parallel. Also it provies a simplified interface to steer the simulation with a single dictionary.

.. code-block:: python

    import corsika_primary

    corsika_primary.corsika_primary(
        steering_dict=STEERING_DICT,
        output_path="/path/to/my/output/run.tar"
    )

This modification allows you to control the:

.. code-block:: python

    {
        "particle_id": 1,
        "energy_GeV": 1.32,
        "theta_rad": 0.0,
        "phi_rad": 0.0,
        "depth_g_per_cm2": 0.0,
    }


of each primary particle in a run. When starting CORSIKA, you provide a steering card which specifies all properties which can not be changed over a CORSIKA run, and a second additional file which lists all the properties of the primary particles.

Steering dictionary
-------------------
A CORSIKA run is fully described by a steering dictionary:

.. code-block:: python

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
                "theta_rad": 0.0,
                "phi_rad": 0.0,
                "depth_g_per_cm2": 0.0,
            },
            {
                "particle_id": 3,
                "energy_GeV": 1.52,
                "theta_rad": 0.1,
                "phi_rad": 0.2,
                "depth_g_per_cm2": 3.6,
            },
        ],
    }

This run will create two showers. One gamma-ray ``particle_id=1``, and one electron ``particle_id=3``. The gamma-ray will start at CORSIKA's edge of the atmosphere at a depth of 0.0 g/cm^{-2} corresponding to ~115km a.s.l., but the electron will start lower in tha atmosphere at a depth of 3.6 g/cm^{-2}.


EventTape
---------
Our coriska_primary mod always outputs all Cherenkov-photons.
The photon's coordinate-frame is w.r.t the observation-level ``OBSLEV``, and the primary particle always starts at ``x=0, y=0``. There is no scattering of the core position. This mod writes a tape-archive ``.tar``.

Tape-archive:

.. code-block::

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

Both ``RUNH.float32``, ``rrrrrrrrr/eeeeeeeee/EVTH.float32``, ``rrrrrrrrr/eeeeeeeee/EVTE.float32``, and ``rrrrrrrrr/RUNE.float32`` are the classic 273-float32-binary-blocks. And the ``rrrrrrrrr/eeeeeeeee/bbbbbbbbb.cer.x8.float32`` are the photon-bunches with eight float32s per bunch.

Photon-bunch:

.. code-block::

        +----+----+----+----+----+----+----+----+
        |      x / cm       |      y / cm       | -->
        +----+----+----+----+----+----+----+----+
             float 32            float 32

        +----+----+----+----+----+----+----+----+
    --> |      ux / 1       |      vy / 1       | -->
        +----+----+----+----+----+----+----+----+
             float 32            float 32

        +----+----+----+----+----+----+----+----+
    --> |     time / ns     |  z-emission / cm  | -->
        +----+----+----+----+----+----+----+----+
             float 32            float 32

        +----+----+----+----+----+----+----+----+
    --> |  bunch-size / 1   |  wavelength / nm  |
        +----+----+----+----+----+----+----+----+
             float 32            float 32



The std-error is expected to be empty. You can also manually provide a ``corsika_path`` to the CORSIKA executable. Otherwise ``corsika_primary`` will look up the path from its configfile.

Calling the CORSIKA executable directly without the ``corsika_primary`` package
===============================================================================
You need to provide a steering card to CORSIKA's sdtin and you need to write a primary file (``PRIMFIL``) into CORSIKA's run directory.

Example steering card
---------------------

.. code-block::

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

Note the abscence of steering for properties which can be changed from event to event. Such as ``PHIP``, ``THETAP``, ``CSCATT``, and ``ESLOPE``. Also the ``SEED`` s are missing. Such properties are now explicitly defined for each primary particle seperately in a dedicated file located at the path defined in ``PRMFIL``.


Primary-particle-block
----------------------
The ``PRMFIL`` is a binary file. It contains a series of blocks. Each block describes a primary particle.

.. code-block::

        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
        |             particle id               |            energy in GeV              | -->
        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
                       float 64 bit                            float 64 bit

        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
    --> |             theta in rad              |     phi rel. to mag. north in rad     | -->
        +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
                       float 64 bit                            float 64 bit

        +----+----+----+----+----+----+----+----+
    --> |      starting depth in g cm^{-2}      |  -->
        +----+----+----+----+----+----+----+----+
                       float 64 bit

The ``PRMFIL`` contains ``NSHOW`` of such blocks.



.. _`KIT-CORSIKA`: https://www.ikp.kit.edu/corsika/

.. _`CORSIKA team`: https://www.ikp.kit.edu/corsika/index.php

.. _`spherical coordinates`: https://github.com/cherenkov-plenoscope/spherical_coordinates

.. |BlackStyle| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. |BlackPackStyle| image:: https://img.shields.io/badge/pack%20style-black-000000.svg
    :target: https://github.com/cherenkov-plenoscope/black_pack

.. |MITLicenseBadge| image:: https://img.shields.io/badge/License-GPL%20v3-blue.svg
    :target: https://opensource.org/licenses/MIT

.. |img_frame| image:: https://github.com/cherenkov-plenoscope/spherical_coordinates/blob/main/readme/frame.png?raw=True
    :target: https://github.com/cherenkov-plenoscope/spherical_coordinates
