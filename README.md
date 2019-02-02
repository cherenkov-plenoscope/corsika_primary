# Installing CORSIKA for the Cherenkov-plenoscope

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Installs the KIT-CORSIKA simulation for air-showers of cosmic-rays and gamma-rays for the Cherenkov-plenoscope. To create reproducable studies, we use this well defined installation-script for CORSIKA.

There is not one CORSIKA program. CORSIKA is actually a collection of many different programs within the same source-code. To keep track of the CORSIKA-build-options, we use this installation-script to memorize and reproduce CORSIKA for the Cherenkov-plenoscope.

### Usage:
```bash
install.py --install_path ./my_corsika_build --username=<CORSIKA-username> --password=<CORSIKA-password>
```

For CORSIKA's credentials (`username` and `password`) follow the instructions on: https://www.ikp.kit.edu/corsika/index.php. Drop the CORSIKA-team an email, and express your interest in CORSIKA to learn about cosmic-rays and air-showers. They will send you an email back with the credentials. They will not spam you.
