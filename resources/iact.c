/* Copyright (c)

    Sebastian Achim Mueller, ETH Zurich 2016

    This file originated from the iact.c file which is part of the IACT/atmo
    package for CORSIKA by Konrad Bernloehr.

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

#define PRMPAR_SIZE 17

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <errno.h>
#include <ctype.h>

#include "microtar.h"

typedef float cors_real_t;
typedef double cors_real_now_t;
typedef double cors_real_dbl_t;
typedef double cors_dbl_t;

/* =============================================================== */
/* FORTRAN called functions                                        */
/* The additional character string lengths for name in telfil_ and */
/* line in tellni_ are not used because compiler-dependent.        */
void telfil_(char *name);
void telset_(
    cors_real_now_t *x,
    cors_real_now_t *y,
    cors_real_now_t *z,
    cors_real_now_t *r);
void telrnh_(cors_real_t runh[273]);
void telrne_(cors_real_t rune[273]);
void televt_(
    cors_real_t evth[273],
    cors_real_dbl_t prmpar[PRMPAR_SIZE]);
int telout_(
    cors_real_now_t *bsize,
    cors_real_now_t *wt,
    cors_real_now_t *px,
    cors_real_now_t *py,
    cors_real_now_t *pu,
    cors_real_now_t *pv,
    cors_real_now_t *ctime,
    cors_real_now_t *zem,
    cors_real_now_t *lambda);
void telend_(cors_real_t evte[273]);


/* =============================================================== */
/* CORSIKA function called from this module: */
extern double heigh_(double *thickness);
extern double refidx_(double *height);

//-------------------- init ----------------------------------------------------
int event_number;

int num_photons_in_event;

char output_path[1024] = "";

char cherenkov_buffer_path[1024] = "";
FILE *cherenkov_buffer;

mtar_t tar;

//-------------------- CORSIKA bridge ------------------------------------------

/**
 * Define the output file for photon bunches hitting the telescopes.
 * @param  name    Output file name.
*/
void telfil_(char *name) {
    snprintf(output_path, sizeof(output_path), "%s", name);
    return;
}


/**
 *  Add another telescope to the system (array) of telescopes.
 *
 *  This function is called for each TELESCOPE keyword in the
 *  CORSIKA input file.
 *
 *  @param  x  X position [cm]
 *  @param  y  Y position [cm]
 *  @param  z  Z position [cm]
 *  @param  r  radius [cm] within which the telescope is fully contained
 *  @return (none)
*/
void telset_(
    cors_real_now_t *x,
    cors_real_now_t *y,
    cors_real_now_t *z,
    cors_real_now_t *r
) {
    return;
}


/**
 *  Save aparameters from CORSIKA run header.
 *
 *  @param  runh CORSIKA run header block
 *  @return (none)
*/
void telrnh_(cors_real_t runh[273]) {
    snprintf(
        cherenkov_buffer_path,
        sizeof(cherenkov_buffer_path),
        "cherenkov_buffer.float32");

    fprintf(stderr, "Open microtar.\n");
    mtar_open(&tar, output_path, "w");

    mtar_write_file_header(&tar, "runh.float32", 273*sizeof(cors_real_t));
    mtar_write_data(&tar, runh, 273*sizeof(cors_real_t));
}


/**
 *  Start of new event. Save event parameters.
 *
 *  @param  evth    CORSIKA event header block
 *  @param  prmpar  CORSIKA primary particle block
 *  @return (none)
*/
void televt_(cors_real_t evth[273], cors_real_dbl_t prmpar[PRMPAR_SIZE]) {
    char evth_filename[1024] = "";
    snprintf(
        evth_filename,
        sizeof(evth_filename),
        "%06d.evth.float32", event_number);

    fprintf(stderr, "Event header name: %s\n", evth_filename);

    mtar_write_file_header(&tar, evth_filename, 273*sizeof(cors_real_t));
    mtar_write_data(&tar, evth, 273*sizeof(cors_real_t));

    num_photons_in_event = 0;
    fprintf(stderr, "Open cherenkov_buffer.\n");
    cherenkov_buffer = fopen(cherenkov_buffer_path, "w");
}


/**
 *  Check if a photon bunch hits one or more simulated detector volumes.
 *
 *  @param  bsize   Number of photons (can be fraction of one)
 *  @param  wt     Weight (if thinning option is active)
 *  @param  px     x position in detection level plane
 *  @param  py     y position in detection level plane
 *  @param  pu     x direction cosine
 *  @param  pv     y direction cosine
 *  @param  ctime   arrival time in plane after first interaction
 *  @param  zem     height of emission above sea level
 *  @param  lambda  0. (if wavelength undetermined) or wavelength [nm].
 *                  If lambda < 0, photons are already converted to
 *                  photo-electrons (p.e.), i.e. we have p.e. bunches.
 *  @param  temis   Time of photon emission 
 *  @param  penergy Energy of emitting particle.
 *  @param  amass   Mass of emitting particle.
 *  @param  charge  Charge of emitting particle.
 *
 *  @return  0 (no output to old-style CORSIKA file needed)
 *           2 (detector hit but no eventio interface available or
 *             output should go to CORSIKA file anyway)
*/
int telout_(
    cors_real_now_t *bsize,
    cors_real_now_t *wt,
    cors_real_now_t *px,
    cors_real_now_t *py,
    cors_real_now_t *pu,
    cors_real_now_t *pv,
    cors_real_now_t *ctime,
    cors_real_now_t *zem ,
    cors_real_now_t *lambda
    /*double *temis,
    double *penergy,
    double *amass,
    double *charge*/
) {
    float bsize_f = (float)(*bsize);
    float px_f = (float)(*px);
    float py_f = (float)(*py);
    float pu_f = (float)(*pu);
    float pv_f = (float)(*pv);
    float ctime_f = (float)(*ctime);
    float zem_f = (float)(*zem);
    float lambda_f = (float)(*lambda);

    fwrite(&px_f, sizeof(float), 1, cherenkov_buffer);
    fwrite(&py_f, sizeof(float), 1, cherenkov_buffer);
    fwrite(&pu_f, sizeof(float), 1, cherenkov_buffer);
    fwrite(&pv_f, sizeof(float), 1, cherenkov_buffer);
    fwrite(&ctime_f, sizeof(float), 1, cherenkov_buffer);
    fwrite(&zem_f, sizeof(float), 1, cherenkov_buffer);
    fwrite(&bsize_f, sizeof(float), 1, cherenkov_buffer);
    fwrite(&lambda_f, sizeof(float), 1, cherenkov_buffer);

    num_photons_in_event = num_photons_in_event + 1;
    return 0;
}


/**
 *  End of event. Write out all recorded photon bunches.
*/
void telend_(cors_real_t evte[273]) {
    uint64_t sizeof_cherenkov_buffer = ftell(cherenkov_buffer);
    fclose(cherenkov_buffer);

    cherenkov_buffer = fopen(cherenkov_buffer_path, "r");

    fprintf(stderr, "cherenkov_buffer size is %ld.\n", sizeof_cherenkov_buffer);
    fprintf(stderr, "%d bunches in cherenkov_buffer.\n", num_photons_in_event);

    char bunch_filename[1024] = "";
    snprintf(
        bunch_filename,
        sizeof(bunch_filename),
        "%06d.photons.float32", event_number);

    mtar_write_file_header(&tar, bunch_filename, sizeof_cherenkov_buffer);
    mtar_write_stream(&tar, cherenkov_buffer, sizeof_cherenkov_buffer);

    fprintf(stderr, "Close cherenkov_buffer.\n");
    fclose(cherenkov_buffer);
    return;
}


//-------------------- UNUSED SO FAR -------------------------------------------
void telsmp_(char *name);
void telshw_(void);
void telinf_(
    int *itel,
    double *x,
    double *y,
    double *z,
    double *r,
    int *exists);
void tellni_(char *line, int *llength);
void telasu_(
    int *n,
    cors_real_dbl_t *dx,
    cors_real_dbl_t *dy);
void telprt_(cors_real_t* datab, int *maxbuf);
void tellng_(
    int *type,
    double *data,
    int *ndim,
    int *np,
    int *nthick,
    double *thickstep);
void extprm_(
    cors_real_dbl_t *type,
    cors_real_dbl_t *eprim,
    double *thetap,
    double *phip);


/**
 *  Placeholder function for external shower-by-shower setting
 *         of primary type, energy, and direction.
 */
void extprm_(
    cors_real_dbl_t *type,
    cors_real_dbl_t *eprim,
    double *thetap,
    double *phip
) {
    return;
}


/**
 *  Set the file name with parameters for importance sampling.
 */
void telsmp_(char *name) {
    return;
}


/**
 *  Show what telescopes have actually been set up.
 *  This function is called by CORSIKA after the input file is read.
*/
void telshw_() {
    return;
}


/**
 * Return information about configured telescopes back to CORSIKA
 *
 * @param  itel     number of telescope in question
 * @param  x, y, z  telescope position [cm]
 * @param  r       radius of fiducial volume [cm]
 * @param  exists   telescope exists
*/
void telinf_(
    int *itel,
    double *x,
    double *y,
    double *z,
    double *r,
    int *exists
) {
    fprintf(stderr, "ABORT: The telinf_ was called.\n");
    exit(1);
}


/**
 *  Keep a record of CORSIKA input lines.
 *
 *  @param  line     input line (not terminated)
 *  @param  llength  maximum length of input lines (132 usually)
*/
void tellni_(char *line, int *llength) {
    return;
}


/**
 *   Write run end block to the output file.
 *
 *  @param  rune  CORSIKA run end block
*/
void telrne_(cors_real_t rune[273]) {
    fprintf(stderr, "Close microtar.\n");
    mtar_finalize(&tar);
    mtar_close(&tar);
    return;
}


/**
 *  Setup how many times each shower is used.
 *
 *  @param n   The number of telescope systems
 *  @param dx  Core range radius (if dy==0) or core x range
 *  @param dy  Core y range (non-zero for ractangular, 0 for circular)
 *  @return (none)
*/
void telasu_(int *n, cors_real_dbl_t *dx, cors_real_dbl_t *dy) {
    return;
}


/**
 *  @short Store CORSIKA particle information into IACT output file.
 *
 *  @param datab  A particle data buffer with up to 39 particles.
 *  @param maxbuf The buffer size, which is 39*7 without thinning
 *                option and 39*8 with thinning.
 */
void telprt_(cors_real_t *datab, int *maxbuf) {
    return;
}


/**
 *  Write CORSIKA 'longitudinal' (vertical) distributions.
 *
 *  @param  type    see above
 *  @param  data    set of (usually 9) distributions
 *  @param  ndim    maximum number of entries per distribution
 *  @param  np      number of distributions (usually 9)
 *  @param  nthick  number of entries actually filled per distribution
 *                  (is 1 if called without LONGI being enabled).
 *  @param  thickstep  step size in g/cm**2
 *  @return  (none)
*/
void tellng_(
    int *type,
    double *data,
    int *ndim,
    int *np,
    int *nthick,
    double *thickstep
) {
    return;
}
