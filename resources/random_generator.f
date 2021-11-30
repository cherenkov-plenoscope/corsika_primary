C --------------/CRRANDPA/-----------------------
C  RD(3000)    = ARRAY (DOUBLE PRECISION) FOR RANDOM NUMBERS
C  FAC         = VARIABLE OF SUBROUT. RANNOR
C  U1          = VARIABLE OF SUBROUT. RANNOR
C  U2          = VARIABLE OF SUBROUT. RANNOR
C  NSEQ        = # OF RANDOM GENERATOR SEQUENCE
C  ISEED(.,.)  = RANDOM GENERATOR SEED
C  KNOR        = FLAG TO STEER GENERATION OF NORMAL DISTRIBUTED RANDOMS
C
C --------------/CRRANMA3/-----------------------
C  KSEQ        = PARAMETER DEFINING MAX. NUMBER OF INDEPENDENT SEQUENCES
C  CD          = STARTING NUMBER FOR RANDOM GENERATOR
C  CINT        = STARTING NUMBER FOR RANDOM GENERATOR
C  CM          = STARTING NUMBER FOR RANDOM GENERATOR
C  TWOM24      = 2**-24 (MANTISSA SINGLE PRECISION)
C  TWOM48      = 2**-48 (MANTISSA DOUBLE PRECISION)
C  MODCNS      = MODULUS (NOTOT * MODCNS = NTOT2) FOR RANDOM GENERATOR
C
C --------------/CRRANMA4/-----------------------
C  C()         = ARRAY(KSEQ) FOR RANDOM GENERATOR
C  U()         = ARRAY(97,KSEQ) FOR RANDOM GENERATOR
C  IJKL()      = ARRAY(KSEQ) FOR RANDOM GENERATOR
C  I97()       = ARRAY(KSEQ) FOR RANDOM GENERATOR
C  J97()       = ARRAY(KSEQ) FOR RANDOM GENERATOR
C  NTOT()      = ARRAY(KSEQ) FOR RANDOM GENERATOR
C  NTOT2()     = ARRAY(KSEQ) FOR RANDOM GENERATOR
C  JSEQ        = ACTUAL SEQUENCE NUMBER
C  UNI         = FINAL RANDOM NUMBER
C

*-- Author :    D. HECK IK FZK KARLSRUHE   17/03/2003
C=======================================================================

      SUBROUTINE RMMAQD( ISEED,ISEQ,CHOPT )

C-----------------------------------------------------------------------
C  SUBROUTINE FOR INITIALIZATION OF RMMARD
C  THESE ROUTINE RMMAQD IS A MODIFIED VERSION OF ROUTINE RMMAQ FROM
C  THE CERN LIBRARIES. DESCRIPTION OF ALGORITHM SEE:
C   http://wwwasdoc.web.cern.ch/wwwasdoc/cernlib.html (v113)
C  FURTHER DETAILS SEE SUBR. RMMARD
C  ARGUMENTS:
C   ISEED  = SEED TO INITIALIZE A SEQUENCE (3 INTEGERS)
C   ISEQ   = # OF RANDOM SEQUENCE
C   CHOPT  = CHARACTER TO STEER INITIALIZE OPTIONS
C            ' '  SEQUENCE 1 IS INITIALIZED WITH DEFAULT SEED
C            'R'  GET STATUS OF GENERATOR BY 3 SEEDS
C            'RV' COMPLETE STATUS OF GENERATOR IS DUMPED (103 WORDS)
C            'S'  SET RANDOM GENERATOR BY 3 SEEDS
C            'SV' SET RANDOM GENERATOR BY ARRAY WITH 103 WORDS
C            'V'  VECTOR OPTION SET/GET STATUS USING 103 WORDS
C-----------------------------------------------------------------------

      IMPLICIT NONE

      INTEGER          KSEQ

      PARAMETER        (KSEQ = 8)

      COMMON /CRRANMA3/CD,CINT,CM,TWOM24,TWOM48,MODCNS
      DOUBLE PRECISION CD,CINT,CM,TWOM24,TWOM48
      INTEGER          MODCNS

      COMMON /CRRANMA4/C,U,IJKL,I97,J97,NTOT,NTOT2,JSEQ
      DOUBLE PRECISION C(KSEQ),U(97,KSEQ),UNI
      INTEGER          IJKL(KSEQ),I97(KSEQ),J97(KSEQ),
     *                 NTOT(KSEQ),NTOT2(KSEQ),JSEQ

      DOUBLE PRECISION CC,S,T,UU(97)
      INTEGER          ISEED(3),I,IDUM,II,II97,IJ,IJ97,IORNDM,
     *                 ISEQ,J,JJ,K,KL,L,LOOP2,M,NITER
      CHARACTER        CHOPT*(*), CCHOPT*12
      LOGICAL          FIRST
      SAVE
      DATA             FIRST / .TRUE. /, IORNDM / 11 /, JSEQ / 1 /
C-----------------------------------------------------------------------

      IF ( FIRST ) THEN
        TWOM24 = 2.D0**(-24)
        TWOM48 = 2.D0**(-48)
        CD     = 7654321.D0*TWOM24
        CM     = 16777213.D0*TWOM24
        CINT   = 362436.D0*TWOM24
        MODCNS = 1000000000
        FIRST  = .FALSE.
      ENDIF

      CCHOPT = CHOPT

      IF     ( INDEX(CCHOPT,'S') .NE. 0 ) THEN
        IF ( ISEQ .GT. 0  .AND.  ISEQ .LE. KSEQ ) JSEQ = ISEQ
        IF ( INDEX(CCHOPT,'V') .NE. 0 ) THEN
          READ(IORNDM,'(3Z8)') IJKL(JSEQ),NTOT(JSEQ),NTOT2(JSEQ)
          READ(IORNDM,'(2Z8,Z16)') I97(JSEQ),J97(JSEQ),C(JSEQ)
          READ(IORNDM,'(24(4Z16,/),Z16)') U
          IJ = IJKL(JSEQ)/30082
          KL = IJKL(JSEQ) - 30082 * IJ
          I  = MOD(IJ/177, 177) + 2
          J  = MOD(IJ, 177)     + 2
          K  = MOD(KL/169, 178) + 1
          L  = MOD(KL, 169)
          CD =  7654321.D0 * TWOM24
          CM = 16777213.D0 * TWOM24
        ELSE
          IJKL(JSEQ)  = ISEED(1)
          NTOT(JSEQ)  = ISEED(2)
          NTOT2(JSEQ) = ISEED(3)
          IJ = IJKL(JSEQ) / 30082
          KL = IJKL(JSEQ) - 30082*IJ
          I  = MOD(IJ/177, 177) + 2
          J  = MOD(IJ, 177)     + 2
          K  = MOD(KL/169, 178) + 1
          L  = MOD(KL, 169)
          DO  II = 1, 97
            S = 0.D0
            T = 0.5D0
            DO  JJ = 1, 48
              M = MOD(MOD(I*J,179)*K, 179)
              I = J
              J = K
              K = M
              L = MOD(53*L+1, 169)
              IF ( MOD(L*M,64) .GE. 32 ) S = S + T
              T = 0.5D0 * T
            ENDDO
            UU(II) = S
          ENDDO
          CC    = CINT
          II97  = 97
          IJ97  = 33
C  COMPLETE INITIALIZATION BY SKIPPING (NTOT2*MODCNS+NTOT) RANDOMNUMBERS
          NITER = MODCNS
          DO  LOOP2 = 1, NTOT2(JSEQ)+1
            IF ( LOOP2 .GT. NTOT2(JSEQ) ) NITER = NTOT(JSEQ)
            DO  IDUM = 1, NITER
              UNI = UU(II97) - UU(IJ97)
              IF ( UNI .LT. 0.D0 ) UNI = UNI + 1.D0
              UU(II97) = UNI
              II97     = II97 - 1
              IF ( II97 .EQ. 0 ) II97 = 97
              IJ97     = IJ97 - 1
              IF ( IJ97 .EQ. 0 ) IJ97 = 97
              CC       = CC - CD
              IF ( CC .LT. 0.D0 ) CC  = CC + CM
            ENDDO
          ENDDO
          I97(JSEQ) = II97
          J97(JSEQ) = IJ97
          C(JSEQ)   = CC
          DO  JJ = 1, 97
            U(JJ,JSEQ) = UU(JJ)
          ENDDO
        ENDIF
      ELSEIF ( INDEX(CCHOPT,'R') .NE. 0 ) THEN
        IF ( ISEQ .GT. 0 ) THEN
          JSEQ = ISEQ
        ELSE
          ISEQ = JSEQ
        ENDIF
        IF ( INDEX(CCHOPT,'V') .NE. 0 ) THEN
          WRITE(IORNDM,'(3Z8)') IJKL(JSEQ),NTOT(JSEQ),NTOT2(JSEQ)
          WRITE(IORNDM,'(2Z8,Z16)') I97(JSEQ),J97(JSEQ),C(JSEQ)
          WRITE(IORNDM,'(24(4Z16,/),Z16)') U
        ELSE
          ISEED(1) = IJKL(JSEQ)
          ISEED(2) = NTOT(JSEQ)
          ISEED(3) = NTOT2(JSEQ)
        ENDIF
      ENDIF

      RETURN
      END

*-- Author :    D. HECK IK FZK KARLSRUHE   17/03/2003
C=======================================================================

      SUBROUTINE RMMARD( RVEC,LENV,ISEQ )

C-----------------------------------------------------------------------
C  R(ANDO)M (NUMBER GENERATOR OF) MAR(SAGLIA TYPE) D(OUBLE PRECISION)
C
C  THESE ROUTINES (RMMARD,RMMAQD) ARE MODIFIED VERSIONS OF ROUTINES
C  FROM THE CERN LIBRARIES. DESCRIPTION OF ALGORITHM SEE:
C   http://wwwasdoc.web.cern.ch/wwwasdoc/cernlib.html (v113)
C  IT HAS BEEN CHECKED THAT RESULTS ARE BIT-IDENTICAL WITH CERN
C  DOUBLE PRECISION RANDOM NUMBER GENERATOR RMM48, DESCRIBED IN
C   http://wwwasdoc.web.cern.ch/wwwasdoc/cernlib.html (v116)
C  ARGUMENTS:
C   RVEC   = DOUBLE PREC. VECTOR FIELD TO BE FILLED WITH RANDOM NUMBERS
C   LENV   = LENGTH OF VECTOR (# OF RANDNUMBERS TO BE GENERATED)
C   ISEQ   = # OF RANDOM SEQUENCE
C
C  VERSION OF D. HECK FOR DOUBLE PRECISION RANDOM NUMBERS.
C-----------------------------------------------------------------------

      IMPLICIT NONE

      INTEGER          KSEQ

      PARAMETER        (KSEQ = 8)

      COMMON /CRRANMA3/CD,CINT,CM,TWOM24,TWOM48,MODCNS
      DOUBLE PRECISION CD,CINT,CM,TWOM24,TWOM48
      INTEGER          MODCNS

      COMMON /CRRANMA4/C,U,IJKL,I97,J97,NTOT,NTOT2,JSEQ
      DOUBLE PRECISION C(KSEQ),U(97,KSEQ),UNI
      INTEGER          IJKL(KSEQ),I97(KSEQ),J97(KSEQ),
     *                 NTOT(KSEQ),NTOT2(KSEQ),JSEQ

      DOUBLE PRECISION RVEC(*)
      INTEGER          ISEQ,IVEC,LENV
      SAVE
C-----------------------------------------------------------------------

      IF ( ISEQ .GT. 0  .AND.  ISEQ .LE. KSEQ ) JSEQ = ISEQ

      DO  IVEC = 1, LENV
        UNI = U(I97(JSEQ),JSEQ) - U(J97(JSEQ),JSEQ)
        IF ( UNI .LT. 0.D0 ) UNI = UNI + 1.D0
        U(I97(JSEQ),JSEQ) = UNI
        I97(JSEQ)  = I97(JSEQ) - 1
        IF ( I97(JSEQ) .EQ. 0 ) I97(JSEQ) = 97
        J97(JSEQ)  = J97(JSEQ) - 1
        IF ( J97(JSEQ) .EQ. 0 ) J97(JSEQ) = 97
        C(JSEQ)    = C(JSEQ) - CD
        IF ( C(JSEQ) .LT. 0.D0 ) C(JSEQ)  = C(JSEQ) + CM
        UNI        = UNI - C(JSEQ)
        IF ( UNI .LT. 0.D0 ) UNI = UNI + 1.D0
C  AN EXACT ZERO HERE IS VERY UNLIKELY, BUT LET''S BE SAFE.
        IF ( UNI .EQ. 0.D0 ) UNI = TWOM48
        RVEC(IVEC) = UNI
      ENDDO

      NTOT(JSEQ) = NTOT(JSEQ) + LENV
      IF ( NTOT(JSEQ) .GE. MODCNS )  THEN
        NTOT2(JSEQ) = NTOT2(JSEQ) + 1
        NTOT(JSEQ)  = NTOT(JSEQ) - MODCNS
      ENDIF

      RETURN
      END


      DOUBLE PRECISION FUNCTION RANNOR( A,B )

C-----------------------------------------------------------------------
C  RAN(DOM NUMBER) NOR(MALLY DISTRIBUTED)
C
C  GENERATES NORMAL DISTRIBUTED RANDOM NUMBER
C  DELIVERS 2 UNCORRELATED RANDOM NUMBERS,
C  THEREFORE RANDOM CALLS ARE ONLY NECESSARY EVERY SECOND TIME.
C  REFERENCE : NUMERICAL RECIPES, W.H. PRESS ET AL.,
C              CAMBRIDGE UNIVERSITY PRESS, 1992  ISBN 0 521 43064 X
C  THIS FUNCTION IS CALLED FROM HDPM, LEADDF, PARRAP, QGSTOR,
C  UPDATE, AND VAPOR.
C  ARGUMENTS:
C   A      = MEAN VALUE
C   B      = STANDARD DEVIATION
C-----------------------------------------------------------------------

      IMPLICIT NONE

      COMMON /CRCONSTA/PI,PI2,OB3,TB3,ENEPER,SQRT3
      DOUBLE PRECISION PI,PI2,OB3,TB3,ENEPER,SQRT3

      COMMON /CRRANDPA/RD,FAC,U1,U2,NSEQ,ISEED,KNOR
      DOUBLE PRECISION RD(3000),FAC,U1,U2

      INTEGER          ISEED(3,10),NSEQ

      LOGICAL          KNOR

      COMMON /CRRUNPAR/FIXHEI,THICK0,HILOECM,HILOELB,SIG1I,TARG1I,
     *                 STEPFC,RCUT,RCUT2,
     *                 NRRUN,NSHOW,MPATAP,MONIIN,
     *                 MONIOU,MDEBUG,NUCNUC,MTABOUT,MLONGOUT,
     *                 ISEED1I,
     *                 IUDEBUG,IUDEBG0,
     *                 MCETAP,NOCERB,
     *                 MCERABS,MCERQEF,MCERMIR,
     *                 LSTCK,
     *                 LSTCK1,LSTCK2,
     *                 ISHOWNO,ISHW,NOPART,NRECS,NBLKS,MAXPRT,NDEBDL,
     *                 N1STTR,MDBASE,
     *                 DEBDEL,DEBUG,FDECAY,FEGS,FIRSTI,FIXINC,FIXTAR,
     *                 FIX1I,FMUADD,FNKG,FPRINT,FDBASE,FPAROUT,FTABOUT,
     *                 FLONGOUT,GHEISH,GHESIG,GHEISDB,USELOW,TMARGIN

     *                 ,FOUTFILE,IFINAM

     *                 ,FURQMD,FURQSG

      COMMON /CRRUNPAC/DATDIR,DSN,DSNTAB,DSNLONG,HOST,USER

     *                 ,LSTDSN

     *                 ,FILOUT

      DOUBLE PRECISION FIXHEI,THICK0,HILOECM,HILOELB,SIG1I,TARG1I,
     *                 STEPFC,RCUT,RCUT2

      INTEGER          NRRUN,NSHOW,MPATAP,MONIIN,MONIOU,MDEBUG,NUCNUC,
     *                 ISHOWNO,ISHW,NOPART,NRECS,NBLKS,MAXPRT,NDEBDL,
     *                 N1STTR,MDBASE,MTABOUT,MLONGOUT,ISEED1I(3)

      INTEGER          IUDEBUG,IUDEBG0


      INTEGER          MCETAP,NOCERB

      INTEGER          MCERABS,MCERQEF,MCERMIR

      INTEGER          LSTCK

     *                ,LSTCK1,LSTCK2

      CHARACTER*132    FILOUT

      CHARACTER*255    DSN,DSNTAB,DSNLONG
      CHARACTER*132    DATDIR
      CHARACTER*60     HOST,USER

      CHARACTER*9      LSTDSN

      LOGICAL          DEBDEL,DEBUG,FDECAY,FEGS,FIRSTI,FIXINC,FIXTAR,
     *                 FIX1I,FMUADD,FNKG,FPRINT,FDBASE,FPAROUT,FTABOUT,
     *                 FLONGOUT,GHEISH,GHESIG,GHEISDB,USELOW,TMARGIN

      LOGICAL          FOUTFILE
      INTEGER          IFINAM

      LOGICAL          FURQMD,FURQSG

      DOUBLE PRECISION A,B,RR
      INTEGER LLSEQ
      SAVE
C-----------------------------------------------------------------------

      LLSEQ = 1
C      IF ( DEBUG ) WRITE(MDEBUG,100) SNGL(A),SNGL(B)
C100   FORMAT(' RANNOR: A,B=',1P,2E10.3)
ctp      write(mdebug,*)'knor,u1,u2,fac,llseq',knor,u1,u2,fac,llseq
      IF ( KNOR ) THEN
  1     CONTINUE
        CALL RMMARD( RD,2,LLSEQ )
        U1 = 2.D0*RD(1) - 1.D0
        U2 = 2.D0*RD(2) - 1.D0
        RR = U1**2 + U2**2
        IF ( RR .GE. 1.D0  .OR.  RR .EQ. 0.D0 ) GOTO 1
        FAC = SQRT( (-2.D0) * LOG( RR ) / RR )

        RANNOR = FAC * U1 * B + A
        KNOR   = .FALSE.
      ELSE
        RANNOR = FAC * U2 * B + A
        KNOR   = .TRUE.
      ENDIF
C      IF ( DEBUG ) WRITE(MDEBUG,101) RANNOR
C101   FORMAT('+',34X,' RANNOR =',1P,E12.5)

      RETURN
      END
