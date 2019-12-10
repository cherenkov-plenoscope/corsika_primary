/*
   Copyright (C) 1997, 1998, ..., 2012, 2013, 2016  Konrad Bernloehr

   This file is part of the IACT/atmo package for CORSIKA.

   The IACT/atmo package is free software; you can redistribute it 
   and/or modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 2.1 of the License, or (at your option) any later version.

   This package is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public License
   along with this package. If not, see <http://www.gnu.org/licenses/>.
 */

/* ================================================================== */
/**
 *  @file iact.c
 *  @short CORSIKA interface for Imaging Atmospheric Cherenkov Telescopes etc.
 *
 *  @author  Konrad Bernloehr 
 *  @date    @verbatim CVS $Date: 2016-01-30 09:17:27 +0100 (Sat, 30 Jan 2016) $ @endverbatim
 *  @date    @verbatim CVS $Revision: 5173 $ @endverbatim
 *
 *  Version 1.2.28 (for IACT/ATMO package version 1.49)
 *
 *  --------------------------------------------------------------------
 *
 *  This file implements a CORSIKA interface for the simulation
 *  of (3-D) arrays of Cherenkov telescopes.
 *  A whole array may be simulated in multiple instances with
 *  random offsets of each instance.
 *  For full use of this software additional files are required
 *  which are available now on request from Konrad Bernloehr
 *  (e-mail: Konrad.Bernloehr@mpi-hd.mpg.de).
 *  These additional files should be included in the same add-on
 *  package to CORSIKA which includes this file.
 *  A fallback mechanism is included to use the normal CORSIKA
 *  output of Cherenkov photon bunches instead of the dedicated
 *  output functions from the unavailable files. However, this
 *  fallback mechanism has important drawbacks: information about
 *  positions of telescopes are completely lost and no photon
 *  bunches are collected in memory because the collected bunches
 *  would never be written out. For those reasons you are adviced
 *  to obtain and use the additional software. 
 *
 *
 *  General comments on this file:
 *
 *  Routines provided in this file interface to recent versions
 *  of the CORSIKA air shower simulation program. Modifications to
 *  CORSIKA have been kept as simple as possible and the existing
 *  routines for production of Cherenkov light have been largely
 *  maintained. Setup of the telescope systems to be simulated is
 *  via the usual CORSIKA input file (the syntax of which has been
 *  extended by a few additional keywords). These telescope systems
 *  can be randomly scattered several times within a given area.
 *  All treatment whether a bunch of photons hits a telescope is done
 *  by the routines in this file. Photon bunches are kept in main
 *  memory until the end of the event. This might be a limitation
 *  when simulating large showers / many telescopes / many systems of
 *  telescopes on a computer with little memory. An option to store
 *  photon bunches in a temporary file has, therefore, been included.
 *  After the end of an event in CORSIKA all photon bunches (sorted
 *  by system and telescope) are written to a data file in the
 *  'eventio' portable data format also used for CRT and HEGRA CT data.
 *  All CORSIKA run/event header/trailer blocks are also written to
 *  this file.
 *
 * This version comes with sections for conditional compilation like
 *    EXTENDED_TELOUT         CORSIKA is compiled with extended interface (IACTEXT option).
 *                            Information about particles on ground is stored.
 *    IACTEXT                 For all practical purposes a synonym to EXTENDED_TELOUT.
 *    STORE_EMITTER           Store information about all particles emitting light
 *                            after the photon bunch. This duplicated the amount of data.
 *                            Requires the IACTEXT option to be activated.
 *    MARK_DIRECT_LIGHT       The Cherenkov photons bunches from the primary particle
 *                            and its leading/major fragments are marked up with a
 *                            non-zero wavelength (1: direct, 2, 3: major fragments).
 *                            Requires the IACTEXT option to be activated.
 *                            See the ALL_WL_RANDOM configuration parameter to sim_telarray.
 *    CORSIKA_SAVES_PHOTONS   CORSIKA should save photons in its own format.
 * Note that these extensions may not have been tested in a long time. Use with care.
 *
*/

/* ==================================================================== */

#define IACT_ATMO_VERSION "1.49 (2016-01-27)"

#ifndef MAX_IO_BUFFER
# define MAX_IO_BUFFER 200000000
#endif

#ifndef MAX_BUNCHES
/* The maximum number of bunches per telescope that the telescope simulation */
/* can read. This should be adapted to actual limits there. */
# define MAX_BUNCHES 5000000
#endif

#if defined(IACTEXT)
# define EXTENDED_TELOUT 1
#elif defined(EXTENDED_TELOUT)
# define IACTEXT 1
#endif

/* Compile with '-DNO_EVENTIO' if eventio functions are not available. */
#ifndef NO_EVENTIO
# define HAVE_EVENTIO_FUNCTIONS 1
#endif

/* Without 'eventio' functions saving the photon bunches is left to CORSIKA. */
/* If you want both kinds of output, compile with '-DCORSIKA_SAVES_PHOTONS' */
#ifndef CORSIKA_SAVES_PHOTONS
# ifndef HAVE_EVENTIO_FUNCTIONS
#  define CORSIKA_SAVES_PHOTONS 1
# endif
#endif

/* Compile with '-DNO_PIPE' if piping of output directly to other programs */
/* is not wanted at all. To actually use pipes, start 'TELFIL' with a '|'. */
#ifndef NO_PIPE
# define PIPE_OUTPUT 1
#endif

/* The Cherenkov light longitudinal distribution from CORSIKA might be  */
/* in either of two ways: an emission profile or an integrated profile. */
/* When neither INTEGRATED_LONG_DIST nor EMISSION_LONG_DIST is declared */
/* we try to find it out dynamically. */
#ifndef INTEGRATED_LONG_DIST
# ifndef EMISSION_LONG_DIST
#  define UNKNOWN_LONG_DIST 1
# endif
#endif




#ifdef HAVE_EVENTIO_FUNCTIONS
#include "initial.h"      /* This file includes others as required. */
#include "io_basic.h"     /* This file includes others as required. */
#include "mc_tel.h"
#ifndef NO_FILEOPEN
#include "fileopen.h"
#endif
#else
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>
#endif

#include "sampling.h"
#include "straux.h"


/* ------------ CORSIKA version-specific definitions -------------- */

#ifndef CORSIKA_VERSION
/* Version 6.990 is the last one well tested but up to 7.400 known to compile. */
/* Support for versions before 6.400 has been dropped. Use version 1.47 */
/* of the IACT/ATMO package for these historical CORSIKA versions. */
# define CORSIKA_VERSION 6900 /* the version that should be matched */
#endif

#if (CORSIKA_VERSION < 6400)
Error: Outdated corsika versions no longer supported.
#endif

# define PRMPAR_SIZE 17

/** Type for CORSIKA floating point numbers remaining REAL*4 */
typedef float cors_real_t;
/** Type for many CORSIKA numbers has changed to REAL*8 with version 5.901. */
typedef double cors_real_now_t;
/** Type for CORSIKA numbers which were REAL*4 but changed to REAL*8 at 5.900 */
typedef double cors_real_dbl_t;
/** Type for CORSIKA numbers which were already REAL*8 */
typedef double cors_dbl_t;

/* ----------- Standard C or Unix-specific include files ---------- */

#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <ctype.h>

/* The following definitions are left over from a rare memory problem */
/* that turned out to be due to a RAM hardware problem. */
/* Should be removed after more testing. */

#ifndef EXTRA_MEM
# define EXTRA_MEM 0
#endif
#define EXTRA_MEM_1 EXTRA_MEM
#define EXTRA_MEM_2 EXTRA_MEM
#define EXTRA_MEM_3 EXTRA_MEM
#define EXTRA_MEM_4 EXTRA_MEM
#define EXTRA_MEM_5 EXTRA_MEM
#define EXTRA_MEM_6 EXTRA_MEM
#define EXTRA_MEM_7 EXTRA_MEM
#define EXTRA_MEM_8 EXTRA_MEM
#define EXTRA_MEM_9 EXTRA_MEM
#define EXTRA_MEM_10 EXTRA_MEM
#define EXTRA_MEM_11 EXTRA_MEM
#define EXTRA_MEM_12 EXTRA_MEM

/* -------------- Use the RMMAR[D] random number generator ----------- */

extern void rmmard_(double *, int *, int *);

#ifdef __GNUC__
static double rndm(int __attribute__((unused)) dummy);
#else
static double rndm(int dummy);
#endif

/** @short Random number interface using sequence 4 of CORSIKA. */
#ifdef __GNUC__
static double rndm(int __attribute__((unused)) dummy)
#else
static double rndm(int dummy)
#endif
{
   int num = 1;
   int seq = 4;     /* Use sequence number 4 of RMMAR[D] */
   static double rtmp[10];
   rmmard_(rtmp,&num,&seq); /* Call Fortran subroutine */
   return rtmp[0];
}

double iact_rndm(int dummy);

double iact_rndm(int dummy)
{
   return rndm(dummy);
}

/* -------------------------------------------------------------- */

#ifndef Nint
#define Nint(x) ((x)>0?(int)((x)+0.5):(int)((x)-0.5))
#endif
#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))

/** The CORSIKA version actually running. */
int corsika_version = (CORSIKA_VERSION);

/** Maximum number of telescopes (or other detectors) per array */
#define MAX_ARRAY_SIZE 1000 /* Use the same limit as in CORSIKA itself. */
/** Position and size definition of fiducial spheres. */
static double xtel[MAX_ARRAY_SIZE], ytel[MAX_ARRAY_SIZE],
              ztel[MAX_ARRAY_SIZE], rtel[MAX_ARRAY_SIZE];
static double raise_tel;  /**< Non-zero if any telescope has negative z */
static double rmax = 0.;  /**< Max. radius of telescopes */
static double dmax = 0.;  /**< Max. distance of telescopes in (x,y) */
static int ntel = 0;      /**< Number of telescopes set up */
static int nsys = 1;      /**< Number of arrays */

/* Speed of light used to correct for the delay between observation level */
/* and the actual telescope elevation. Adapted to observation level after run start. */
static double airlightspeed = 29.9792458/1.0002256; /**< [cm/ns] at H=2200 m */

/** The maximum core offset of array centres in circular distribution. */
static double core_range;
/** The maximum core offsets in x,y for rectangular distribution. */
static double  core_range1, core_range2;
static double impact_offset[2]; /**< Offset of impact position of charged primaries */
static int impact_correction = 1; /**< Correct impact position if non-zero. */

/** The central value of the allowed ranges in theta and phi. */
static double theta_central, phi_central, off_axis;

/* The number of events for which full output is 'printed' can be limited. */
/* You can control that with the TELFIL option for the output file. */
/* Defaults correspond to 'TELFIL iact.dat:10:100:1' */
static int count_print_tel = 0, count_print_evt = 0;
static int max_print_tel = 10, max_print_evt = 100;
static int skip_print = 1, skip_print2 = 100;
static int skip_off2 = 1;

/* Parameters for external setup of primaries. */
int with_extprim = 0;
void extprim_setup(char *text);

/** The name of the file providing parameters for importance sampling. */
static char *sampling_fname;
/** The name of the output file for eventio format data. */
static char *output_fname;
/** The largest block size in the output data, which must hold all
    photons bunches of one array. */
static size_t max_io_buffer = MAX_IO_BUFFER;
static long max_bunches = MAX_BUNCHES;
#ifdef HAVE_EVENTIO_FUNCTIONS
/* Data structures are defined in mc_tel.h */
static IO_BUFFER *iobuf;
static void ioerrorcheck ();
#else
/* Data structures: */

/** A photon (or photoelectron) bunch in full mode. */
struct bunch
{
   float photons; /**< Number of photons in bunch */
   float x, y;    /**< Arrival position relative to telescope (cm) */
   float cx, cy;  /**< Direction cosines of photon direction */
   float ctime;   /**< Arrival time (ns) */
   float zem;     /**< Height of emission point above sea level (cm) */
   float lambda;  /**< Wavelength in nanometers or 0 (negative if scattered) */
};

/** A photon (or photoelectron) bunch in compact mode. */
struct compact_bunch
{
   short photons; /**< ph*100 */
   short x, y;    /**< x,y*10 (mm) */
   short cx, cy;  /**< cx,cy*30000 */
   short ctime;   /**< ctime*10 (0.1ns) after subtracting offset */
   short log_zem; /**< log10(zem)*1000 */
   short lambda;  /**< (nm) or 0 (negative for scattered light) */
};

/** A linked list of text strings. */
struct linked_string
{
   char *text;
   struct linked_string *next;
};

#endif

#define NBUNCH 5000           /**< Memory allocation step size for bunches */
#define INTERNAL_LIMIT 100000 /**< Start external storage after so many bunches */
#define EXTERNAL_STORAGE 1    /**< Enable external temporary bunch storage */

/** A structure describing a detector and linking its photons bunches to it. */
struct detstruct
{
   double x, y, x0, y0, z0, r0;
   double sampling_area;
   double r, dx, dy;
   int geo_type;
   int sens_type;
   int dclass;
   int iarray;
   int idet;
   int bits;
   double photons;
   struct bunch *bunch;
   struct compact_bunch *cbunch;
   int available_bunch;
   int next_bunch;
   char ext_fname[60];
   int external_bunches;
   int shrink_factor;
   int shrink_cycle;
};

struct gridstruct
{
   int ndet, idet;
   struct detstruct **detectors;
};

#define MAX_CLASS 1

#ifdef IACTEXT
static struct bunch *particles;
int particles_space;
int particles_stored;
#endif

/** The largest number of photon bunches kept in main memory before
    attempting to flush them to temporary files on disk. */
static int max_internal_bunches = INTERNAL_LIMIT;
static int narray;
static int *ndet;
static int nevents, event_number;
static int do_print;
static struct detstruct **detector;
static int det_in_class[MAX_CLASS];
static double *xoffset, *yoffset, *weight;
static struct gridstruct *grid;
static double grid_x_low, grid_y_low, grid_x_high, grid_y_high;
static int grid_nx, grid_ny, grid_elements;

static char corsika_inputs_head[80]; /* "* CORSIKA inputs:" */
static struct linked_string corsika_inputs = { corsika_inputs_head, NULL };

static int tel_individual = 0; // 0: never split, 1: always split, 2: split automatically.
static int televt_done;
static size_t tel_split_threshold = 10000000; // Bunches in the whole array for auto-splitting.
static double obs_height, toffset;
static double energy, theta_prim, phi_prim;
#ifdef SHOW_ANGLE
static double cx_prim, cy_prim, cz_prim;
#endif
static int nrun;
static int primary;
static double first_int;
static double Bfield[3]; /**< Magnetic field vector in detector coordinate system (with Bz positive if upwards) */
static double pprim[3];  /**< Momentum vector of primary particle */
static double bxplane[3], byplane[3]; /**< Spanning vectors of shower plane such that projection of B field is in bxplane direction */

#if defined(IACTEXT) || defined(EXTENDED_TELOUT)
static int use_compact_format = 0;
#else
static int use_compact_format = 1;
#endif

static double all_photons, all_photons_run;
static double all_bunches, all_bunches_run;
static long stored_bunches;
static double lambda1, lambda2;

#define GRID_SIZE 1000  /**< unit: cm */


/* =============================================================== */

/* FORTRAN called functions (beware changes of parameter types !!) */
/* The additional character string lengths for name in telfil_ and */
/* line in tellni_ are not used because compiler-dependent.        */
void telfil_(char *name);
void telsmp_(char *name);
void telshw_(void);
void telinf_(int *itel, 
   double *x, double *y, double *z, double *r, int *exists);
void tellni_(char *line, int *llength); 
void telrnh_(cors_real_t runh[273]);
void telrne_(cors_real_t rune[273]);
void telasu_(int *n, cors_real_dbl_t *dx, cors_real_dbl_t *dy);
void telset_(cors_real_now_t *x, cors_real_now_t *y, 
   cors_real_now_t *z, cors_real_now_t *r);
void televt_(cors_real_t evth[273], cors_real_dbl_t prmpar[PRMPAR_SIZE]);
int telout_(cors_real_now_t *bsize, cors_real_now_t *wt, 
   cors_real_now_t *px, cors_real_now_t *py, cors_real_now_t *pu, 
   cors_real_now_t *pv, cors_real_now_t *ctime, 
   cors_real_now_t *zem, cors_real_now_t *lambda
#ifdef EXTENDED_TELOUT
   , double *temis, double *penergy, double *amass, double *charge
#endif
   );
#ifdef IACTEXT
void telprt_ (cors_real_t* datab, int *maxbuf);
#endif
void tellng_ (int *type, double *data, int *ndim, int *np, 
   int *nthick, double *thickstep);
void telend_(cors_real_t evte[273]);

void extprm_(
    cors_real_dbl_t *type,
    cors_real_dbl_t *eprim,
    double *thetap,
    double *phip,
    double *thick0,
    int* iseed);

/* CORSIKA function called from this module: */
extern double heigh_ (double *thickness);

/* C called functions (parameter types are always checked) */
static void iact_param (char *text);
static int photon_hit (struct detstruct *det, double x, double y,
   double cx, double cy, double sx, double sy, double photons,
   double ctime, double zem, double lambda);
static int in_detector (struct detstruct *det, double x, double y, 
   double sx, double sy);
static int set_random_systems (double theta, double phi, 
   double thetaref, double phiref, double offax,
   double E, int primary, int volflag);

void sample_offset (char *sampling_fname, double core_range, 
   double theta, double phi, 
   double thetaref, double phiref, double offax, 
   double E, int primary,
   double *xoff, double *yoff, double *sampling_area);

static double ush, vsh, wsh;
static double ushc, vshc, wshc;

extern double refidx_ (double *height);
extern double rhof_ (double *height);

/** Norm of a 3-D vector */
static double norm3 (double *v);
static double norm3 (double *v)
{
   return sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);
}
/** Normalize a 3-D vector */
static void norm_vec (double *v);
static void norm_vec (double *v)
{
   double n = sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);
   if ( n != 0. )
   {
      v[0] /= n;
      v[1] /= n;
      v[2] /= n;
   }
}
#ifdef HISTOGRAMS
/** Scalar product of two 3-D vectors */
static double scalar_prod (double *v1, double *v2);
static double scalar_prod (double *v1, double *v2)
{
   return v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2];
}
/** Scalar product of two normalized 3-D vectors, i.e cos(angle between vectors) */
static double scalar_prod_norm (double *v1, double *v2);
static double scalar_prod_norm (double *v1, double *v2)
{
   double n1 = sqrt(v1[0]*v1[0]+v1[1]*v1[1]+v1[2]*v1[2]);
   double n2 = sqrt(v2[0]*v2[0]+v2[1]*v2[1]+v2[2]*v2[2]);
   if ( n1 != 0. && n2 != 0. )
      return (v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]) / (n1*n2);
   else
      return 0.;
}
#endif
/** Cross (outer) product of two 3-D vectors v1, v2 into 3-D vector v3 */
static void cross_prod (double *v1, double *v2, double *v3);
static void cross_prod (double *v1, double *v2, double *v3)
{
   v3[0] = v1[1]*v2[2] - v1[2]*v2[1];
   v3[1] = v1[2]*v2[0] - v1[0]*v2[2];
   v3[2] = v1[0]*v2[1] - v1[1]*v2[0];
}
#if 0
/** Cross (outer) product of two normalized 3-D vectors */
static void cross_prod_norm (double *v1, double *v2, double *v3);
static void cross_prod_norm (double *v1, double *v2, double *v3)
{
   double n1 = sqrt(v1[0]*v1[0]+v1[1]*v1[1]+v1[2]*v1[2]);
   double n2 = sqrt(v2[0]*v2[0]+v2[1]*v2[1]+v2[2]*v2[2]);
   v3[0] = (v1[1]*v2[2] - v1[2]*v2[1]) / (n1*n2);
   v3[1] = (v1[2]*v2[0] - v1[0]*v2[2]) / (n1*n2);
   v3[2] = (v1[0]*v2[1] - v1[1]*v2[0]) / (n1*n2);
}
#endif

/* ================================================================== */

#ifdef CATCH_SIGNALS
#include <signal.h>
#if defined(OS_ULTRIX)
void stop_signal_function (int isig, int code, struct sigcontext *scp);
#else
void stop_signal_function (int isig);
#endif

/** Catching signals and then exit makes sense with dmalloc, for example. */
#if defined(OS_ULTRIX)
void stop_signal_function (int isig, int code, struct sigcontext *scp)
#else
void stop_signal_function (int isig)
#endif
{
   if ( isig >= 0 )
   {
#if defined(OS_ULTRIX)
      fprintf(stderr,"Received signal %d (code %d)\n",isig,code);
#else
      fprintf(stderr,"Received signal %d\n",isig);
#endif
   }
   
   signal(SIGINT,SIG_DFL);
   signal(SIGTERM,SIG_DFL);
   
   /* Free all allocated memory. With memory debugging tools this helps to */
   /* reassure that no memory leaks or other memory allocation problems exist. */
   
   /* Free grid from previous showers */
   
   if ( grid != NULL )
   {
      int ix, iy;
      for (iy=0; iy<grid_ny; iy++)
         for (ix=0; ix<grid_nx; ix++)
         {
            struct gridstruct *gc;
            if ( iy*grid_nx+ix < 0 || iy*grid_nx+ix >= grid_elements )
            {
               fprintf(stderr,
              "Grid bounds exceeded: ix=%d, iy=%d, i=%d (nx=%d, ny=%d, n=%d)\n",
                  ix, iy, iy*grid_nx+ix, grid_nx, grid_ny, grid_elements);
            }
            gc = &grid[iy*grid_nx+ix];
            if ( gc->detectors != NULL )
            {
               free(gc->detectors);
               gc->detectors = NULL;
            }
            gc->ndet = gc->idet = 0;
         }
      free(grid);
      grid = NULL;
   }
    
   if ( detector != 0 )
   {
      int iarray;
      for (iarray=0; iarray<narray; iarray++)
      {
         if ( detector[iarray] != NULL )
         {
            int idet;
	    for (idet=0; idet<ndet[iarray]; idet++)
            {
               if ( detector[iarray][idet].cbunch != NULL )
               {
                  free(detector[iarray][idet].cbunch);
                  detector[iarray][idet].cbunch = NULL;
               }
               if ( detector[iarray][idet].bunch != NULL )
               {
                  free(detector[iarray][idet].bunch);
                  detector[iarray][idet].bunch = NULL;
               }
            }
            free(detector[iarray]);
            detector[iarray] = NULL;
         }
      }
      free(detector);
      detector = NULL;
   }
   
   if ( ndet != NULL )
   {
      free(ndet);
      ndet = NULL;
   }

   /* Search end of linked list */
   {
      struct linked_string *xl;
      for (xl=&corsika_inputs; xl != NULL; )
      {
         struct linked_strings *xln = xl->next;
         xl->next = NULL;
         if ( xl != &corsika_inputs )
         {
            if ( xl->text != NULL )
            {
               free(xl->text);
               xl->text = NULL;
            }
            free(xl);
         }
         xl = xln;
      }
   }
   
   if ( output_fname != NULL )
   {
      free(output_fname);
      output_fname = NULL;
   }
   
   if ( xoffset != NULL )
   {
      free(xoffset);
      xoffset = NULL;
   }

   if ( yoffset != NULL )
   {
      free(yoffset);
      yoffset = NULL;
   }
   
   if ( weight != NULL )
   {
      free(weight);
      weight = NULL;
   }
   
   initpath(NULL); /* Two allocations remain there */
   
   if ( iobuf != NULL )
   {
      if ( iobuf->output_file != NULL )
         fileclose(iobuf->output_file);
      iobuf->output_file = NULL;
      free_io_buffer(iobuf);
      iobuf = NULL;
   }

   exit(1);
}

#endif

#ifdef HAVE_EVENTIO_FUNCTIONS
void ioerrorcheck (void)
{
   static size_t ioerrcnt = 0;
   
   if ( ++ioerrcnt > 100 )
   {
      fflush(stdout);
      fprintf(stderr,"\n\nFatal error:\n"
          "Too many errors on the IACT output file were detected.\n"
          "It makes little sense to continue with CORSIKA when no output\n"
          "can be written or the output file is badly corrupted.\n"
          "This situation could arise when your disk is full or the output is\n"
          "piped into a detector simulation program and that happened to fail.\n");
      fflush(NULL);
      exit(9);
   }
}
#endif

char primary_path[1024] = "";
FILE *primary_file;

/* ------------------------------ telfil_ --------------------------- */
/**
 * @short Define the output file for photon bunches hitting the telescopes.
 *
 * This function is called when the 'TELFIL' keyword is present in
 * the CORSIKA input file.
 *
 * @verbatim
 * The 'file name' parsed is actually decoded further:
 *    Apart from the leading '+' or '|' or '+|' the TELFIL argument
 *    may contain further bells ans whistles:
 *    If the supplied file name contains colons, they are assumed to 
 *    separate appended numbers with the following meaning:
 *      #1:  number of events for which the photons per telescope are shown
 *      #2:  number of events for which energy, direction etc. are shown
 *      #3:  every so often an event is shown (e.g. 10 -> every tenth event).
 *      #4:  every so often the event number is shown even if #1 and #2 ran out.
 *      #5:  offset for #4 (#4=100, #5=1: show events 1, 101, 201, ...)
 *      #6:  the maximum number of photon bunches before using external storage
 *      #7:  the maximum size of the output buffer in Megabytes.
 *    Example: name = "iact.dat:5:15:10"
 *       name becomes "iact.dat"
 *       5 events are fully shown
 *       15 events have energy etc. shown
 *       Every tenth event is shown, i.e. 10,20,30,40,50 are fully shown
 *       and events number 60,...,150 have their energies etc. shown.
 *       After that every shower with event number divideable by 1000 is shown.
 *    Note: No spaces inbetween! CORSIKA input processing truncates at blanks.
 * @endverbatim
 *
 * @param  name    Output file name.
 * 		   Note: A leading '+' means: use non-compact format
 * 		   A leading '|' (perhaps after '+') means that the
 * 		   name will not be interpreted as the name of
 * 		   a data file but of a program to which the
 * 		   'eventio' data stream will be piped (i.e. that
 * 		   program should read the data from its standard
 * 		   input.
 * @return (none)
 *
*/

void telfil_ (char *name)
{
   int i, l;
   char *s;

   if ( (s=strchr(name,':')) != NULL )
   {
      *s = '\0';
      if ( max_print_tel == 0 )
      {
         max_print_tel = max_print_evt = atoi(s+1);
         skip_print = 1; /* Well, actually 1 means don't skip any event */
      }
      if ( (s=strchr(s+1,':')) != NULL )
      {
	 if ( (max_print_evt = atoi(s+1)) < max_print_tel )
	    max_print_evt = max_print_tel;
	 if ( (s=strchr(s+1,':')) != NULL )
         {
	    if ( (skip_print = atoi(s+1)) <= 0 )
	       skip_print = 1;
            if ( (s=strchr(s+1,':')) != NULL )
            {
	       if ( (skip_print2 = atoi(s+1)) <= 0 )
	          skip_print2 = 1000;
               if ( (s=strchr(s+1,':')) != NULL )
               {
	          if ( (skip_off2 = atoi(s+1)) <= 0 )
	             skip_off2 = 0;
                  if ( (s=strchr(s+1,':')) != NULL )
                  {
	             if ( (max_internal_bunches = atoi(s+1)) <= 1000 )
	                max_internal_bunches = INTERNAL_LIMIT;
                     if ( (s=strchr(s+1,':')) != NULL )
                     {
                        /* Maximum size of I/O buffer in 10^6 bytes units. */
                        if ( atoi(s+1) >= 1 && atoi(s+1) < 64000 )
                           max_io_buffer = ((size_t) atoi(s+1)) * 1000000;
                     }
                  }
               }
            }
	 }
      }
   }

   /* The rest of the string should be the real file name */
   l = strlen(name);
   if ( l > 1024 )
   {
      fprintf(stderr,
         "\n Output file name of length %d truncated to 1024 characters.\n\n",l);
      l = 1024;
   }
#ifdef REMOVE_PADDING_BLANKS
   for (i=l; i>0; i--)
      if ( name[i-1] != ' ' && name[i-1] != '\n' && name[i-1] != '\0' )
         break;
#else
   i = l;
#endif
   name[i] = '\0';
   if ( *name == '+' && i > 0 )
   {
      name++; i--;
      use_compact_format = 0;
   }
#if !defined(IACTEXT) && !defined(EXTENDED_TELOUT)
   else
      use_compact_format = 1;
#endif
   if ( i <= 0 )
   {
      fprintf(stderr,"Missing or invalid filename for Cherenkov photons.\n");
      exit(1);
   }
   output_fname = (char *) malloc((size_t)i+1+EXTRA_MEM_1);
   strncpy(output_fname,name,(size_t)i);
   output_fname[i] = '\0';
   /* If we get "/dev/null" plus anything behind it, it still should be just "/dev/null" */
   if ( strncmp(output_fname,"/dev/null",(size_t)9) == 0 )
      strcpy(output_fname,"/dev/null");
#ifndef HAVE_EVENTIO_FUNCTIONS
   fprintf(stderr,"\n Output filename for Cherenkov photons ignored.\n\n");
#endif
}


/* ----------------------------- telsmp_ --------------------------- */
/**
 *  @short Set the file name with parameters for importance sampling.
 *
 *  Note that the TELSAMPLE parameter is not processed by CORSIKA itself
 *  and thus has to be specified through configuration lines like
@verbatim
IACT TELSAMPLE filename
*(IACT) TELSAMPLE filename
@endverbatim
where the first form requires a CORSIKA patch and the second
would work without that patch (but then only with uppercase file names).
 */

void telsmp_ (char *name)
{
   size_t i, len = 0;
   if ( name == 0 )
      return;
   len = strlen(name);
   for (i=0; i<len; i++)
      if ( !isalnum(name[i]) && name[i] != '_' && name[i] != '.' && 
           name[i] != '-' && name[i] != '/' )
      {
         fprintf(stderr,"\n Invalid file name for core offset sampling parameters.\n\n");
         return; 
      }
   sampling_fname = (char *) malloc((size_t)len+1+EXTRA_MEM_1);
   strcpy(sampling_fname,name);
}

/* ------------------------------ telshw_ --------------------------- */
/**
 *  @short Show what telescopes have actually been set up.
 *
 *  This function is called by CORSIKA after the input file is read.
 *
*/

void telshw_ ()
{
   int i;
   fflush(NULL);
#ifdef HAVE_EVENTIO_FUNCTIONS
   fprintf(stdout,"\n Telescope output file: '%s'\n",output_fname);
#endif
   fprintf(stdout,"\n Number of simulated telescopes: %d\n",ntel);
   if ( raise_tel != 0. )
      fprintf(stdout," All telescopes are raised by %4.2f m\n",
         0.01*raise_tel);
   for (i=0; i<ntel; i++)
      fprintf(stdout,
      "    Telescope %d at x=%6.2f m, y=%6.2f m, z=%6.2f m with r=%4.2f m\n",
         i+1,xtel[i]/100.,ytel[i]/100.,ztel[i]/100.,rtel[i]/100.);          
   fprintf(stdout,"\n");
   fprintf(stdout," Number of telescope arrays simulated: %d\n",nsys);
   if ( core_range2 <= 0. )
      fprintf(stdout,
      " Array centers are at random offsets within %5.2f m radius from core.\n",
         core_range/100.);
   else
      fprintf(stdout,
      " Array centers are at random offsets within %5.2f m by %5.2f m from core.\n",
         core_range1/100.,core_range2/100.);
   if ( sampling_fname != NULL )
      fprintf(stdout,
      " The distribution of core offsets within this area is controlled through the\n"
      " parameter file '%s'.\n"
      " All generated events are recorded with area weights.\n",
      sampling_fname);
   fprintf(stdout, " Impact position correction for bending of primary particle track in geomagnetic field is %s.\n",
      impact_correction ? "on" : "off");
   if ( with_extprim )
   {
      fprintf(stdout,
      " Primary particles should be set up externally (user-defined).\n");
   }
   fprintf(stdout," Up to %d bunches are kept in memory before writing to temporary files.\n",
      max_internal_bunches);
   if ( max_bunches > 0 )
      fprintf(stdout," When more than %ld bunches are collected per telescope, thinning sets in.\n",
         max_bunches);
   /* fprintf(stdout," I/O buffers can dynamically grow up to a size of %ld bytes\n", (long) max_io_buffer); */
   if ( tel_individual == 0 )
      fprintf(stdout," All photon data is enclosed in one block per array.\n");
   else if ( tel_individual == 1 )
      fprintf(stdout," All photon data is written in a separate block for each telescope.\n");
   else if ( tel_individual == 2 )
      fprintf(stdout," Photon data is automatically split if exceeding a total of %ld bunches.\n",
         (unsigned long) tel_split_threshold);
   fprintf(stdout,"\n");
   fflush(stdout);
}

/* --------------------------- telinf_ ------------------------------ */
/**
 * @short Return information about configured telescopes back to CORSIKA
 *
 * @param  itel     number of telescope in question
 * @param  x, y, z  telescope position [cm]
 * @param  r	    radius of fiducial volume [cm]
 * @param  exists   telescope exists
 *
*/

void telinf_ (int *itel, 
   double *x, double *y, double *z, double *r, int *exists)
{
   if ( *itel <= 0 || *itel > ntel )
   {
      *exists = 0;
      *x = *y = *z = *r = 0.;
   }
   else
   {
      *exists = 1;
      *x = xtel[*itel-1];
      *y = ytel[*itel-1];
      *z = ztel[*itel-1];
      *r = rtel[*itel-1];
   }
}


/** Expanding environment variables ourselves rather than passing that on 
 *  a shell later, so that we can still check characters after expansion.
 */

static int expand_env (char *fname, size_t maxlen);

static int expand_env (char *fname, size_t maxlen)
{
   char varname[128];
   char *beg = NULL, *end = NULL, *dollar = NULL, *next = NULL;
   char tmp_fname[maxlen];
   char *value;
   size_t vlen = 0;
   int expansions = 0;
   
   while ( (dollar = beg = strchr(fname,'$')) != NULL && expansions < 100 )
   {
      next = NULL;
      if ( beg[1] == '{' )
      {
         beg += 2;
         end = strchr(beg,'}');
         if ( end != NULL ) next = end+1;
      }
      else if ( beg[1] == '(' )
      {
         beg += 2;
         end = strchr(beg,')');
         if ( end != NULL ) next = end+1;
      }
      else if ( isalpha(beg[1]) )
      {
         beg++;
         end = beg;
         while ( isalnum(*end) || *end == '_' )
            end++;
         next = end;
      }
      else
         end = next = NULL;
      if ( end == NULL || next == NULL )
         break;
      if ( end-beg < 1 || (size_t)(end-beg) >= sizeof(varname) )
         break;
      strncpy(varname,beg,end-beg);
      varname[end-beg] = '\0';
      printf("Looking for variable %s\n",varname);
      value = getenv(varname);
      vlen = 0;
      if ( value != NULL )
      {
         vlen = strlen(value);
         if ( vlen + strlen(fname) - (next-dollar) >= maxlen )
            break;
      }
      if ( dollar-fname > 0 )
         strncpy(tmp_fname,fname,dollar-fname);
      if ( vlen > 0 )
         strcpy(tmp_fname+(dollar-fname),value);
      strcpy(tmp_fname+(dollar-fname)+vlen,next);
      strncpy(fname,tmp_fname,maxlen-1);
      expansions++;
   }
   return expansions;
}

/* --------------------------- telrnh_ ------------------------------ */
/**
 *  @short Save aparameters from CORSIKA run header.
 *
 *  Get relevant parameters from CORSIKA run header block and
 *  write run header block to the data output file.
 *
 *  @param  runh CORSIKA run header block
 *  @return (none)
 * 
*/

void telrnh_ (cors_real_t runh[273])
{
#ifdef HAVE_EVENTIO_FUNCTIONS
   struct stat st;
   char tmp_fname[1024];
   char *orig_fname;
#endif
   double cors_ver_def = (double)(CORSIKA_VERSION)/1000.;
   if ( cors_ver_def > 50. ) /* Sometimes 5-digit version number */
      cors_ver_def *= 0.1;

#ifdef CATCH_SIGNALS
   /* Catch INTerrupt and TERMinate signals to stop program */
   signal(SIGINT,stop_signal_function);
   signal(SIGTERM,stop_signal_function);
#endif

   fflush(NULL);
   fprintf(stderr,"\n Using IACT/ATMO package version %s for CORSIKA %5.3f\n\n",
      IACT_ATMO_VERSION, cors_ver_def);
   fflush(NULL);

   nrun = (int) (runh[1]+0.1);
   corsika_version = (int)(runh[3]*1000.+0.5);

   /* Refuse to run with versions known to be no longer supported. */
   if ( corsika_version < 6400 || cors_ver_def <  6.400 )
   {
      fprintf(stderr,"\nCORSIKA versions below 6.400 are no longer supported.\n");
      fprintf(stderr,"Use version 1.47 or older of the IACT/ATMO (bernlohr) package with those.\n\n");
      exit(1);
   }

   /* Check if versions compiler for and running do match */
   if ( corsika_version != (int) (cors_ver_def*1000.) )
   {
      /* Unless more things change, it should work but caution the user */
      fprintf(stdout,
       "\n CORSIKA version is %5.3f but IACT interface was adapted to version %5.3f.\n",
          (double)runh[3], cors_ver_def);
      fprintf(stdout,
       " You might want to check that parameters passed are of matching types.\n\n");
      fflush(NULL);
   }

#ifdef HAVE_EVENTIO_FUNCTIONS
   /* Allocate I/O buffer for event data */
   if ( iobuf == 0 )
   {
      if ( (iobuf = allocate_io_buffer(1000000)) == (IO_BUFFER *) NULL )
      {
         fflush(NULL);
         fprintf(stderr,"No I/O buffer can be allocated.\n");
         exit(1);
      }

      /* The maximum allowed buffer size is controlled by an environment variable */
      if ( getenv("CORSIKA_IO_BUFFER") != 0 )
      {
         char *s = getenv("CORSIKA_IO_BUFFER");
         long nb = atol(s);
         long bs = 1;
         if ( strstr(s,"MiB") != NULL )
            bs = 1024L*1024L;
         else if ( strstr(s,"GiB") != NULL )
            bs = 1024L*1024L*1024L;
         else if ( strstr(s,"M") != NULL || strstr(s,"MB") != NULL || 
              (nb < 64000 && *s == '\0') )
            bs = 1000000L;
         else if ( strstr(s,"G") != NULL || strstr(s,"GB") != NULL )
            bs = 1000000000L;
         if ( sizeof(long) <= 4 && nb*(bs/1000000L) > 2047 /* 2147 for non-"i" */ )
         {
            fprintf(stderr,"Requested buffer size is too large for this system.\n");
            nb = 2147;
            bs = 1000000L;
         }
         if ( (size_t)(nb*bs) > max_io_buffer )
            max_io_buffer = (size_t)(nb*bs);
      }


      /* The maximum number of bunches (before thinning sets in) can be controlled as well. */
      if ( getenv("CORSIKA_MAX_BUNCHES") != 0 )
      {
         long nb = atol(getenv("CORSIKA_MAX_BUNCHES"));
         if ( nb >= 1000 && nb < 1000000000L )
            max_bunches = nb;
      }
      else
      {
         char s[40];
         snprintf(s,sizeof(s)-1,"%ld",max_bunches);
         setenv("CORSIKA_MAX_BUNCHES",s,1);
      }

#ifdef HAVE_EVENTIO_EXTENDED_LENGTH
      /* Large buffer sizes need a modification to the data format only */
      /* available with not-too-old eventio versions. Reading these data */
      /* with versions capable of the extended length is automatic but */
      /* to make real use of it you should run on a 64-bit machine with */
      /* sizeof(long) > 4. Otherwise you will be limited to 2 GB. */
      /* Old eventio version are not able to read the extended length format. */
      /* For the sake of simplicity the extended format is always used, */
      /* no matter if it is really needed for a particular data block. */

      if ( max_io_buffer > 1073741823UL )
      {
         printf(" Using the extended length format to accommodate large data blocks.\n");
         iobuf->extended = 1;

         if ( sizeof(long) <= 4 )
         {
            printf(" On this system only buffer lenghs up to 2^31-1 bytes can be used.\n");
            printf(" Use a 64-bit system to make full use of large buffers.\n");
         }
      }
#else
      if ( max_io_buffer > 1073741823UL )
      {
         fprintf(stderr, "Data format cannot handle buffer sizes beyond 2^30-1 bytes. Buffer size reduced.\n");
         max_io_buffer = 1073741823UL;
      }
#endif

      /* If you ever get a message that the I/O buffer could not be     */
      /* extended but you think you have enough memory in your machine, */
      /* increase the following maximum (in units of bytes):            */
      if ( max_io_buffer != MAX_IO_BUFFER )
         printf(" Using a maximum output buffer size of %ld MB for the IACT module.\n\n",
             (long)(max_io_buffer/1000000));

      iobuf->max_length = max_io_buffer;

      if ( output_fname == NULL )
         output_fname = "telescope.dat";

      orig_fname = output_fname;
      if ( strchr(output_fname,'$') != NULL )
      {
         strncpy(tmp_fname,output_fname,sizeof(tmp_fname)-1);
         expand_env(tmp_fname,sizeof(tmp_fname));
         output_fname = tmp_fname;
      }

#ifdef PIPE_OUTPUT
      /* Output can be to a pipe if the first (remaining) character is a '|'. */
      if ( output_fname[0] == '|' )
      {
      	 int i, l;
         char pv[64];
         snprintf(pv,sizeof(pv)-1,"%d",(int)getpid());
         setenv("CORSIKA_PID",pv,1);
	 l = strlen(output_fname);
	 for (i=1; i<l; i++)
	 {
	    /* Check that no shell metacharacters are in the string */
	    if ( !isalnum(output_fname[i]) &&
	         strchr(" \t=_-+.,:%%\'\"/@",output_fname[i]) == NULL )
	    {
	       fflush(NULL);
	       fprintf(stderr,"Invalid character '%c' in output pipe string.\n",
	          output_fname[i]);
	       exit(1);
	    }
	 }
      	 iobuf->output_file = popen(output_fname+1,"w");
      }
      else
#endif
      {
      	 /* Open output file in append mode to make sure that existing */
      	 /* data is not overwritten. */
#ifndef NO_FILEOPEN
         iobuf->output_file = fileopen(output_fname,"a");
#else
#ifdef __USE_LARGEFILE64
         /* With explicit support for large files on 32-bit machines. */
         iobuf->output_file = fopen64(output_fname,"a");
#else
         /* Support for large files is implicit or not available. */
         iobuf->output_file = fopen(output_fname,"a");
#endif
#endif
      }

      output_fname = orig_fname;

      if ( iobuf->output_file == NULL )
      {
         fflush(NULL);
         perror(output_fname);

         if ( errno == EACCES || errno == ESPIPE )
         {
            fprintf(stderr,
             "In most cases this error message means that you have the data file named\n");
            fprintf(stderr,"'%s' left over from a previous run.\n",
               output_fname);
            fprintf(stderr,
             "You may append new data to this file if you enable write permissions\n");
            fprintf(stderr,"to the data file before restarting this program.\n");
            fprintf(stderr,"Otherwise rename or remove the data file first.\n");
         }
         exit(1);
      }
   }
#else
   fflush(NULL);
   fprintf(stderr,"\n You don't have IACT Cherenkov light output functions.\n");
   fprintf(stderr," The fallback solution is to use CORSIKA output.\n");
   fprintf(stderr," Note that CORSIKA output files contain no information on\n");
   fprintf(stderr," telescope positions or random offsets of telescope systems.\n\n");
#endif
   { int nht = runh[4];
     if ( nht>0 && nht <= 10 )
       obs_height = runh[4+nht];
     else
       obs_height = -100.;
   }
#ifdef HAVE_EVENTIO_FUNCTIONS
   if ( write_tel_block(iobuf,IO_TYPE_MC_RUNH,(int)runh[1],runh,273) != 0 )
      ioerrorcheck();
   if ( write_input_lines(iobuf,&corsika_inputs) != 0 )
      ioerrorcheck();
   fflush(iobuf->output_file);

   /* Setting file to read-only is delayed until here, so that */
   /* it also works with gzip/bzip2 compressed files. */
   if ( fstat(fileno(iobuf->output_file),&st) != 0 )
      perror("Error getting access mode of output file (fstat)");
#ifdef S_ISFIFO
   else if ( !S_ISFIFO(st.st_mode) )
#else
   else if ( !((st.st_mode & S_IFMT) == S_IFIFO) )
#endif
   {
      /* Disable writing by other programs. User must enable write */
      /* bit by hand if appending of other data is wanted later on. */
      fchmod(fileno(iobuf->output_file),st.st_mode&~(unsigned)0333);
   }
   else if ( output_fname[0] == '|' )
   {
      printf("Output is piped to %s (ifmt=0%d%d)\n", output_fname+1,
         (st.st_mode & 0100000) >> 15, (st.st_mode & 0070000) >> 12 );
   }
   else if ( stat(output_fname,&st) != 0 )
   {
      if ( errno != ENOENT )
      {
         fprintf(stderr, "%s: ", output_fname);
         perror("Error getting access mode of output file (stat)");
      }
      else
         fprintf(stderr, "Output file %s not yet created.\n", output_fname);
   }
   else
   {
      /* Disable writing by other programs. User must enable write */
      /* bit by hand if appending of other data is wanted later on. */
      chmod(output_fname,st.st_mode&~(unsigned)0333);
   }
#endif

   all_photons_run = 0.;
   all_bunches_run = 0.;

   primary_file = fopen(primary_path, "rb");

}

/* ---------------------------- tellni_ -------------------------- */
/**
 *  @short Keep a record of CORSIKA input lines.
 *
 *  Add a CORSIKA input line to a linked list of strings which
 *  will be written to the output file in eventio format right
 *  after the run header.
 *
 *  @param  line     input line (not terminated)
 *  @param  llength  maximum length of input lines (132 usually)
 *
*/

void tellni_ (char *line, int *llength)
{
   int len = *llength, i;
   struct linked_string *xl, *xln;
   char myline[512];
   
   if ( *corsika_inputs_head == '\0' )
   {
      double cors_ver_def = (double)(CORSIKA_VERSION)/1000.;
      if ( cors_ver_def > 50. ) /* Sometimes 5-digit version number */
         cors_ver_def *= 0.1;
      snprintf(corsika_inputs_head, sizeof(corsika_inputs_head)-1,
        "* CORSIKA %5.3f + IACT/ATMO %s inputs:",
        cors_ver_def, IACT_ATMO_VERSION);
   }

   /* Skip backwards over trailing blanks. */
   for (i=len-1; i>0; i--)
      if ( line[i] == ' ' )
      	 len--;
      else
      	 break;

   /* We may have some configuration concerning this module */
   if ( len>0 && (size_t)len < sizeof(myline) )
   {
      strncpy(myline,line,len);
         myline[len] = '\0';
      if ( strncmp(myline,"IACT ",5) == 0 )
         iact_param(myline+5);
      else if ( strncmp(myline,"* (IACT) ",9) == 0 )
         iact_param(myline+9);
      else if ( strncmp(myline,"*(IACT) ",8) == 0 )
         iact_param(myline+8);
   }

   /* Search end of linked list */
   for (xl=&corsika_inputs; xl->next != NULL; xl=xl->next)
      ;

   /* Append new line */
   if ( len > 0 )
      if ( (xln = (struct linked_string *) calloc((size_t)1+EXTRA_MEM_2,sizeof(struct linked_string))) != NULL )
      {
         if ( (xln->text = (char *) malloc((size_t)(len+1+EXTRA_MEM_3))) != NULL )
         {
            if ( len > 0 )
      	       strncpy(xln->text,line,(size_t)len);
	    xln->text[len] = '\0';
	    xl->next = xln;
         }
      }
}

/* ----------------------- is_on ------------------ */

static int is_on (char *word)
{
   if ( strcasecmp(word,"on") == 0 ||
        strcasecmp(word,"yes") == 0 ||
        strcasecmp(word,"Y") == 0 ||
        strcasecmp(word,"True") == 0 ||
        strcasecmp(word,"T") == 0 ||
        strcasecmp(word,"1") == 0 )
      return 1;
   else
      return 0;
}

/* ----------------------- is_off ------------------ */

static int is_off (char *word)
{
   if ( strcasecmp(word,"off") == 0 ||
        strcasecmp(word,"no") == 0 ||
        strcasecmp(word,"N") == 0 ||
        strcasecmp(word,"False") == 0 ||
        strcasecmp(word,"F") == 0 ||
        strcasecmp(word,"0") == 0 )
      return 1;
   else
      return 0;
}

/* ------------------------- iact_param ------------------------- */
/** @short Processing of IACT module specific parameters in Corsika input.
 *
 *  @param text Text following the IACT keyword on the input line.
 *
 */

static void iact_param (char *text)
{
   char word[128], word2[128];
   int ipos = 0;
   char *s = strchr(text,'#');

   printf("\n IACT control parameter line: %s\n", text);

   /* If there are comments appended, strip them off */
   if ( s != NULL )
   {
      int l;
      *s = '\0';
      if ( strlen(text) == 0 )
         return;
      for (l=strlen(text)-1; l>=0; l--)
         if ( text[l] == ' ' || text[l] == '\t' )
            text[l] = '\0';
         else
            break;
   }
   if ( getword(text,&ipos,word,sizeof(word)-1,' ','\n') <= 0 )
      return;
   if ( strcasecmp(word,"TELFIL") == 0 )
      telfil_(text+ipos);
   else if ( strcasecmp(word,"TELSAMPLE") == 0 )
      telsmp_(text+ipos);
   else if ( strcasecmp(word,"impact_correction") == 0 )
   {
      if ( getword(text,&ipos,word,sizeof(word)-1,' ','\n') <= 0 )
         return;
      if ( is_on(word) )
         impact_correction = 1;
      else if ( is_off(word) )
         impact_correction = 0;
   }
   else if ( strcasecmp(word,"print_events") == 0 )
   {
      /* See the first five colon separated numbers after the TELFIL */
      /* file name. The reason we offer a separate keyword here is to */
      /* reduce problems with exceeding CORSIKA's input line length. */
      sscanf(text+ipos,"%d %d %d %d %d",
         &max_print_tel, &max_print_evt, &skip_print, 
         &skip_print2, &skip_off2);
      if ( max_print_evt < max_print_tel )
         max_print_evt = max_print_tel;
   }
   else if ( strcasecmp(word,"internal_bunches") == 0 )
   {
      /* The maximum number of photon bunches before using external storage. */
      /* See the sixth colon separated number after the TELFIL */
      /* file name, as described for the telfil_ function. */
      if ( atoi(text+ipos) > max_internal_bunches )
         max_internal_bunches = atoi(text+ipos);
   }
   else if ( strcasecmp(word,"max_bunches") == 0 )
   {
      long nb;
      word2[0] = '\0';
      getword(text,&ipos,word2,sizeof(word2)-1,' ','\n');
      nb = atol(word2);
      if ( nb >= 1000 && nb < 1000000000L )
      {
         max_bunches = nb;
         setenv("CORSIKA_MAX_BUNCHES",word2,1);
      }
   }
   else if ( strcasecmp(word,"io_buffer") == 0 )
   {
      size_t nb=0, bs=1;
      /* The maximum size of the output buffer (usually in Megabytes). */
      /* See the seventh colon separated number after the TELFIL */
      /* file name, as described for the telfil_ function. */
      word2[0] = '\0';
      getword(text,&ipos,word2,sizeof(word2)-1,' ','\n');
      nb = atoi(word2);
      if ( strstr(word2,"Mi") != NULL || strstr(word2,"MiB") != NULL)
         bs = 1024*1024;
      else if ( strstr(word2,"M") != NULL || strstr(word2,"MB") != NULL )
         bs = 1000000;
      else if ( strstr(word2,"Gi") != NULL || strstr(word2,"GiB") != NULL )
         bs = 1024L*1024L*1024L;
      else if ( strstr(word2,"G") != NULL || strstr(word2,"GB") != NULL )
         bs = 1000000000L;
      else if ( nb < 64000 ) /* Very small numbers are implicity Megabytes. */
         bs = 1000000;
      if ( sizeof(long) <= 4 && nb*(bs/1000000L) > 2147 )
      {
         fprintf(stderr,"Requested buffer size is too large for this system.\n");
         nb = 2147;
         bs = 1000000L;
      }
      if ( nb*bs >= 1000000 )
         max_io_buffer = nb*bs;
      setenv("CORSIKA_IO_BUFFER",word2,1);
   }
   else if ( strcasecmp(word,"extprim") == 0 )
   {
      extprim_setup(text+ipos);
   }
   else if ( strcasecmp(word,"individual") == 0 || 
             strcasecmp(word,"split-always") == 0 ||
             strcasecmp(word,"split_always") == 0 )
   {
      /* We want to write the photon data in individual blocks for each
         telescope. This may save a substantial amount of memory when
         dealing with many telescopes but could be otherwise less efficient,
         in particular when combined with the sequential option of
         multipipe_corsika. */
      tel_individual = 1;
      printf(" Activating split mode.\n");
   }
   else if ( strcasecmp(word,"auto-split") == 0 || 
             strcasecmp(word,"split-auto") == 0 || 
             strcasecmp(word,"split_auto") == 0 || 
             strcasecmp(word,"auto_split") == 0 )
   {
      /* We want to write the photon data in individual blocks only for
         events with many photon bunches across an array. Otherwise there
         is no real concern of saving memory and we can write data for
         the whole array in one block */
      tel_individual = 2;
      word2[0] = '\0';
      if ( getword(text,&ipos,word2,sizeof(word2)-1,' ','\n') > 0 )
      {
         size_t l = strlen(word2);
         char lastchar = '\0';
         if ( l>0 )
            lastchar = word2[l-1];
         if ( atol(word2) > 0 )
         {
            tel_split_threshold = atol(word2);
            if ( lastchar == 'k' || lastchar == 'K' )
               tel_split_threshold *= 1000;
            else if ( lastchar == 'm' || lastchar == 'M' )
               tel_split_threshold *= 1000000;
         }
         printf(" Activating auto-split mode above %lu bunches.\n", 
            (unsigned long) tel_split_threshold);
      }
      else
      	 printf(" Activating auto-split mode (current threshold: %lu bunches)\n",
            (unsigned long) tel_split_threshold);
   }
   else
   {
      fprintf(stderr,"\n\n Unknown IACT control parameter line: %s\n\n",
         word);
      exit(1); /* In the tradition of CORSIKA, everything unknown is fatal. */
   }
}

/* ---------------------------- telrne_ -------------------------- */
/**
 *  @short Write run end block to the output file.
 *
 *  @param  rune  CORSIKA run end block
 *
*/

void telrne_ (cors_real_t rune[273])
{
#ifdef HAVE_EVENTIO_FUNCTIONS
    if ( write_tel_block(iobuf,IO_TYPE_MC_RUNE,(int)rune[1],rune,3) != 0 )
       ioerrorcheck();
#endif
   printf("\n Total number of photons produced in this run: %f in %f bunches\n\n",
      all_photons_run, all_bunches_run);

#ifndef NO_EVENTIO
   if ( iobuf != NULL )
   {
      if ( iobuf->output_file != NULL )
         fileclose(iobuf->output_file);
      iobuf->output_file = NULL;
   }
#endif

   fclose(primary_file);
}

/* --------------------------- telasu_ --------------------------- */
/**
 *  @short Setup how many times each shower is used.
 *
 *  Set up how many times the telescope system should be
 *  randomly scattered within a given area. Thus each telescope
 *  system (array) will see the same shower but at random offsets.
 *  Each shower is thus effectively used several times.
 *  This function is called according to the CSCAT keyword in the
 *  CORSIKA input file.
 *
 *  @param n   The number of telescope systems
 *  @param dx  Core range radius (if dy==0) or core x range
 *  @param dy  Core y range (non-zero for ractangular, 0 for circular)
 *  @return (none)
 *
*/

void telasu_ (int *n, cors_real_dbl_t *dx, cors_real_dbl_t *dy)
{
   core_range = core_range1 = *dx;
   core_range2 = *dy;
   nsys = *n;
}

/* --------------------------- telset_ ---------------------------- */
/**
 *  @short Add another telescope to the system (array) of telescopes.
 *
 *  Set up another telescope for the simulated telescope system.
 *  No details of a telescope need to be known except for a
 *  fiducial sphere enclosing the relevant optics.
 *  Actually, the detector could as well be a non-imaging device.
 *
 *  This function is called for each TELESCOPE keyword in the
 *  CORSIKA input file.
 *
 *  @param  x  X position [cm]
 *  @param  y  Y position [cm]
 *  @param  z  Z position [cm]
 *  @param  r  radius [cm] within which the telescope is fully contained
 *  @return (none)
 *
*/

void telset_ (cors_real_now_t *x, cors_real_now_t *y, 
   cors_real_now_t *z, cors_real_now_t *r)
{
   int itel;
   double d;
   
   if ( ((char *) x) + sizeof(cors_real_now_t) != (char *) y )
   {
      fprintf(stderr,
         "\nReal numbers in IACT code are treated as REAL*%d numbers\n",
         (int)sizeof(cors_real_now_t));
      fprintf(stderr,"but CORSIKA passes them as REAL*%d.\n",
         (int)((char *)y-(char *)x));
      exit(1);
   }
   
   if ( ntel >= MAX_ARRAY_SIZE )
   {
      fprintf(stderr,"\nToo many telescopes. Do you really have that many telescopes/detectors?\n");
      fprintf(stderr,"A little tip: increase MAX_ARRAY_SIZE in iact.c and recompile.\n");
      exit(1);
   }
   xtel[ntel] = *x;
   ytel[ntel] = *y;
   d = sqrt(xtel[ntel]*xtel[ntel]+ytel[ntel]*ytel[ntel]);
   if ( d > dmax )
      dmax = d;
   ztel[ntel] = *z + raise_tel;
   rtel[ntel] = *r;
   if ( rtel[ntel] > rmax ) 
      rmax = rtel[ntel];
   /* In order to have even the Cherenkov light from the last few meters, */
   /* all telescope z coordinates should be non-negative. */
   if ( ztel[ntel]-rtel[ntel] < 0. )
   {
      raise_tel -= ztel[ntel]-rtel[ntel];
      for (itel=0; itel<ntel; itel++)
         ztel[itel] -= ztel[ntel]-rtel[ntel];
      ztel[ntel] = rtel[ntel];
   }
   ntel++;
}

/* ------------------------- get_impact_offset ------------------------- */
/**
 *  @short Approximate impact offset of primary due to geomagnetic field.
 *
 *  Get the approximate impact offset of the primary particle due to
 *  deflection in the geomagnetic field. The approximation that the curvature
 *  radius is large compared to the distance travelled is used.
 *  The method is also not very accurate at large zenith angles where
 *  curvature of the atmosphere gets important. Therefore a zenith
 *  angle cut is applied and showers very close to the horizon are skipped.
 *  Only the offset at the lowest detection level is evaluated.
 *
 *  @param  evth    CORSIKA event header block
 *  @param  prmpar  CORSIKA primary particle block. We need it to get the
 *                  particle's relativistic gamma factor (prmpar[2] or prmpar[1],
 *                  depending on the CORSIKA version).
 *  @return (none)
 *
*/

void get_impact_offset (cors_real_t evth[273], cors_real_dbl_t prmpar[PRMPAR_SIZE])
{
   int type = (int)(evth[2]+0.5);
   int type2 =(int)(prmpar[0]+0.5);
   int curved_flag = (int)(evth[78]+0.5);

   impact_offset[0] = impact_offset[1] = 0.;

   if ( type != type2 || type <= 0 || type >= 26099 )
   {
      fprintf(stderr,"Inconsistent particle type. Skipping get_impact_offset()\n");
      return;
   }

   if ( type == 1 )  /* Gammas are not deflected */
      return;

   if ( evth[6] >= 0. )  /* With TSTART set to true, no deflection was applied in CORSIKA */
      return;

   {
      double cosz = cos(evth[10]);
      double Bxc = evth[70] * 1e-6;
      double Bzc = evth[71] * 1e-6;
      double phiB = evth[92];
      double Bx = Bxc*cos(phiB);
      double By = -Bxc*sin(phiB);
      double Bz = -Bzc;
      double theta = evth[10];
      double phi = evth[11] - evth[92];
#ifdef DEBUG_IMPACT
      double B = sqrt(Bxc*Bxc+Bzc*Bzc);
      double Bl = fabs(Bx*sin(theta)*cos(phi) + By*sin(theta)*sin(phi) + Bz*cos(theta));
      double Bt = (Bl<B?sqrt(B*B-Bl*Bl):0.);
#endif
      double charge = 0;
      double mass = 0.;
      double E = evth[3];
      double p = E;
      double gamma = prmpar[1];
      double beta = 1.;
      double c = 2.99792458e8; /* m/s */
      double e = 1.602e-19; /* Coulomb */
      double psi = p*1e9*e/c;
      double dx = 0., dy = 0., dz = 0.;
      double vx = 0., vy = 0., vz = c;
#ifdef DEBUG_IMPACT
      double px = 0., py = 0., pz = p;
      double R = 1e10;
      double vx1 = 0., vy1 = 0., vz1 = c;
      double vx2 = 0., vy2 = 0., vz2 = c;
#endif
      double Fx = 0., Fy = 0., Fz = 0.;
      double t0 = fabs(evth[4]);
      double h0 = heigh_(&t0);
      double dist = (h0-obs_height)/cosz * 1e-2;
#ifdef DEBUG_IMPACT
      double t1;
#endif
      double t2;

      if ( fabs(cosz-prmpar[curved_flag?15:2]) > 1e-5 )
      {
         fprintf(stderr,"Inconsistent zenith angle information: %f versus %f.\n"
            "Skipping get_impact_offset()\n",
            cosz, prmpar[curved_flag?15:((CORSIKA_VERSION>=6400)?2:3)]);
         return;
      }
      if ( cosz < 0.1 )
         return; /* Too large zenith angle or even upwards. Cannot correct. */

      if ( type >= 100 )
      {
         charge = type%100;
         mass = (0.931494-0.000511)*(int)(type/100); /* nuclear mass */
         switch ( type ) /* more accurate masses for a few nuclei */
         {
            case 402: /* 4He */
               mass = 0.931845*4.;
               break;
         }
      }
      else if ( type > 1 )
      {
         switch ( type )
         {
            case 2: /* positron */
               charge = 1;
               mass = 0.000511;
               break;
            case 5: /* mu+ */
               charge = 1;
               mass = 0.105658;
               break;
            case 8: /* pi+ */
               charge = 1;
               mass = 0.13957;
               break;
            case 11: /* K+ */
               charge = 1;
               mass = 0.493677;
               break;
            case 14: /* proton */
               charge = 1;
               mass = 0.938272;
               break;
            case 3: /* electron */
               charge = -1;
               mass = 0.000511;
               break;
            case 6: /* mu- */
               charge = -1;
               mass = 0.105658;
               break;
            case 9: /* pi- */
               charge = -1;
               mass = 0.13957;
               break;
            case 12: /* K- */
               charge = -1;
               mass = 0.493677;
               break;
            case 15: /* antiproton */
               charge = -1;
               mass = 0.938272;
               break;
            case 13: /* neutron */
               charge = 0;
               mass = 0.939;
               break;
            case 66: /* neutrinos */
            case 67:
            case 68:
            case 69:
               charge = 0;
               mass = 1e-8;
               break;
            default:
               fprintf(stderr,"Primary type %d not supported in get_impact_offset()\n",type);
               return;
         }
      }

#ifdef DEBUG_IMPACT
printf(" Particle type %d, mass = %f GeV/c^2, E= %g GeV, gamma = %f (%f), distance = %f km\n",
  type, mass, E, gamma, E/mass, dist*1e-3);
#endif

      if ( charge == 0 )
         return;
      if ( mass > 0. && fabs(gamma/(E/mass)-1.0) > 1e-3 )
      {
         static int warned = 0;
         if ( warned < type )
         {
            fprintf(stderr,"Nuclear masses in CORSIKA and IACT module differ:"
                "%g vs. %g GeV/c**2.\n", E/gamma, mass);
            warned = type;
         }
      }
      if ( mass > 0. && fabs(gamma/(E/mass)-1.0) > 1e-2 )
      {
         fprintf(stderr,"Inconsistent gamma factor: %g vs. %g.\n"
            "Skipping get_impact_offset()\n", gamma, E/mass);
         return;
      }
      if ( mass > 0. && mass < E )
         p = sqrt(E*E-mass*mass); /* GeV/c */
      psi = p*1e9*e/c; /* momentum in SI units */
      if ( gamma > 1. )
         beta = sqrt(1.-1./(gamma*gamma));
      t2 = dist/(beta*c);
#ifdef DEBUG_IMPACT
      t1 = 0.5*t2;
      px = psi*sin(theta)*cos(phi); /* kg m/s */
      py = psi*sin(theta)*sin(phi);
      pz = -psi*cos(theta);
#endif
      vx = beta*c*sin(theta)*cos(phi); /* m/s */
      vy = beta*c*sin(theta)*sin(phi);
      vz = -beta*c*cos(theta);
      Fx = charge*e*(vy*Bz - vz*By);
      Fy = charge*e*(vz*Bx - vx*Bz);
      Fz = charge*e*(vx*By - vy*Bx);

#ifdef DEBUG_IMPACT
      if ( charge != 0. && Bt != 0. )
         R = p / (0.299782e2 * charge * Bt);
      printf("   R = %f m\n",R);
      printf("   p = %g kg*m/s, beta = %f, gamma = %f\n", psi, beta, gamma);
      printf("   px/p = %f, py/p = %f, pz/p = %f kg m/s\n", px/psi, py/psi, pz/psi);
      printf("   Bx = %f, By = %f, Bz = %f nT\n", Bx*1e9, By*1e9, Bz*1e9);
      printf("   Fx/p = %f, Fy/p = %f, Fz/p = %f\n", Fx/psi, Fy/psi, Fz/psi);

      printf("   Starting altitude: %f g/cm**2 -> %f km\n", evth[4], h0*1e-5);
      printf("   Ground altitude:  %f km\n", obs_height*1e-5);
      printf("   Distance to travel: %f km\n", dist*1e-3);
      printf("   Time to travel: %f s, v = %f m/s\n", t2, beta*c);

      vx1 = vx + t1*Fx/psi*(beta*c);
      vy1 = vy + t1*Fy/psi*(beta*c);
      vz1 = vz + t1*Fz/psi*(beta*c);
      vx2 = vx + t2*Fx/psi*(beta*c);
      vy2 = vy + t2*Fy/psi*(beta*c);
      vz2 = vz + t2*Fz/psi*(beta*c);

      printf("   vx0 = %f m/s, vy0 = %f m/s, vz0 = %f m/s\n", vx, vy, vz);
      printf("   vx2 = %f m/s, vy2 = %f m/s, vz2 = %f m/s\n", vx2, vy2, vz2);
      printf("   Bending of direction: %f deg\n",(180./M_PI) *
               acos((vx*vx2+vy*vy2+vz*vz2) /
                  sqrt(vx*vx+vy*vy+vz*vz) /
                  sqrt(vx2*vx2+vy2*vy2+vz2*vz2)));

      dx = (0.25*(vx+2*vx1+vx2)*t2 - vx*t2);
      dy = (0.25*(vy+2*vy1+vy2)*t2 - vy*t2);
      dz = (0.25*(vz+2*vz1+vz2)*t2 - vz*t2);
      printf("   Offsets(1): dx = %f m, dy = %f m, dz = %f m\n", dx, dy, dz);
      /* Extrapolate/interpolate from the offset point to the CORSIKA */
      /* detection level with the final velocity vector. */
      impact_offset[0] = (dx-dz*vx2/vz2) * 100.; /* in cm */
      impact_offset[1] = (dy-dz*vy2/vz2) * 100.; /* in cm */
      printf("   Impact offset(1): dxc = %f m, dyc = %f m\n", 
         impact_offset[0]*0.01, impact_offset[1]*0.01);
#endif
      
      /* These dx, dy, dz offsets are identical to the ones above. */
      dx = 0.5*t2*Fx/psi*t2*(beta*c);
      dy = 0.5*t2*Fy/psi*t2*(beta*c);
      dz = 0.5*t2*Fz/psi*t2*(beta*c);
      /* Simplified version: extrapolate to detection level with 
         initial velocity vector */
      impact_offset[0] = (dx-dz*vx/vz) * 100.; /* in cm */
      impact_offset[1] = (dy-dz*vy/vz) * 100.; /* in cm */

#ifdef DEBUG_IMPACT
      printf("   Offsets(2): dx = %f m, dy = %f m, dz = %f m\n", dx, dy, dz);
#endif

      if ( do_print )
         printf(" Impact offset: dxc = %f m, dyc = %f m\n", 
            impact_offset[0]*0.01, impact_offset[1]*0.01);
   }
}

/* --------------------------- televt_ ------------------------ */
/**
 *  @short Start of new event. Save event parameters.
 *
 *  Start of new event: get parameters from CORSIKA event header block,
 *  create randomly scattered telescope systems in given area, and
 *  write their positions as well as the CORSIKA block to the data file.
 *
 *  @param  evth    CORSIKA event header block
 *  @param  prmpar  CORSIKA primary particle block
 *  @return (none)
 *
*/

void televt_ (cors_real_t evth[273], cors_real_dbl_t prmpar[PRMPAR_SIZE])
{
#ifdef HAVE_EVENTIO_FUNCTIONS
   static int telpos_written = 0;
#endif
/*
 *    If iact.c is used but atmo.c is not, then compile iact.c with
 *    the -DNO_EXTERNAL_ATMOSPHERES compiler switch.
*/
#ifndef NO_EXTERNAL_ATMOSPHERES
   /* The model atmosphere no. is declared in atmo.c and either left zero */
   /* if the CORSIKA internal atmospheric profiles are used or set to */
   /* the user-defined atmosphere model number. */
   extern int atmosphere; 
#else
   /* No atmosphere extensions used; thus take CORSIKA atm. for granted. */
   static int atmosphere = 0;
#endif
   static int first = 1; /* For things to be written only at the start */
   static int thinning = 0;
   int options = 0;
   int written = 0;
   int i;
   double cos_oa;

   if ( first )
   {
      double Bxc = evth[70] * 1e-6;
      double Bzc = evth[71] * 1e-6;
      double phiB = evth[92];
      Bfield[0] = Bxc*cos(phiB);
      Bfield[1] = -Bxc*sin(phiB);
      Bfield[2] = -Bzc;
   }
   pprim[0] = evth[7];
   pprim[1] = evth[8];
   pprim[2] = -evth[9];
   cross_prod(Bfield,pprim,byplane);
   cross_prod(pprim,byplane,bxplane);
   {
      double nx = norm3(bxplane);
      double ny = norm3(byplane);
      if ( nx != 0. && ny != 0. )
      {
         norm_vec(bxplane);
         norm_vec(byplane);
      }
      else /* B field zero or parallel to primary */
      {
         double xn[3] = { 1., 0., 0. };
         /* Use North instead of B field */
         cross_prod(xn,pprim,byplane);
         cross_prod(pprim,byplane,bxplane);
         nx = norm3(bxplane);
         ny = norm3(byplane);
         if ( nx != 0. && ny != 0. )
         {
            norm_vec(bxplane);
            norm_vec(byplane);
         }
         else /* unexpected; fall back to horizontal detector plane */
         {
            bxplane[0] = byplane[1] = 1.;
            bxplane[1] = bxplane[2] = byplane[0] = byplane[2] = 0.;
         }
      }
   }


   all_photons = 0.;
   all_bunches = 0.;
   stored_bunches = 0;

   fflush(stdout);
   if ( ntel == 0 )
   {
      fprintf(stderr,
    "\n No telescopes set up. See the TELESCOPE keyword in the User's Guide.\n");
      exit(1);
   }
   event_number = (int)(evth[1]+0.5);
   /* Angles coming in radians: */
   theta_prim = evth[10];
   phi_prim = evth[11] - evth[92];
   if ( phi_prim >= 2.*M_PI )
      phi_prim -= 2.*M_PI;
   if ( phi_prim < 0.)
      phi_prim += 2.*M_PI;
#ifdef SHOW_ANGLE
   cx_prim = cos(phi_prim) * sin(theta_prim);
   cy_prim = sin(phi_prim) * sin(theta_prim);
   cz_prim = -cos(theta_prim);
#endif
   /* Angles coming in degrees: */
   theta_central = 0.5*(evth[80]+evth[81])*((double)(M_PI)/180.);
   if ( evth[83] >= evth[82] )
      phi_central = 0.5*(evth[82]+evth[83])*((double)(M_PI)/180.);
   else
   {
      phi_central = 0.5*(evth[82]+360.+evth[83])*((double)(M_PI)/180.);
   }
   phi_central -= evth[92];
   if ( phi_central >= 2.*M_PI )
      phi_central -= 2.*M_PI;
   if ( phi_central < 0.)
      phi_central += 2.*M_PI;

   ush  = sin(theta_prim)*cos(phi_prim);
   vsh  = sin(theta_prim)*sin(phi_prim);
   wsh  = cos(theta_prim);
   ushc = sin(theta_central)*cos(phi_central);
   vshc = sin(theta_central)*sin(phi_central);
   wshc = cos(theta_central);
   cos_oa = ush*ushc + vsh*vshc + wsh*wshc;
   if ( cos_oa >= 1. ) /* Catch possible rounding errors */
      off_axis = 0.;
   else
      off_axis = acos(cos_oa);

   lambda1 = evth[95];
   lambda2 = evth[96];
   energy  = evth[3];
   primary = (int) (evth[2]+0.5);
   
   { double oht = obs_height;
#ifndef NO_EXTERNAL_ATMOSPHERES
   if ( atmosphere > 0 )
      airlightspeed = 29.9792458 / refidx_(&oht);
   else
#endif
      airlightspeed = 29.9792458 / (1.+ (0.000283 * 994186.38 / 1222.656)*rhof_(&oht));
   }

   /* If the time is counted since the primary entered the atmosphere, */
   /* this is indicated by a negative number in the height of the first */
   /* interaction. */
   if ( evth[6] < 0. )
   {
      double t = 0.;
      toffset = (heigh_(&t)-obs_height) / cos(evth[10]) / 29.9792458;
      first_int = -evth[6];
   }
   else /* Time is counted since first interaction. */
   {
      toffset = (evth[6]-obs_height) / cos(evth[10]) / 29.9792458;
      first_int = evth[6];
   }

   /* Add atmospheric profile to Cherenkov flag in CORSIKA event header */
   /* if not yet present and do a few sanity checks. */
   options = (int)(evth[76]+0.5);
   if ( (options & 0x02) == 0 )
   {
      if ( first ) fprintf(stdout,
         "\n This CORSIKA version does not yet properly identify all options\n"
         " relevant for Cherenkov light production in EVTH(77).\n\n");
      options = (options & 0x3ff) | (atmosphere<=1023?atmosphere:1023 << 10);
      evth[76] = (cors_real_t) options;
   }
   else if ( (options >> 10) != atmosphere )
   {
      if ( first ) fprintf(stdout,
         "\n CORSIKA reports external atmosphere as number %d but we use %d.\n\n",
	 options >> 10, atmosphere);
      options = (options & 0x3ff) | (atmosphere<=1023?atmosphere:1023 << 10);
      evth[76] = (cors_real_t) options;
   }

   if ( (options & 0x20) != 0 )
   {
      if ( first ) fprintf(stdout,
         "\n CORSIKA was compiled with the VOLUMEDET option and the IACT option\n"
         " automatically adapts to that. This means that all random shower core\n"
         " offsets are counted in a plane perpendicular to the shower axis.\n"
         " For non-vertical showers, the horizontal offsets can therefore be\n"
         " larger than specified in your CORSIKA inputs.\n");
      options |= 0x80;
      evth[76] = (cors_real_t) options;
   }
   else
   {
      if ( first ) fprintf(stdout,
         "\n CORSIKA was compiled without the VOLUMEDET option and the IACT option\n"
         " automatically adapts to that. This means that all random shower core\n"
         " offsets are counted in a horizontal plane.\n");
   }

   if ( (options & 0x100) != 0 )
   {
      if ( first ) fprintf(stdout,
         "\n CORSIKA was compiled with the SLANT option and all longitudinal\n"
         " distributions are in slant depth units.\n");
   }
   else
   {
      if ( first ) fprintf(stdout,
         "\n CORSIKA was compiled without the SLANT option and all longitudinal\n"
         " distributions are in vertical depth units (the classical way).\n");
   }

   if ( (options & 0x04) == 0 && evth[84] < 3. )
   {
      if ( first ) fprintf(stdout,
      	 "\n You are using the IACT option (without CEFFIC) with a bunch size of %f.\n"
	 " You should be aware that this is inefficient with realistic detectors.\n"
	 " A bunch size of the order of 5 would usually be an adequate number for\n"
	 " imaging Cherenkov telescopes instrumented with ordinary photomultiplier tubes.\n",
	 evth[84]);
   }

   if ( (options & 0x04) != 0 && evth[84] > 1. )
   {
      if ( first ) fprintf(stdout,
      	 "\n You are using the IACT and CEFFIC options with a bunch size of %f.\n"
	 " Please keep in mind that this will result in correlated photo-electrons.\n",
	 evth[84]);
   }

   if ( !thinning && (evth[147] != 0. || evth[148] != 0.) )
   {
      fprintf(stdout,"\n CORSIKA is using the THIN option.\n");
      if ( use_compact_format )
      {
         fprintf(stdout,
            " The THIN option is not compatible with the compact bunch format.\n"
            " Switching to full bunch format.\n");
         use_compact_format = 0;
      }
      thinning = 1;
   }

   if ( use_compact_format ) /* We better check if it makes sense here */
   {
      int bad = 0;
      double cr = core_range;
      if ( core_range1 > cr )
         cr = core_range1;
      if ( core_range2 > cr )
         cr = core_range2;
      if ( evth[84] >= 327. )
         bad = 1;
      else if ( rmax / cos(theta_prim) > 32e2 )
         bad = 1;
      else if ( (cr+dmax+rmax) * sin(theta_prim) > 950e2 )
         bad = 1;
      if ( bad )
      {
         if ( first ) fprintf(stdout,
            "\n You selected to write output files in compact format but the configured\n"
            " values for bunch sizes, telescope sizes, positions, and random offsets\n"
            " together with the zenith angle indicate that this format is not appropriate\n"
            " and its inherent limitations would be violated.\n"
            " The compact bunch format is disabled now.\n");
         use_compact_format = 0;
      }
   }

   first = 0;
   do_print = 0;
   if ( (nevents+1)%skip_print == 0 )
   {
      if ( count_print_evt++ < max_print_evt )
      	 do_print = 1;
   }

   if ( do_print || (nevents+1-skip_off2)%skip_print2 == 0 )
   {
      fflush(NULL); /* to get FORTRAN and C output into sync */
      fprintf(stdout,
       "\n Start with event %d (E=%5.3f TeV, first interaction in %3.1f km height)\n",
	(int)evth[1],1e-3*energy,fabs(1e-5*evth[6]));
      fprintf(stdout,
      " Azimuth=%6.2f deg (S->E) which is %6.2f deg (N->E), zenith angle=%5.2f deg\n",
           phi_prim*(180./((double)M_PI)),
           180.-phi_prim*(180./((double)M_PI)) - 
           floor((180.-phi_prim*(180./((double)M_PI)))/360.)*360.,
           theta_prim*(180./((double)M_PI)));
/*
fprintf(stdout," Reference direction is %6.2f deg (S->E), %5.2f deg zenith angle\n",
  phi_central*(180./((double)M_PI)), theta_central*(180./((double)M_PI)));
*/
      written = 1;
   }

   if ( do_print )
      fprintf(stdout," Observation level is at an altitude of %1.0f m.\n",
           0.01*obs_height);

   if ( impact_correction )
      get_impact_offset(evth,prmpar);

   set_random_systems( theta_prim, phi_prim, theta_central, phi_central,
       off_axis, energy, primary, (options&0x20));

   /* Report as many offsets as possible back to CORSIKA header block */
   for ( i=0; i<20; i++ )
      evth[98+i] = evth[118+i] = 0.;
   for ( i=0; i<20 && i<nsys; i++ )
   {
      evth[98+i]  = xoffset[i];
      evth[118+i] = yoffset[i];
   }
   evth[98-1] = i;

   televt_done = 1;
   
#ifdef HAVE_EVENTIO_FUNCTIONS
   clear_shower_extra_parameters(get_shower_extra_parameters());

   if ( !telpos_written )
   {
      telpos_written = 1;
      if ( write_tel_pos(iobuf,ntel,xtel,ytel,ztel,rtel) != 0 ) /* 1201 */
         ioerrorcheck();
   }
   if ( write_tel_block(iobuf,IO_TYPE_MC_EVTH,(int)evth[1],evth,273) != 0 )
      ioerrorcheck();
   if ( sampling_fname != NULL ) 
   {
      /* Possibly non-uniform distribution: use weights. */
      if ( write_tel_offset_w(iobuf,nsys,toffset,xoffset,yoffset,weight) != 0 ) /* 1203 */
         ioerrorcheck();
   }
   else
   {
      /* Uniform distribution of core offsets: no weights needed. */
      if ( write_tel_offset(iobuf,nsys,toffset,xoffset,yoffset) != 0 ) /* 1203 */
         ioerrorcheck();
   }
   if ( do_print )
   {
      fprintf(stdout," Event header of event %d written to output file.\n",
      	 (int)(evth[1]+0.5));
      written = 1;
   }
   fflush(iobuf->output_file);
#endif
   if ( written )
   {
      fprintf(stdout,"\n");
      fflush(stdout);
   }
}

/* --------------------------- photon_hit ---------------------- */
/**
 *  @short Store a photon bunch for a given telescope in long format.
 *
 *  Store a photon bunch in the bunch list for a given telescope.
 *  It is kept in memory or temporary disk storage until the end
 *  of the event. This way, photon bunches or sorted by telescope.
 *  This bunch list is dynamically created and extended as required.
 *
 *  @param  det  pointer to data structure of the detector hit.
 *  @param  x    X position in CORSIKA detection plane [cm]
 *  @param  y    Y position in CORSIKA detection plane [cm]
 *  @param  cx   Direction projection onto X axis
 *  @param  cy   Direction projection onto Y axis
 *  @param  sx   Slope with respect to X axis (atan(sx) = acos(cx))
 *  @param  sy   Slope with respect to Y axis (atan(sy) = acos(cy))
 *  @param  photons Bunch size
 *  @param  ctime Arrival time of bunch in CORSIKA detection plane.
 *  @param  zem  Altitude of emission above sea level [cm]
 *  @param  lambda Wavelength (0: undetermined, -1: converted to photo-electron)
 *
 *  @return 0 (O.K.), -1 (failed to save photon bunch)
 *
 *  Note: With the EXTENDED_TELOUT every second call would have
 *  data of the emitting particle: the mass in cx, the charge in cy,
 *  the energy in photons, the time of emission in zem, and 9999 in lambda.
*/

/* #define DEBUG_PHOTONS_SUM 1 */

static int photon_hit (struct detstruct *det, double x, double y,
   double cx, double cy, double sx, double sy, double photons,
   double ctime, double zem, double lambda)
{
   struct bunch *bunch, *btmp;
   size_t wanted;

#ifdef EXTENDED_TELOUT 
   if ( lambda < 9000 )
#endif
   det->photons += photons;

#ifndef STORE_EMITTER
   /* When we exceed the maximum number of bunches that the telescope simulation */
   /* would be able to handle, we discard every second bunch and increase the */
   /* size of the other by a factor of 2. Take care that respective MAX_BUNCHES */
   /* definitions match in both programs (or the one here is the smaller one). */
   if ( det->next_bunch + det->external_bunches >= max_bunches )
   {
      struct bunch *bunch = det->bunch;
#ifdef DEBUG_PHOTONS_SUM
      double sum1 = 0., sum2 = 0.;
      int ni1 = 0, ne1 = 0, ni2 = 0, ne2 = 0, is;
#endif
      if ( det->shrink_factor <= 0 )
         det->shrink_factor = 1;
      det->shrink_factor *= 2;
      det->shrink_cycle = det->shrink_factor/2;
      printf("\nUsing only one out of %d photon bunches for detector %d of array %d.\n",
         det->shrink_factor, det->idet, det->iarray);
#ifdef DEBUG_PHOTONS_SUM
      ni1 = det->next_bunch; ne1 = det->external_bunches;
      for (is=0; is< det->next_bunch; is++) 
         sum1 += det->bunch[is].photons;
#endif

      /* Shrink the number of internal bunches by a(nother) factor of 2. */
      bunch[0].photons *= 2.;
      {
       /* We keep every second bunch (note: not applicable with STORE_EMITTER). */
       int j = 1, i = 2;
       for ( ; i<det->next_bunch; i+=2, j+=1 )
       {
         memcpy(bunch+j,bunch+i,sizeof(struct bunch));
         bunch[j].photons *= 2.;
       }
       det->next_bunch = j;
#ifdef DEBUG_PHOTONS_SUM
      for (is=0; is< det->next_bunch; is++) 
         sum2 += det->bunch[is].photons;
       ni2 = det->next_bunch;
#endif
      }

#ifdef EXTERNAL_STORAGE
      /* Shrink the number of external bunches by a(nother) factor of 2. */
      if ( det->external_bunches > 0 )
      {
         FILE *ext_in, *ext_out;
         char tmp_fname[256];
         struct bunch tbunch;
         int new_external_bunches = 0;
         sprintf(tmp_fname,"tmp_xx_%d_%d_%d.cbunch",
            (int)getpid(),det->iarray,det->idet);
         if ( (ext_in = fileopen(det->ext_fname,"r")) != NULL )
            if ( (ext_out = fileopen(tmp_fname,"w")) != NULL )
            {
               int ic = 0;
               while ( fread((void *)&tbunch,sizeof(struct bunch),1,ext_in) == 1 )
               {
                  ic++;
#ifdef DEBUG_PHOTONS_SUM
                  if ( tbunch.lambda < 9000. )
                     sum1 += tbunch.photons;
#endif
                  if ( ic%2 == 0 )
                  {
                     tbunch.photons *= 2.;
#ifdef DEBUG_PHOTONS_SUM
                        sum2 += tbunch.photons;
#endif
                     if ( fwrite((void *)&tbunch,sizeof(struct bunch),1,ext_out) == 1 )
                        new_external_bunches += 1;
                  }
               }
               fileclose(ext_out);
               fileclose(ext_in);
               if ( unlink(det->ext_fname) == -1 )
                  perror(det->ext_fname);
               if ( rename(tmp_fname,det->ext_fname) == -1 )
                  perror(tmp_fname);
               det->external_bunches = new_external_bunches;
#ifdef DEBUG_PHOTONS_SUM
               ne2 = det->external_bunches;
#endif
            }
      }
#endif /* EXTERNAL_STORAGE */

#ifdef DEBUG_PHOTONS_SUM
      printf("Before shrinking: %f photons (instead of %f) in %d + %d bunches.\n",
         sum1, det->photons, ni1, ne1);
      printf("After shrinking:  %f photons (instead of %f) in %d + %d bunches.\n",
         sum2, det->photons, ni2, ne2);
#endif

   }
   
   /* If we started shrinking the number of photon bunches, use only every n-th */
   /* bunch and increase its amount of light by a factor of n. */
   if ( det->shrink_factor > 1 )
   {
      if ( ++(det->shrink_cycle) >= det->shrink_factor )
      {
         photons *= det->shrink_factor;
         det->shrink_cycle = 0;
      }
      else
         return 0;
   }
#endif /* ifndef STORE_EMITTER */

#ifdef EXTERNAL_STORAGE
   /* fprintf(stderr,"%d photon bunches so far\n",det->next_bunch);*/
   if ( det->next_bunch >= INTERNAL_LIMIT )
   {
      FILE *ext;
      sprintf(det->ext_fname,"tmp_%d_%d_%d.cbunch",
         (int)getpid(),det->iarray,det->idet);
      if ( det->external_bunches == 0 )
         unlink(det->ext_fname);
      /* fprintf(stderr,"Open file %s\n",det->ext_fname); */
      if ( (ext = fileopen(det->ext_fname,"a")) != NULL )
      {
#if defined(__USE_LARGEFILE64)
         int rc = fseeko64(ext,(off64_t)sizeof(struct bunch)*
            det->external_bunches,SEEK_SET);
#elif defined(__USE_FILE_OFFSET64) || defined(__USE_LARGEFILE)
         int rc = fseeko(ext,(off_t)sizeof(struct bunch)*
            det->external_bunches,SEEK_SET);
#else
         int rc = fseek(ext,(long)sizeof(struct bunch)*
            det->external_bunches,SEEK_SET);
#endif
         if ( rc == -1 )
         {
            perror(det->ext_fname);
            return -1;
         }
         if ( fwrite((void *)det->bunch,sizeof(struct bunch),
                 (size_t)det->next_bunch,ext) == (size_t)det->next_bunch )
         {
            det->external_bunches += det->next_bunch;
            free(det->bunch);
            det->bunch = NULL;
            det->available_bunch = det->next_bunch = 0;
         }
         else /* if ( det->next_bunch >= 10*INTERNAL_LIMIT ) */
         {
            char cwd[1024];
            int err = errno;
            perror(det->ext_fname);
            if ( err == ENOSPC || err == EDQUOT )
               fprintf(stderr,"Too bad that you filled up your disk space or quota while storing\n"
                   "temporary photon bunches. Even though it is possible that this is just a\n"
                   "particularly large event and your final output goes to a different device,\n"
                   "you should better make sure that you have sufficient working space available\n"
                   "in directory '%s'.\n", getcwd(cwd,sizeof(cwd)));
            else
               fprintf(stderr,"That is an unexpected error while writing temporary photon bunches.\n"
                   "Check that you have sufficient space and privileges to create and write files\n"
                   "in directory '%s'.\n", getcwd(cwd,sizeof(cwd)));
            return -1;
         }
         fclose(ext);
      }
      else /* if ( det->next_bunch >= 10*INTERNAL_LIMIT ) */
      {
         char cwd[1024];
         int err = errno;
         perror(det->ext_fname);
         fflush(stdin);
         if ( err == ENOSPC || err == EDQUOT )
            fprintf(stderr,"Too bad that you filled up your disk space or quota while storing\n"
                "temporary photon bunches. Even though it is possible that this is just a\n"
                "particularly large event and your final output goes to a different device,\n"
                "you should better make sure that you have sufficient working space available\n"
                "in directory '%s'.\n", getcwd(cwd,sizeof(cwd)));
         else
            fprintf(stderr,"That is an unexpected error while writing temporary photon bunches.\n"
                "Check that you have sufficient space and privileges to create and write files\n"
                "in directory '%s'.\n", getcwd(cwd,sizeof(cwd)));
         fflush(NULL);
         return -1;
      }
   }
#endif

   if ( det->bunch == NULL )
   { 
      if ( (det->bunch = (struct bunch *) 
            calloc(NBUNCH+EXTRA_MEM_4,sizeof(struct bunch))) == NULL )
      {
         fprintf(stderr,
    "Telescope %d of array %d: initial photon bunch list allocation failed.\n",
              det->idet, det->iarray);
         return -1;
      }
      det->available_bunch = NBUNCH;
   }

   if ( det->next_bunch >= det->available_bunch )
   {
      if ( NBUNCH < det->available_bunch/4 )
         wanted = det->available_bunch + NBUNCH + det->available_bunch/4;
      else
         wanted = det->available_bunch + NBUNCH;
      if ( (btmp = (struct bunch *) realloc(det->bunch,
             (wanted+EXTRA_MEM_4)*sizeof(struct bunch))) == NULL )
      {
         fprintf(stderr,
         "Telescope %d of array %d: photon bunch list reallocation failed.\n",
              det->idet, det->iarray);
         return -1;
      }
      det->bunch = btmp;
      det->available_bunch = wanted;
   }
   
   bunch = &det->bunch[det->next_bunch];
   bunch->photons = photons;
   bunch->x       = x - sx*det->z0 - det->x0;
   bunch->y       = y - sy*det->z0 - det->y0;
   bunch->cx      = cx;
   bunch->cy      = cy;
   bunch->ctime   = ctime - 
          det->z0*sqrt(1.+sx*sx+sy*sy)/airlightspeed - toffset;
   bunch->zem     = zem;
   bunch->lambda  = lambda;
   det->next_bunch++;
   
   return 0;
}

#if !defined(IACTEXT) && !defined(EXTENDED_TELOUT)
/* --------------------- compact_photon_hit ---------------------- */
/**
 *  @short Store a photon bunch for a given telescope in compact format.
 *
 *  Store a photon bunch in the bunch list for a given telescope.
 *  This bunch list is dynamically created and extended as required.
 *  This routine is using a more compact format than photon_hit().
 *  This compact format is not appropriate when core distances
 *  of telescopes times sine of zenith angle exceed 1000 m.
 *
 *  @param  det  pointer to data structure of the detector hit.
 *  @param  x    X position in CORSIKA detection plane [cm]
 *  @param  y    Y position in CORSIKA detection plane [cm]
 *  @param  cx   Direction projection onto X axis
 *  @param  cy   Direction projection onto Y axis
 *  @param  sx   Slope with respect to X axis (atan(sx) = acos(cx))
 *  @param  sy   Slope with respect to Y axis (atan(sy) = acos(cy))
 *  @param  photons Bunch size (sizes above 327 cannot be represented)
 *  @param  ctime Arrival time of bunch in CORSIKA detection plane.
 *  @param  zem  Altitude of emission above sea level [cm]
 *  @param  lambda Wavelength (0: undetermined, -1: converted to photo-electron)
 *
 *  @return 0 (O.K.), -1 (failed to save photon bunch)
 *
*/

static int compact_photon_hit (struct detstruct *det, double x, double y,
   double cx, double cy, double sx, double sy, double photons,
   double ctime, double zem, double lambda)
{
   struct compact_bunch *cbunch, *cbtmp;
   size_t wanted;
   
   /* Note: the optional shrinking of the number of photon bunches, when */
   /* a maximum number of bunches is exceeded, is not available for compact */
   /* bunches since we would soon exceed the allowed photons per bunch. */
   
#ifdef EXTERNAL_STORAGE
   /* fprintf(stderr,"%d photon bunches so far\n",det->next_bunch);*/
   if ( det->next_bunch >= INTERNAL_LIMIT )
   {
      FILE *ext;
      sprintf(det->ext_fname,"tmp_%d_%d_%d.cbunch",
         (int)getpid(),det->iarray,det->idet);
      if ( det->external_bunches == 0 )
         unlink(det->ext_fname);
      /* fprintf(stderr,"Open file %s\n",det->ext_fname); */
#ifdef __USE_LARGEFILE64
      if ( (ext = fopen64(det->ext_fname,"a")) != NULL )
#else
      if ( (ext = fopen(det->ext_fname,"a")) != NULL )
#endif
      {
#if defined(__USE_LARGEFILE64)
         fseeko64(ext,(off64_t)sizeof(struct compact_bunch)*
            det->external_bunches,SEEK_SET);
#elif defined(__USE_FILE_OFFSET64) || defined(__USE_LARGEFILE)
         fseeko(ext,(off_t)sizeof(struct compact_bunch)*
            det->external_bunches,SEEK_SET);
#else
         fseek(ext,(long)sizeof(struct compact_bunch)*
            det->external_bunches,SEEK_SET);
#endif
         if ( fwrite((void *)det->cbunch,sizeof(struct compact_bunch),
                 (size_t)det->next_bunch,ext) == (size_t)det->next_bunch )
         {
            det->external_bunches += det->next_bunch;
            free(det->cbunch);
            det->cbunch = NULL;
            det->available_bunch = det->next_bunch = 0;
         }
         else /* if ( det->next_bunch >= 10*INTERNAL_LIMIT ) */
         {
            char cwd[1024];
            int err = errno;
            perror(det->ext_fname);
            if ( err == ENOSPC || err == EDQUOT )
               fprintf(stderr,"Too bad that you filled up your disk space or quota while storing\n"
                   "temporary photon bunches. Even though it is possible that this is just a\n"
                   "particularly large event and your final output goes to a different device,\n"
                   "you should better make sure that you have sufficient working space available\n"
                   "in directory '%s'.\n", getcwd(cwd,sizeof(cwd)));
            else
               fprintf(stderr,"That is an unexpected error while writing temporary photon bunches.\n"
                   "Check that you have sufficient space and privileges to create and write files\n"
                   "in directory '%s'.\n", getcwd(cwd,sizeof(cwd)));
            return -1;
         }
         fclose(ext);
      }
      else /* if ( det->next_bunch >= 10*INTERNAL_LIMIT ) */
      {
         char cwd[1024];
         int err = errno;
         perror(det->ext_fname);
         if ( err == ENOSPC || err == EDQUOT )
            fprintf(stderr,"Too bad that you filled up your disk space or quota while storing\n"
                "temporary photon bunches. Even though it is possible that this is just a\n"
                "particularly large event and your final output goes to a different device,\n"
                "you should better make sure that you have sufficient working space available\n"
                "in directory '%s'.\n", getcwd(cwd,sizeof(cwd)));
         else
            fprintf(stderr,"That is an unexpected error while writing temporary photon bunches.\n"
                "Check that you have sufficient space and privileges to create and write files\n"
                "in directory '%s'.\n", getcwd(cwd,sizeof(cwd)));
         return -1;
      }
   }
#endif

   det->photons += photons;

   if ( det->cbunch == NULL )
   { 
      if ( (det->cbunch = (struct compact_bunch *) 
            calloc(NBUNCH+EXTRA_MEM_4,sizeof(struct compact_bunch))) == NULL )
      {
         fprintf(stderr,
    "Telescope %d of array %d: initial photon bunch list allocation failed.\n",
              det->idet, det->iarray);
         return -1;
      }
      det->available_bunch = NBUNCH;
   }
   
   if ( det->next_bunch >= det->available_bunch )
   {
      if ( NBUNCH < det->available_bunch/4 )
         wanted = det->available_bunch + NBUNCH + det->available_bunch/4;
      else
         wanted = det->available_bunch + NBUNCH;
      if ( (cbtmp = (struct compact_bunch *) realloc(det->cbunch,
             (wanted+EXTRA_MEM_4)*sizeof(struct compact_bunch))) == NULL )
      {
         fprintf(stderr,
         "Telescope %d of array %d: photon bunch list reallocation failed.\n",
              det->idet, det->iarray);
         return -1;
      }
      det->cbunch = cbtmp;
      det->available_bunch = wanted;
   }
   
   cbunch = &det->cbunch[det->next_bunch];
   /*@ The bunch size has a limited range of up to 327 photons. */
   cbunch->photons = (short)(100.*photons+0.5);
   /*@ Positions have a limited range of up to 32.7 m from the detector centre */
   cbunch->x       = (short)Nint(10.*(x - sx*det->z0 - det->x0));
   cbunch->y       = (short)Nint(10.*(y - sy*det->z0 - det->y0));
   /*@ No limits in the direction (accuracy 7 arcsec for vertical showers) */
   cbunch->cx      = (short)Nint(30000.*cx);
   cbunch->cy      = (short)Nint(30000.*cy);
   /*@ The time has a limited range of +-3.27 microseconds. */
   cbunch->ctime   = (short)Nint(10.*(ctime - 
           det->z0*sqrt(1.+sx*sx+sy*sy)/airlightspeed - toffset));
   cbunch->log_zem = (short)(1000.*log10(zem)+0.5);
   if ( lambda == 0. )     /* Unspecified wavelength of photons */
      cbunch->lambda = (short)0;
   else if ( lambda < 0. ) /* Photo-electrons instead of photons */
      cbunch->lambda = (short)(lambda-0.5);
   else                    /* Photons of specific wavelength */
      cbunch->lambda = (short)(lambda+0.5);
   det->next_bunch++;
   
   return 0;
}
#endif

/* -------------------------- Nint_f ------------------------- */
/**
 *
 *  Nearest integer function
 *
*/

static int Nint_f(double x)
{
   if ( x >= 0. )
      return (int)(x+0.5);
   else
      return (int)(x-0.5);
}


/* --------------------------- telout_ --------------------------- */
/**
 *  @short Check if a photon bunch hits one or more simulated detector volumes.

 *  A bunch of photons from CORSIKA is checked if they hit a
 *  a telescope and in this case it is stored (in memory).
 *  This routine can alternatively trigger that the photon bunch
 *  is written by CORSIKA in its usual photons file.
 *
 *  Note that this function should only be called for downward photons
 *  as there is no parameter that could indicate upwards photons.
 *
 *  The interface to this function can be modified by defining
 *  EXTENDED_TELOUT. Doing so requires to have a CORSIKA version
 *  with support for the IACTEXT option, and to actually activate
 *  that option. That could be useful when adding your own
 *  code to create some nice graphs or statistics that requires
 *  to know the emitting particle and its energy but would be of
 *  little help for normal use. Inconsistent usage of 
 *  EXTENDED_TELOUT here and IACTEXT in CORSIKA will most likely
 *  lead to a crash.

 *  @param  bsize   Number of photons (can be fraction of one)
 *  @param  wt	   Weight (if thinning option is active)
 *  @param  px	   x position in detection level plane
 *  @param  py	   y position in detection level plane
 *  @param  pu	   x direction cosine
 *  @param  pv	   y direction cosine
 *  @param  ctime   arrival time in plane after first interaction
 *  @param  zem     height of emission above sea level
 *  @param  lambda  0. (if wavelength undetermined) or wavelength [nm].
 *                  If lambda < 0, photons are already converted to
 *                  photo-electrons (p.e.), i.e. we have p.e. bunches.
 *  @param  temis   Time of photon emission (only if CORSIKA extracted
 *                  with IACTEXT option and this code compiled with
 *                  EXTENDED_TELOUT defined).
 *  @param  penergy Energy of emitting particle (under conditions as temis).
 *  @param  amass   Mass of emitting particle (under conditions as temis).
 *  @param  charge  Charge of emitting particle (under conditions as temis).
 *
 *  @return  0 (no output to old-style CORSIKA file needed)
 *           2 (detector hit but no eventio interface available or
 *             output should go to CORSIKA file anyway)
 *
*/

int telout_ (cors_real_now_t *bsize, cors_real_now_t *wt, 
   cors_real_now_t *px, cors_real_now_t *py, 
   cors_real_now_t *pu, cors_real_now_t *pv, 
   cors_real_now_t *ctime, cors_real_now_t *zem , cors_real_now_t *lambda
#ifdef EXTENDED_TELOUT   
   , double *temis, double *penergy, double *amass, double *charge
#endif
   )
{
   int ix, iy, igrid, rc, kdet, idet, iarray;
   double x = *px - impact_offset[0], y = *py - impact_offset[1];
   double u = *pu, v = *pv, sx, sy;
   double xphotons = *bsize;
   double wl = *lambda;
#ifdef CORSIKA_SAVES_PHOTONS
   int is_corsika;
#endif

   if ( *wt != 1. )
   {
      /* When thinning is used in CORSIKA, we simply multiply the */
      /* bunch size with the thinning weight. Note that in this case */
      /* the limitations of the compact bunch format are easily exceeded. */
      xphotons *= (*wt);
   }


   all_photons += xphotons;
   all_bunches += 1.0;   

   /* Completely outside of grid area? */
   if ( x < grid_x_low || y < grid_y_low )
      return 0;
   ix = (int)((x-grid_x_low)/GRID_SIZE);
   iy = (int)((y-grid_y_low)/GRID_SIZE);
   /* Completely outside of grid area? */
   if ( ix < 0 || ix >= grid_nx || iy < 0 || iy >= grid_ny )
      return 0;

   igrid = iy*grid_nx + ix;
   if ( iy*grid_nx+ix < 0 || iy*grid_nx+ix >= grid_elements )
   {
      fprintf(stderr,
     "Grid bounds exceeded***: ix=%d, iy=%d, i=%d (nx=%d, ny=%d, n=%d)\n",
         ix, iy, iy*grid_nx+ix, grid_nx, grid_ny, grid_elements);
      return -1;
   }
   /* No telescopes/detectors on this grid element? */
   if ( grid[igrid].ndet <= 0 )
      return 0;

#ifdef CORSIKA_SAVES_PHOTONS
   is_corsika = 0;
#endif

   sx = u/sqrt(1.-u*u-v*v);
   sy = v/sqrt(1.-u*u-v*v);

#if defined(EXTENDED_TELOUT) && defined(MARK_DIRECT_LIGHT)
   /* Instead of normally having a unspecified wavelength 0. */
   /* we can mark direct Cherenkov light from the primary */
   /* particle by a wavelength of 1. */
   /* Such light is effectively ignored in sim_telarray unless */
   /* the 'ALL_WL_RANDOM' configuration variable is non-zero. */
   if ( (*charge) > 1.5 )
   {
      if ( primary > 100 )
      {
	 int icharge = (int)(*charge+0.5);
         if ( icharge == (primary%100) )
            wl = 1.;
         else if ( icharge >= (primary%100)/2 && icharge > 2 &&
	           *penergy > 0.4*energy )
            wl = 2.;
         else if ( icharge >= (primary%100)/4 && icharge > 2 &&
	           *penergy > 0.2*energy )
            wl = 3.;
      }
      else if ( *penergy > 0.9*energy )
         wl = 1.;
   }
   else if ( *penergy > 0.9*energy )
      wl = 1.;
#endif

   /* Check all telescopes/detectors having something in this */
   /* grid element if the photons hit this telescope/detector. */
   for (kdet=0; kdet<grid[igrid].ndet; kdet++)
      /* First a quick check if the photons hit the projection of the */
      /* somewhat enlarged detector circumference on the detection level. */
      if ( fabs(x-grid[igrid].detectors[kdet]->x) <= 
              grid[igrid].detectors[kdet]->r )
       if ( fabs(y-grid[igrid].detectors[kdet]->y) <= 
               grid[igrid].detectors[kdet]->r )
        /* Then do a more careful check */
        if ( (rc = in_detector(grid[igrid].detectors[kdet],x,y,sx,sy)) != 0 )
        {
           /* Yes the photons really hit this detector */
#if defined(EXTENDED_TELOUT) && defined(STORE_EMITTER) && !defined(MARK_DIRECT_LIGHT)
           /* We keep both the photon bunch for later storage and the */
           /* information about the particle emitting the photons. */
           if ( photon_hit(grid[igrid].detectors[kdet],
                     x, y, u, v, sx, sy, xphotons,
                    (double)*ctime, (double)*zem, wl) != 0 
                || photon_hit(grid[igrid].detectors[kdet],
                     x, y, *amass, *charge, sx, sy, *penergy,
                     (double)*ctime, *temis, 9999) != 0 )
#else
           /* We keep the photon bunch in one of two possible storage formats */
# ifdef EXTENDED_TELOUT
           if ( photon_hit(grid[igrid].detectors[kdet],
                     x, y, u, v, sx, sy, xphotons,
                    (double)*ctime, (double)*zem, wl) != 0 )
# else
           if ( (use_compact_format ?
                  compact_photon_hit(grid[igrid].detectors[kdet],
                     x, y, u, v, sx, sy, xphotons,
                    (double)*ctime, (double)*zem, wl) :
                  photon_hit(grid[igrid].detectors[kdet],
                     x, y, u, v, sx, sy, xphotons,
                    (double)*ctime, (double)*zem, wl)) != 0 )
# endif
#endif
           {
              fflush(NULL);
              fprintf(stderr,"\n******************************************\n");
              fprintf(stderr,"Fatal problem with storing photon bunches.\n");
              fprintf(stderr,"Already stored: %ld bunches.\n",stored_bunches);
              fprintf(stderr,"Run this simulation with a smaller energy\n");
              fprintf(stderr,"or with a smaller number of telescopes or\n");
              fprintf(stderr,"run it on a computer with more memory.\n");
              fprintf(stderr,"Make also sure you have enough disk space.\n");
              fprintf(stderr,"******************************************\n\n");
              for (iarray=0; iarray<narray; iarray++)
                 for (idet=0; idet<ndet[iarray]; idet++)
                    if ( detector[iarray][idet].ext_fname[0] != '\0' )
                       unlink(detector[iarray][idet].ext_fname);
              exit(1);
           }
           stored_bunches++;
#ifdef CORSIKA_SAVES_PHOTONS
           is_corsika = 2;
#endif
        }           

#ifndef CORSIKA_SAVES_PHOTONS
   return 0;
#else
   return is_corsika;
#endif
}

#ifdef IACTEXT
/* --------------------------- telprt_ ------------------------- */
/**
 *  @short Store CORSIKA particle information into IACT output file.
 *
 *  This function is not needed for normal simulations and is
 *  therefore only available if the preprocessor symbols
 *  IACTEXT or EXTENDED_TELOUT are defined. At the same time
 *  CORSIKA itself should be extracted with the IACTEXT option.
 *
 *  @param datab  A particle data buffer with up to 39 particles.
 *  @param maxbuf The buffer size, which is 39*7 without thinning
 *                option and 39*8 with thinning.
 */

void telprt_ (cors_real_t *datab, int *maxbuf)
{
   int i;
   int vpp = (*maxbuf)/39; /* Values per particle (7 without thinning, 8 with) */
   int thinning = (vpp==8?1:0);

   if ( particles == NULL )
   {
      if ( (particles = (struct bunch *) 
            calloc(NBUNCH+EXTRA_MEM_4,sizeof(struct bunch))) == NULL )
      {
         fprintf(stderr, "Initial particles list allocation failed.\n");
         return;
      }
      particles_space = NBUNCH;
      particles_stored = 0;
   }

   if ( particles_stored+39 > particles_space )
   {
      size_t wanted = particles_space + NBUNCH;
      struct bunch *tmpp = (struct bunch *) realloc(particles, 
            (wanted+EXTRA_MEM_4)*sizeof(struct bunch));
      if ( tmpp == NULL )
      {
         fprintf(stderr,"Particle list reallocation failed.\n");
         return;
      }
      particles = tmpp;
      particles_space = wanted;
   }

   for (i=0; i<39; i++ )
   {
      if ( datab[i*vpp] == 0. ) /* Buffer not filled completely */
         break;

      double p = sqrt(datab[i*vpp+1]*datab[i*vpp+1] +
          datab[i*vpp+2]*datab[i*vpp+2] +
          datab[i*vpp+3]*datab[i*vpp+3]);
      struct bunch *bunch = &particles[particles_stored];
      bunch->zem    = datab[i*vpp+3]>0. ? p : -p; /* momentum goes into zem; check sign */
      bunch->x      = datab[i*vpp+4] - impact_offset[0];
      bunch->y      = datab[i*vpp+5] - impact_offset[1];
      bunch->cx     = datab[i*vpp+1] / p;
      bunch->cy     = datab[i*vpp+2] / p;
      bunch->ctime  = datab[i*vpp+6];
      /* Note: this is 1000 * particle code + 10 * generation no.,
         if applicable, + detection level no. (here always 1). */
      bunch->lambda = datab[i*vpp]; /* Particle information goes into lamda */
      if ( thinning )
         bunch->photons = datab[i*vpp+7]; /* Thinning weight */
      else
         bunch->photons = 1.;
      particles_stored++;

#ifdef DEBUG_IMPACT
      printf(" Particle type %d hits detection level %d at x=%f m, y=%f m\n",
         ((int)(bunch->lambda+0.5))/1000,
         ((int)(bunch->lambda+0.5))%1000,
         bunch->x*1e-2,bunch->y*1e-2 );
      printf("   corrected for offset %f m, %f m\n", 
         impact_offset[0]*1e-2, impact_offset[1]*1e-2);
#endif
   }

   return;
}
#endif

/* --------------------------- tellng_ ------------------------- */
/**
 *  @short Write CORSIKA 'longitudinal' (vertical) distributions.
 *
 *  Write several kinds of vertical distributions to the output.
 *  These or kinds of histograms as a function of atmospheric depth.
 *  In CORSIKA, these are generally referred to as 'longitudinal' distributions.
 *
 *  @verbatim
 *  There are three types of distributions:
 *	type 1: particle distributions for
 *		gammas, positrons, electrons, mu+, mu-,
 *		hadrons, all charged, nuclei, Cherenkov photons.
 *	type 2: energy distributions (with energies in GeV) for
 *		gammas, positrons, electrons, mu+, mu-,
 *		hadrons, all charged, nuclei, sum of all.
 *	type 3: energy deposits (in GeV) for
 *		gammas, e.m. ionisation, cut of e.m.  particles,
 *		muon ionisation, muon cut, hadron ionisation,
 *		hadron cut, neutrinos, sum of all.
 *		('cut' accounting for low-energy particles dropped)
 *  @endverbatim
 *
 *  Note: Corsika can be extracted from CMZ sources with three options
 *  concerning the vertical profile of Cherenkov light:
 *  default = emission profile, INTCLONG = integrated light profile,
 *  NOCLONG = no Cherenkov profiles at all. If you know which kind
 *  you are using, you are best off by defining it for compilation
 *  of this file (either -DINTEGRATED_LONG_DIST, -DEMISSION_LONG_DIST, or
 *  -DNO_LONG_DIST).
 *  By default, a run-time detection is attempted which should work well
 *  with some 99.99% of all air showers but may fail in some cases like 
 *  non-interacting muons as primary particles etc.
 *
 *  @param  type    see above
 *  @param  data    set of (usually 9) distributions
 *  @param  ndim    maximum number of entries per distribution
 *  @param  np      number of distributions (usually 9)
 *  @param  nthick  number of entries actually filled per distribution
 *                  (is 1 if called without LONGI being enabled).
 *  @param  thickstep  step size in g/cm**2
 *
 *  @return  (none)
 *
*/

void tellng_ (int *type, double *data, int *ndim, int *np, 
   int *nthick, double *thickstep)
{
#if defined(INTEGRATED_LONG_DIST)
   static int is_integ = 1;
#elif defined(UNKNOWN_LONG_DIST)
   static int is_integ = 0;
#else
   static int is_integ = -1;
#endif
   static int init_done = 0;
   int i;

#ifdef HAVE_EVENTIO_FUNCTIONS
#ifndef WRITE_ALL_LONG
   /* Ignoring everything except particle distributions */
   if ( *type != 1 )
      return;
#endif

   if ( *nthick <= 1 )
   {
      if ( !init_done )
      	 printf("\n No vertical profiles switched on and none written to output.\n\n");
      init_done = 1;
      return;
   }

#ifdef NO_LONG_DIST
   if ( !init_done )
      printf("\n No vertical profiles are written to output.\n\n");
   init_done = 1;
   return;
#else
#ifdef UNKNOWN_LONG_DIST
   /* When not knowing how CORSIKA writes Cherenkov light longitudinal */
   /* distributions, we have to find it out dynamically. */
   if ( *type == 1 && is_integ == 0 )
   {
      double sum_prof = data[8*(*ndim)+0];
      /* If the photon number ever falls of again it is an emission profile. */
      for (i=1; i<(*nthick); i++)
      {
      	 sum_prof += data[8*(*ndim)+i];
         if ( data[8*(*ndim)+i] - data[8*(*ndim)+i-1] < 0 )
      	 {
	    printf("\n Cherenkov light vertical distribution is an"
	           "\n emission profile and will not be differentiated.\n\n");
	    is_integ = -1;
	    break;
	 }
      }
      if ( is_integ == 0 )
      {
      	 if ( sum_prof == 0. )
	    printf("\n Cherenkov light vertical distribution is empty.\n\n");
	 else
            printf("\n Cherenkov light vertical distribution is presumably"
	        "\n an integrated profile and will be differentiated.\n\n");
      }
      /* Note that in the latter case there is a small chance of being wrong. */
   }
#endif

   /* Cherenkov distribution is cummulative: differentiate it now */
   if ( *type == 1 && is_integ != -1 )
   {
      for (i=(*nthick)-1; i>=1; i--)
      	 data[8*(*ndim)+i] -= data[8*(*ndim)+i-1];
   }

#ifdef DEBUG_LONG_DIST
   if ( *type == 1 )
   {
      for (i=0; i<(*nthick); i++)
      {
	 double heigh_(double *x);
	 double x=(*thickstep)*(i+0.5);
	 printf("# %7.3f %f %g %g\n",heigh_(&x)*1e-5,x/cos(theta_prim),
	    data[6*(*ndim)+i],data[8*(*ndim)+i]);
      }
   }
#endif

   /* Now actually store the longitudinal distributions */
   if ( write_shower_longitudinal(iobuf,event_number,*type,data,*ndim,*np,
            *nthick,*thickstep) != 0 )
      ioerrorcheck();

   /* Restore cumulative Cherenkov distribution */
   if ( *type == 1 && is_integ != -1 )
   {
      for (i=1; i<(*nthick); i++)
      	 data[8*(*ndim)+i] += data[8*(*ndim)+i-1];
   }
#endif /* NO_LONG_DIST */
#endif /* HAVE_EVENTIO_FUNCTIONS */
}

/* --------------------------- telend_ ------------------------- */
/**
 *  @short End of event. Write out all recorded photon bunches.
 *
 *  End of an event: write all stored photon bunches to the
 *  output data file, and the CORSIKA event end block as well.
 *
 *  @param  evte  CORSIKA event end block
 *  @return (none)
 *
*/

void telend_ (cors_real_t evte[273])
{
   int iarray, idet;
#ifdef HAVE_EVENTIO_FUNCTIONS
   IO_ITEM_HEADER item_header;
#endif
   
   do_print = 0;
   if ( (nevents+1)%skip_print == 0 )
   {
      if ( count_print_tel++ < max_print_tel )
      	 do_print = 1;
   }

   all_photons_run += all_photons;
   all_bunches_run += all_bunches;
   nevents++;

   if ( do_print )
   {
      printf("\n Total number of photons in shower: %f in %f bunches\n",
         all_photons,all_bunches);

      for (iarray=0; iarray<narray; iarray++)
      {
	 printf(" Array %2d: ",iarray);
	 for (idet=0; idet<ndet[iarray]; idet++)
	 {
            printf(" %6.0f",detector[iarray][idet].photons);
	 }
	 printf(" photons (array offset: %7.1f %7.1f m)\n",
            xoffset[iarray]*0.01,yoffset[iarray]*0.01);
      }
      fflush(NULL);
   }

#ifdef HAVE_EVENTIO_FUNCTIONS
   {
      struct shower_extra_parameters *ep = get_shower_extra_parameters();
      if ( ep != NULL && ep->is_set )
      {
         write_shower_extra_parameters(iobuf,ep);
         ep->is_set = 0;
      }
   }
#endif

#ifdef IACTEXT
   /* If we have extra particle information, write that first. */
   if ( particles != NULL && particles_stored > 0 )
   {
      if ( write_tel_photons(iobuf, 999, 999, (double) particles_stored,
             particles, particles_stored, 0, NULL) != 0 )
         ioerrorcheck();
      particles_stored = 0;
      if ( particles != NULL )
      {
         free(particles);
         particles = NULL;
         particles_space = 0;
      }
   }
#endif

#ifdef HAVE_EVENTIO_FUNCTIONS
   for (iarray=0; iarray<narray; iarray++)
   {
      int write_individual = 0;  /* By default all write photon bunches of an array in one block. */
      if ( tel_individual == 1 ) /* Should we always write separate blocks for each telescope? */
         write_individual = 1;
      else if ( tel_individual == 2 ) /* Should we split the data on a case-by-case basis? */
      {
         /* First count how many bunches we have and then decide. */
         size_t nbtot = 0;
         for (idet=0; idet<ndet[iarray]; idet++)
            nbtot += detector[iarray][idet].next_bunch + 
                     detector[iarray][idet].external_bunches;
         if ( nbtot > tel_split_threshold )
            write_individual = 1;
      }
      /* We have a choice of two ways to write the telescope data. */
      /* Which one is more efficient depends on the energy range, */
      /* the number of telescopes, and the computer main memory. */
      if ( !write_individual )
      {
         /* By default, a full array is in one block. */
         begin_write_tel_array(iobuf,&item_header,iarray);
      }
      else
      {
         /* As an alternative, we can write separate blocks for */
         /* each telescope, bracketed by header and trailer blocks. */
         /* This will save memory in the pipeline but not all */
         /* readers (telescope simulation, ...) may be able to understand it. */
         if ( write_tel_array_head(iobuf,&item_header,iarray) != 0 )
            ioerrorcheck();
      }
      for (idet=0; idet<ndet[iarray]; idet++)
      {
#ifdef WRITE_ONLY_NONEMPTY_TELESCOPES
         if ( detector[iarray][idet].next_bunch + 
              detector[iarray][idet].external_bunches > 0 )
#endif
         {
            if ( use_compact_format )
            {
               if ( write_tel_compact_photons(iobuf,iarray,idet,
                     detector[iarray][idet].photons,
                     detector[iarray][idet].cbunch,
                     detector[iarray][idet].next_bunch,
                     detector[iarray][idet].external_bunches,
                     detector[iarray][idet].ext_fname) != 0 )
                  ioerrorcheck();
            }
            else
            {
               if ( write_tel_photons(iobuf,iarray,idet,
                     detector[iarray][idet].photons,
                     detector[iarray][idet].bunch,
                     detector[iarray][idet].next_bunch,
                     detector[iarray][idet].external_bunches,
                     detector[iarray][idet].ext_fname) != 0 )
                  ioerrorcheck();
            }
         }
         if ( detector[iarray][idet].ext_fname[0] != '\0' )
            unlink(detector[iarray][idet].ext_fname);
         detector[iarray][idet].external_bunches = 0;
         detector[iarray][idet].ext_fname[0] = '\0';
      }
      /* Depending on whether the photon bunches were written into one */
      /* common block for a full array or into separate blocks for each */
      /* telescope, slightly different actions are required at the end. */
      if ( !write_individual )
      {
         if ( end_write_tel_array(iobuf,&item_header) != 0 )
            ioerrorcheck();
      }
      else
      {
         if ( write_tel_array_end(iobuf,&item_header,iarray) != 0 )
            ioerrorcheck();
      }
   }
   if ( write_tel_block(iobuf,IO_TYPE_MC_EVTE,(int)evte[1],evte,273) != 0 )
      ioerrorcheck();
   fflush(iobuf->output_file);
#endif

}

/* ----------------------------------------------------------- */

#if 0
/* in case of problems with square() implemented as a macro use function */
static double square(double x)
{
   return x*x;
}
#else
#define square(x) ((x)*(x))
#endif

/* ------------------------- in_detector --------------------- */
/**
 *  @short Check if a photon bunch hits a particular telescope volume.
 *
 *  Check if a photon bunch (or, similarly, a particle) hits a
 *  particular simulated telescope/detector.
 *
 *  @param  x  X position of photon position in CORSIKA detection level [cm]
 *  @param  y  Y position of photon position in CORSIKA detection level [cm]
 *  @param  sx Slope of photon direction in X/Z plane.
 *  @param  sy Slope of photon direction in Y/Z plane.
 *
 *  @return 0 (does not hit), 1 (does hit)
*/

static int in_detector (struct detstruct *det, double x, double y, double sx, double sy)
{
   double xd, yd, d2;

   switch ( det->geo_type )
   {
      case 1: /* circular (in detection level plane) */
         if ( sqrt((x-det->x)*(x-det->x)+(y-det->y)*(y-det->y)) > det->dx )
            return 0;
         break;
      case 2: /* rectangular (in detection level plane) */
         if ( fabs(x-det->x) > det->dx || fabs(y-det->y) > det->dy )
            return 0;
         break;
      case 3: /* quasi spherical (fiducial volume in space) */
         xd = x - sx*det->z0;
         yd = y - sy*det->z0;
         
#ifdef DEBUG_IACT
printf("Photon: x=%5.0f, y=%5.0f, sx=%5.3f, sy=%5.3f, xd=%5.0f, yd=%5.0f\n",
      x,y,sx,sy,xd,yd);
printf("Detector: x=%5.0f, y=%5.0f, z=%3.0f\n",
      det->x0,det->y0,det->z0);
fflush(stdout);
#endif

         /* Distance of photon path at (xd,yd,det->z0) with direction */
         /* (sx,sy,1) from centre of sphere at (det->x0,det->y0,det->z0). */
         d2 = (square((xd-det->x0)*sy-(yd-det->y0)*sx) +
               square((yd-det->y0)) +
               square((xd-det->x0))) / (sx*sx+sy*sy+1.);
         /* Reject paths not intersecting sphere. */
         /* Note: photons are accepted even if produced below the sphere. */
         if ( d2 > det->r0*det->r0 )
            return 0;
#ifdef DEBUG_IACT
printf("Telescope hit, d = %5.0f\n",sqrt(d2));
fflush(stdout);
#endif
         break;
   }

   return 1;
}

/* ------------------------ set_random_systems ---------------------- */
/**
 *  @short Randomly scatter each array of detectors in given area.
 *
 *  The area containing the detectors is sub-divided into a rectangular
 *  grid and each detector with a (potential) intersection with a grid
 *  element is marked for that grid element. A detector can be marked
 *  for several grid elements unless completely inside one element.
 *  Checks which detector(s) is/are hit by a photon bunch (or, similarly,
 *  by a particle) is thus reduced to check only the detectors marked
 *  for the grid element which is hit by the photon bunch (or particle).
 *  The grid should be sufficiently fine-grained that there are usually
 *  not much more than one detector per element but finer graining than
 *  the detector sizes makes no sense.
 *
 *  @param theta     Zenith angle of the shower following [radians].
 *  @param phi       Shower azimuth angle in CORSIKA angle convention [radians].
 *  @param thetaref  Reference zenith angle (e.g. of VIEWCONE centre) [radians].
 *  @param phiref    Reference azimuth angle (e.g. of VIEWCONE centre) [radians].
 *  @param offax     Angle between central direction (typically VIEWCONE centre)
 *                   and the direction of the current primary [radians].
 *  @param E         Primary particle energy in GeV (may be used in importance sampling).
 *  @param primary   Primary particle ID (may be used in importance sampling).
 *  @param volflag   Set to 1 if CORSIKA was compiled with VOLUMEDET option, 0 otherwise.
 *
 *  @return 0 (O.K.), -1 (error)
*/

static int set_random_systems (double theta, double phi, 
   double thetaref, double phiref, double offax,
   double E, int primary, int volflag)
{
   int iarray, idet, iclass, ix, iy; 
   int start_class[MAX_CLASS], size_class[MAX_CLASS];
   double r_class[MAX_CLASS], dx_class[MAX_CLASS], dy_class[MAX_CLASS];
   int nod, nn;

   narray = nsys;
   if ( ndet == NULL )
      ndet = (int *) calloc((size_t)narray+EXTRA_MEM_5,sizeof(int));

   size_class[0] = nsys;
   for (start_class[0]=0,iclass=1; iclass<MAX_CLASS; iclass++)
      start_class[iclass] = start_class[iclass-1]+size_class[iclass-1];

   for (iarray=start_class[0]; iarray<start_class[0]+size_class[0]; iarray++)
      ndet[iarray] = ntel;
      
   for (iclass=0; iclass<MAX_CLASS; iclass++)
     det_in_class[iclass] = ndet[start_class[iclass]];

   for (iarray=nod=0; iarray<narray; iarray++)
      nod += ndet[iarray];
   if ( do_print )
      fprintf(stdout," %d telescope%s simulated in %d array%s.\n",
         nod, nod==1?" is":"s are", narray, narray==1?"":"s");

   if ( detector == NULL )
      detector = (struct detstruct **) calloc((size_t)narray+EXTRA_MEM_6,
          sizeof(struct detstruct *));
   if ( xoffset == NULL )
      xoffset = (double *) calloc((size_t)narray+EXTRA_MEM_7,sizeof(double));
   if ( yoffset == NULL )
      yoffset = (double *) calloc((size_t)narray+EXTRA_MEM_7,sizeof(double));
   if ( weight == NULL )
      weight = (double *) calloc((size_t)narray+EXTRA_MEM_7,sizeof(double));

   for (iarray=0; iarray<narray; iarray++)
   {
      if ( detector[iarray] == NULL )
       if ( (detector[iarray] = (struct detstruct *)
           calloc((size_t)ndet[iarray]+EXTRA_MEM_8,sizeof(struct detstruct))) == NULL )
      {
         fprintf(stderr,"Detector allocation failed\n");
         return -1;
      }
   }

   iclass = 0;
   for (iarray=start_class[iclass]; 
        iarray<start_class[iclass]+size_class[iclass]; iarray++)
   {
      for ( idet = 0; idet < ndet[iarray]; idet++ )
      {
         /* Projected position (along shower direction) on detection level: */
         detector[iarray][idet].x = xtel[idet] + ztel[idet]*tan(theta)*cos(phi);
         detector[iarray][idet].y = ytel[idet] + ztel[idet]*tan(theta)*sin(phi);
         /* Simple fiducial area is larger than simple projection: */
         detector[iarray][idet].r  = 
         detector[iarray][idet].dx = 
         detector[iarray][idet].dy = 
              rtel[idet]/cos(theta) * 1.1 + fabs(ztel[idet]*tan(theta)*0.1);
         /* Position in space: */
         detector[iarray][idet].x0 = xtel[idet];
         detector[iarray][idet].y0 = ytel[idet];
         detector[iarray][idet].z0 = ztel[idet];
         detector[iarray][idet].r0 = rtel[idet];
         detector[iarray][idet].geo_type = 3;
         detector[iarray][idet].sens_type = 1;
         detector[iarray][idet].dclass = iclass;
         if ( detector[iarray][idet].bunch != NULL )
            free(detector[iarray][idet].bunch);
         detector[iarray][idet].bunch = NULL;
         if ( detector[iarray][idet].cbunch != NULL )
            free(detector[iarray][idet].cbunch);
         detector[iarray][idet].cbunch = NULL;
         detector[iarray][idet].available_bunch = 0;
         detector[iarray][idet].next_bunch = 0;
         detector[iarray][idet].photons = 0.;
         detector[iarray][idet].ext_fname[0] = '\0';
         detector[iarray][idet].external_bunches = '\0';
      }
   }

   /* Determine size of arrays. */

   for ( iclass=0; iclass<MAX_CLASS; iclass++ )
   {
      r_class[iclass] = dx_class[iclass] = dy_class[iclass] = 0.;
      iarray = start_class[iclass];
      for ( idet=0; idet<ndet[iarray]; idet++ )
      {
         double r, dx, dy;

         r = sqrt(detector[iarray][idet].x*detector[iarray][idet].x +
                  detector[iarray][idet].y*detector[iarray][idet].y) +
             detector[iarray][idet].r;
         dx = fabs(detector[iarray][idet].x)+detector[iarray][idet].dx;
         dy = fabs(detector[iarray][idet].y)+detector[iarray][idet].dy;
         if ( r > r_class[iclass] )
            r_class[iclass] = r;
         if ( dx > dx_class[iclass] )
            dx_class[iclass] = dx;
         if ( dy > dy_class[iclass] )
            dy_class[iclass] = dy;
      }
   }

   /* Shift detectors by random amount (but must be inside trigger area) */

   for ( iarray = 0; iarray < narray; iarray++ )
   {
      int inside;
      double xoff, yoff;

      iclass = detector[iarray][0].dclass;
      
      if ( sampling_fname == NULL )
      {
         /* Uniform sampling */
         for ( inside=0; !inside; )
         {
            if ( core_range2 <= 0. )
            {
               xoff = core_range*(2.*(rndm(0)-0.5));
               yoff = core_range*(2.*(rndm(1)-0.5));
               if ( sqrt(xoff*xoff+yoff*yoff) <= core_range )
                  inside = 1;
            }
            else
            {
               xoff = core_range1*(2.*(rndm(0)-0.5));
               yoff = core_range2*(2.*(rndm(1)-0.5));
               inside = 1;
            }

#ifdef DEBUG_IACT
printf("Array %d (class%d) has offset dx=%f, dy=%f\n",iarray,iclass,xoff,yoff);
fflush(stdout);
#endif
         }

         if ( core_range2 <= 0. )
            detector[iarray][0].sampling_area = M_PI*(core_range*core_range) / (double)narray;
         else
            detector[iarray][0].sampling_area = 4.*(core_range1*core_range2) / (double)narray;
      }
      else if ( core_range2 != 0. )
      {
         fprintf(stderr,"\n Importance sampling can only be used with circular regions.\n");
         exit(1);
      }
      else if ( !volflag )
      {
         fprintf(stderr,"\n Importance sampling with circular regions requires CORSIKA option VOLUMEDET.\n");
         exit(1);
      }
      else
         sample_offset(sampling_fname, core_range, theta, phi, 
            thetaref, phiref, offax, E, primary,
            &xoff, &yoff, &detector[iarray][0].sampling_area);

      /* If CORSIKA is compiled with the VOLUMEDET option, we follow that */
      /* here and take our random offset to be in a plane perpendicular to */
      /* the shower axis and not a horizontal plane. */

      if ( volflag )
      {
         double x1, y1, x2, y2;
         x1 = xoff/cos(theta);
         y1 = yoff;
         x2 = x1*cos(phi) - y1*sin(phi);
         y2 = x1*sin(phi) + y1*cos(phi);
         xoff = x2;
         yoff = y2;
      }

      xoffset[iarray] = xoff;
      yoffset[iarray] = yoff;
      weight[iarray] = detector[iarray][0].sampling_area;
      for ( idet = 0; idet < ndet[iarray]; idet++ )
      {
         detector[iarray][idet].x += xoff;
         detector[iarray][idet].y += yoff;
         detector[iarray][idet].x0 += xoff;
         detector[iarray][idet].y0 += yoff;
      }
#ifdef DEBUG_IACT
printf("Array %d (class%d) has offset dx=%f, dy=%f\n",iarray,iclass,xoff,yoff);
fflush(stdout);
#endif
   }

   /* Free grid from previous showers */
   
   if ( grid != NULL )
   {
      for (iy=0; iy<grid_ny; iy++)
         for (ix=0; ix<grid_nx; ix++)
         {
            struct gridstruct *gc;
            if ( iy*grid_nx+ix < 0 || iy*grid_nx+ix >= grid_elements )
            {
               fprintf(stderr,
              "Grid bounds exceeded: ix=%d, iy=%d, i=%d (nx=%d, ny=%d, n=%d)\n",
                  ix, iy, iy*grid_nx+ix, grid_nx, grid_ny, grid_elements);
               return -1;
            }
            gc = &grid[iy*grid_nx+ix];
            if ( gc->detectors != NULL )
            {
               free(gc->detectors);
               gc->detectors = NULL;
            }
            gc->idet = gc->ndet = 0;
         }
      free(grid);
      grid = NULL;
   }

   /* Determine grid size for next shower */

   for (iarray=0; iarray < narray; iarray++)
      for (idet=0; idet<ndet[iarray]; idet++)
      {
         if ( detector[iarray][idet].x - detector[iarray][idet].r < grid_x_low )
            grid_x_low = detector[iarray][idet].x - detector[iarray][idet].r;
         if ( detector[iarray][idet].x + detector[iarray][idet].r > grid_x_high )
            grid_x_high = detector[iarray][idet].x + detector[iarray][idet].r;
         if ( detector[iarray][idet].y - detector[iarray][idet].r < grid_y_low )
            grid_y_low = detector[iarray][idet].y - detector[iarray][idet].r;
         if ( detector[iarray][idet].y + detector[iarray][idet].r > grid_y_high )
            grid_y_high = detector[iarray][idet].y + detector[iarray][idet].r;
      }

   grid_nx = Nint_f(ceil(grid_x_high/GRID_SIZE) - floor(grid_x_low/GRID_SIZE));
   grid_x_low = GRID_SIZE * floor(grid_x_low/GRID_SIZE);
   grid_x_high = grid_x_low + GRID_SIZE * grid_nx;
   grid_ny = Nint_f(ceil(grid_y_high/GRID_SIZE) - floor(grid_y_low/GRID_SIZE));
   grid_y_low = GRID_SIZE * floor(grid_y_low/GRID_SIZE);
   grid_y_high = grid_y_low + GRID_SIZE * grid_ny;
   
   nn = grid_nx+1;
   if ( grid_ny >= nn )
      nn = grid_ny+1;

#ifdef DEBUG_IACT
printf("Grid: %3.0f<x<%3.0f (%d bins),  %3.0f<y<%3.0f (%d bins)\n",
      grid_x_low,grid_x_high,grid_nx,grid_y_low,grid_y_high,grid_ny);
fflush(stdout);
#endif

   /* Allocate grid and references to detectors on grid elements. */

   grid_elements = 0;
   if ( (grid = (struct gridstruct *) calloc((size_t)(nn*nn)+EXTRA_MEM_10,
           sizeof(struct gridstruct))) == NULL )
   {
      fprintf(stderr,"Grid allocation failed\n");
      return -1;
   }
   grid_elements = nn*nn;

   for (iarray=0; iarray < narray; iarray++)
      for (idet=0; idet<ndet[iarray]; idet++)
      {
         double x0, y0, x1, y1;
         x0 = detector[iarray][idet].x - detector[iarray][idet].r;
         x1 = detector[iarray][idet].x + detector[iarray][idet].r;
         y0 = detector[iarray][idet].y - detector[iarray][idet].r;
         y1 = detector[iarray][idet].y + detector[iarray][idet].r;
         for (ix=(int)((x0-grid_x_low)/GRID_SIZE);
              ix<=(int)((x1-grid_x_low)/GRID_SIZE); ix++)
            for (iy=(int)((y0-grid_y_low)/GRID_SIZE);
                 iy<=(int)((y1-grid_y_low)/GRID_SIZE); iy++)
               if ( ix >= 0 && ix < grid_nx && iy >= 0 && iy < grid_ny )
                  grid[iy*grid_nx+ix].ndet++;
         detector[iarray][idet].iarray = iarray;
         detector[iarray][idet].idet = idet;
         detector[iarray][idet].shrink_factor = 1;
         detector[iarray][idet].shrink_cycle = 0;
      }

   for (iy=0; iy<grid_ny; iy++)
      for (ix=0; ix<grid_nx; ix++)
      {
         struct gridstruct *gc;
         if ( iy*grid_nx+ix < 0 || iy*grid_nx+ix >= grid_elements )
         {
            fprintf(stderr,
           "Grid bounds exceeded*: ix=%d, iy=%d, i=%d (nx=%d, ny=%d, n=%d)\n",
               ix, iy, iy*grid_nx+ix, grid_nx, grid_ny, grid_elements);
            return -1;
         }
         gc = &grid[iy*grid_nx+ix];
         if ( gc->ndet <= 0 )
            gc->detectors = NULL;
         else if ( (gc->detectors = (struct detstruct **)
                 calloc((size_t)gc->ndet+EXTRA_MEM_11,
                    sizeof(struct detstruct *))) == NULL )
	 {
	    fprintf(stderr,"Grid element allocation failed\n");
            return -1;
	 }
      }

   for (iarray=0; iarray < narray; iarray++)
      for (idet=0; idet<ndet[iarray]; idet++)
      {
         double x0, y0, x1, y1;
         x0 = detector[iarray][idet].x - detector[iarray][idet].r;
         x1 = detector[iarray][idet].x + detector[iarray][idet].r;
         y0 = detector[iarray][idet].y - detector[iarray][idet].r;
         y1 = detector[iarray][idet].y + detector[iarray][idet].r;
         for (ix=(int)((x0-grid_x_low)/GRID_SIZE);
              ix<=(int)((x1-grid_x_low)/GRID_SIZE); ix++)
            for (iy=(int)((y0-grid_y_low)/GRID_SIZE);
                 iy<=(int)((y1-grid_y_low)/GRID_SIZE); iy++)
               if ( ix >= 0 && ix < grid_nx && iy >= 0 && iy < grid_ny )
               {
                  struct gridstruct *gc;
                  if ( iy*grid_nx+ix < 0 || iy*grid_nx+ix >= grid_elements )
                  {
                     fprintf(stderr,
                    "Grid bounds exceeded**: ix=%d, iy=%d, i=%d (nx=%d, ny=%d, n=%d)\n",
                        ix, iy, iy*grid_nx+ix, grid_nx, grid_ny, grid_elements);
                     return -1;
                  }
                  gc = &grid[iy*grid_nx+ix];
                  if ( gc->detectors == NULL )
                     fprintf(stderr,"Grid cell problem. No detectors expected.\n");
                  else if ( gc->idet < 0 )
                     fprintf(stderr,"Bad detector count in grid cell.\n");
                  else if ( gc->idet < gc->ndet )
                     gc->detectors[gc->idet++] = &detector[iarray][idet];
                  else
                     fprintf(stderr,"No more detectors added to grid cell.\n");
               }
               else
                  fprintf(stderr,"Outside grid limits: ix=%d, iy=%d, nx=%d, ny=%d\n",
                     ix, iy, grid_nx, grid_ny);
      }

   return 0;
}

#ifdef NO_EXTERN_SAMPLING

/* ------------------------- sample_offset ---------------------------- */
/**
 *  @short Get uniformly sampled or importance sampled offset of array
 *         with respect to core, in the plane perpendicular to the shower axis.
 *
 *  @param sampling_fname Name of file with parameters, to be read on first call.
 *  @param core_range     Maximum core distance as used in data format check [cm].
 *                        If not obeying this maximum distance, make sure to switch on
 *                        the long data format manually.
 *  @param theta          Zenith angle [radians]
 *  @param phi            Shower azimuth angle in CORSIKA angle convention [radians].
 *  @param thetaref       Reference zenith angle (e.g. of VIEWCONE centre) [radians].
 *  @param phiref         Reference azimuth angle (e.g. of VIEWCONE centre) [radians].
 *  @param offax          Angle between central direction (typically VIEWCONE centre)
 *                        and the direction of the current primary [radians].
 *  @param E              Energy of primary particle [GeV]
 *  @param primary        Primary particle ID.
 *  @param xoff           X offset [cm] to be generated.
 *  @param yoff           Y offset [cm] to be generated.
 *  @param sampling_area  Area weight of the generated sample 
 *                        (normalized to Pi*core_range^2) [cm^2].
 */

void sample_offset (char *sampling_fname, double core_range, 
   double theta, double phi, 
   double thetaref, double phiref, double offax, 
   double E, int primary,
   double *xoff, double *yoff, double *sampling_area)
{
   static int init_done = 0;
   double R, p;
   
   if ( !init_done )
   {
      FILE *f = fileopen(sampling_fname,"r");
      if ( f == NULL )
      {
         perror(sampling_fname);
         exit(1);
      }
      /* Read sampling parameters */
      /* ... (TO BE DONE) ... */
      fprintf(stderr,"Sampling parameter file '%s' opened but not used.\n",
         sampling_fname);
      fileclose(f);
      init_done = 1;
   }
   
#ifndef TEST_SAMPLING
   /* In the absence of a real implementation, use uniform distribution. */
   R = core_range*sqrt(rndm(0));
   p = (2.*M_PI) * rndm(1);
   *xoff = R * cos(p);
   *yoff = R * sin(p);
   *sampling_area = M_PI*(core_range*core_range);
#else
   /* Test uniform per radius, not uniform per area. */
   R = core_range*rndm(0);
   p = (2.*M_PI) * rndm(1);
   *xoff = R * cos(p);
   *yoff = R * sin(p);
   *sampling_area = 2.*M_PI*(core_range*R);
#endif
}

#endif /* NO_EXTERN_SAMPLING */

/* --------------------- extprim_setup ------------------------- */
/**
 *  @short Placeholder function for activating and setting up
 *         user-defined (external to CORSIKA) controlled over
 *         types, spectra, and angular distribution of primaries.
 *
 *  @param text CORSIKA input card text following the 'IACT EXTPRIM'
 *         keywords. Could be parameter values or a file name.
 */

void extprim_setup (char *text)
{
   extern int with_extprim;

   with_extprim = 1;

   fprintf(stderr,"Dummy set-up function for external control over primaries called\n");
   fprintf(stderr,"with the following argument(s): %s\n", text);
}


#define iact_clean_errno() (errno == 0 ? "None" : strerror(errno))

#define iact_log_err(M) \
    fprintf( \
        stderr, \
        "[ERROR] (%s:%d: errno: %s) " M "\n", \
        __FILE__, \
        __LINE__, \
        iact_clean_errno())

#define iact_check(A, M) \
    if (!(A)) {\
        iact_log_err(M); \
        errno = 0; \
        goto error; \
    }

#define iact_fwrite(PTR, SIZE_OF_TYPE, NUM, F) { \
    const size_t num_written = fwrite(PTR, SIZE_OF_TYPE, NUM, F); \
    iact_check(num_written == NUM, "Can not write to file."); \
}

#define iact_fread(PTR, SIZE_OF_TYPE, NUM, F) { \
    const size_t num_read = fread(PTR, SIZE_OF_TYPE, NUM, F); \
    iact_check(num_read == NUM, "Can not read from file."); \
}

/**
 * Define the input file for controling the primary particle.
 * @param  name    Input-file-name.
*/
void prmfil_(char *name) {
    const uint64_t sz = sizeof(primary_path);
    const int rc = snprintf(primary_path, sz, "%s", name);
    iact_check(rc > 0 && rc < sz, "Can not copy PRMFIL path.");
    return;
error:
    exit(1);
}


/**
 *  Called at begin of shower. Explicitly set primary particle.
 *  For each shower, the primary_file has one block
 *  [
 *      float64, particle's id
 *      float64, particle's energy
 *      float64, particle's theta
 *      float64, particle's phi
 *      float64, particle's starting depth in atmosphere
 *      int32    random seed
 *  ]
 *  defining the primary particle.
 */
void extprm_(
    cors_real_dbl_t *type,
    cors_real_dbl_t *eprim,
    double *thetap,
    double *phip,
    double *thick0,
    int* iseed) {
    double type_, eprim_, thetap_, phip_, thick0_;
    int32_t iseed_;
    iact_fread(&type_, sizeof(double), 1, primary_file);
    iact_fread(&eprim_, sizeof(double), 1, primary_file);
    iact_fread(&thetap_, sizeof(double), 1, primary_file);
    iact_fread(&phip_, sizeof(double), 1, primary_file);
    iact_fread(&thick0_, sizeof(double), 1, primary_file);
    iact_fread(&iseed_, sizeof(int32_t), 1, primary_file);
    (*type) = type_;
    (*eprim) = eprim_;
    (*thetap) = thetap_;
    (*phip) = phip_;
    (*thick0) = thick0_;
    (*iseed) = iseed_;
    return;
error:
    exit(1);
}
