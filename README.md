# CORSIKA install

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Installs the KIT CORSIKA cosmic-ray air-shower simulation with the settings used for the Atmospheric Cherenkov Plenoscope (ACP). To create reproducable studies on the ACP, we need a well defined procedure to reinstall the CORSIKA flavor we use. There is not one CORSIKA program. CORSIKA is actually a collection of many different programs within the same source code. To keep track of the CORSIKA build options we explore on our quest with the ACP, we use this installation script to memorize and reproduce our CORSIKA flavor. 

### Usage:
```bash
acp_corsika_install -p install_path --username=<your corsika username> --password=<your corsika password>
```

It will install CORSIKA to your `install_path`.

For corsika credentials (`username` and `password`) follow the instructions on: https://www.ikp.kit.edu/corsika/index.php. You have to drop the CORSIKA team an email and say that you want to play around with CORSIKA to learn about cosmic-rays and air-showers. They will send you an email back with the credentials. They will not spam you.

