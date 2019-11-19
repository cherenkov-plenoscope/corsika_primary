CherenkovInOut
--------------

The chemical composition of cosmic rays at energies around the 'knee' (10^15 eV) is still a mistery. Direct Cherenkov light observations with the novel Atmospheric Cherenkov Plenoscope (ACP) might give an answer to this question.
To simulate high energy hadronic events for such a study, we need information on the mother particle and must not use the bunch thinning. 
Unfortunately the iact package EventIo reaches its limit for this task. This is why we had to come up with this custom format 'CherenkovInOut'.
The goal is to store a single photon in only 16byte (8 x int16) including information on the mother particle without any bunch thinning.