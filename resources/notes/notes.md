exploring corsika75600Linux_QGSII_urqmd_compilefile.f


C  LOOP OVER SHOWERS
====================


PRMPAR
------
The primary particle with its user defined properties


PRMPAR(0): particle type
(# 11652 "corsika.F")
PRMPAR(1): energy/GeV

PRMPAR(2) = COS( THETAP )

PRMPAR(3) = SIN( THETAP ) * COS( PHIP )

PRMPAR(4) = SIN( THETAP ) * SIN( PHIP )

PRMPAR(5) = HEIGH( THICK0 )
PRMPAR(5): starting height/cm
(# 2154 "corsika.F", equal EVTH(158))

PRMPAR(6): T time
PRMPAR(7): X
PRMPAR(8): Y
(C  RESET T, X AND Y COORDINATES OF PRIMARY PARTICLE)

PRMPAR(9): CHI


CURPAR
------
The current particle in AAMAIN.

