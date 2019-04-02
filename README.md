# Installing CORSIKA for the Cherenkov-plenoscope

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Install the [KIT-CORSIKA](https://www.ikp.kit.edu/corsika/) simulation for air-showers of cosmic-rays and gamma-rays for the Cherenkov-plenoscope.
There is not one CORSIKA-program. CORSIKA is a collection of many different programs within the same source-code. To keep track of the CORSIKA's build-options, we use this installation-script to reproduce CORSIKA for the Cherenkov-plenoscope.

### Usage:
```bash
install.py --install_path ./my_corsika_build --username=<CORSIKA-username> --password=<CORSIKA-password>
```

For CORSIKA's credentials (`username` and `password`) follow the instructions on: https://www.ikp.kit.edu/corsika/index.php. Drop the CORSIKA-team an email, and express your interest in CORSIKA to learn about cosmic-rays and air-showers. They will send you an email back with the credentials. They will not spam you.

### How it is done:
We first set up CORSIKA manually using its own build-tool called coconut. We then save coconut's output ```config.h```.
When we want to build CORSIKA again, we use this ```config.h``` to reproduce our specific build-options.
Further, we include additional atmospheric profiles which are taken from [Konrad Bernloehr's IACT/ATMO-package](https://www.mpi-hd.mpg.de/hfm/~bernlohr/iact-atmo/).
