# A custom CORSIKA install

### Usage:

    custom_corsika -p install_path --username=<your corsika username> --password=<your corsika password>
    
For corsika credentials see: https://www.ikp.kit.edu/corsika/index.php

It will install corsika in you `install_path`.

### Why?
To create reproducable studies on the ACP, we need a well defined mechanism to keep track and reinstall the CORSIKA flavor we use. There is not one CORSIKA. CORSIKA is actually a collection of many different programs with in the same source code. To keep track of the CORSIKA build options we explore on our quest for the ACP simulations, we use a installation script to memorize and reproduce our CORSIKA. 

### Customization
The IACT option did not forsee instruments collecting several millions of photons. Buffers in the IACT CORSIKA Bernloehr extension need to be extended.

### Alternatives
Max N. created a Docker container to handle specific CORSIKA build flavors for e.g. the FACT IACT.§

