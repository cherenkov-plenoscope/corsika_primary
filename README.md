# CORSIKA install

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Installs the KIT-CORSIKA simulation for air-showers of cosmic-rays and gamma-rays for the Atmospheric-Cherenkov-Plenoscope (ACP). To create reproducable studies on the ACP, we have this well defined installation-script for CORSIKA.

There is not one CORSIKA program. CORSIKA is actually a collection of many different programs within the same source-code. To keep track of the CORSIKA build-options, we use this installation-script to memorize and reproduce CORSIKA for the ACP.

### Usage:
```bash
install.py --install_path ./my_corsika_build --username=<CORSIKA-username> --password=<CORSIKA-password>
```

For the credentials of CORSIKA credentials (`username` and `password`) follow the instructions on: https://www.ikp.kit.edu/corsika/index.php. Go and drop the CORSIKA-team an email, and say that you want to explore CORSIKA to learn about cosmic-rays and air-showers. They will send you an email back with the credentials. They will not spam you.
