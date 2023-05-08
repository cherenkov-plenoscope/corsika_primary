/* Copyright (c)

    Sebastian Achim Mueller, ETH Zurich 2016
                             MPI Heidelberg 2019

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
#include <stdint.h>

#include "mli_corsika_EventTape_headeronly.h"

typedef float cors_real_t;
typedef double cors_real_now_t;
typedef double cors_real_dbl_t;
typedef double cors_dbl_t;

/* =============================================================== */
/* functions called from CORSIKA in fortran77                      */
void telfil_(char *name);
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
void extprm_(
    cors_real_dbl_t *type,
    cors_real_dbl_t *eprim,
    double *thetap,
    double *phip,
    double *thick0);

/* =============================================================== */
/* CORSIKA function called from this module: */
extern double heigh_(double *thickness);
extern double refidx_(double *height);

//-------------------- init ----------------------------------------------------
int event_number;

const char *PRIMARY_PATH = "primaries.x5.float64";
FILE *primary_file = NULL;

char output_path[1024] = "";
const uint64_t CHERENKOV_BUFFER_SIZE = 1048576;
struct mliEventTapeWriter taro;

//-------------------- CORSIKA bridge ------------------------------------------

/**
 * Define the output file for photon-bunches.
 * @param  name    Output-file-name.
*/
void telfil_(char *name) {
    const uint64_t sz = sizeof(output_path);
    const int rc = snprintf(output_path, sz, "%s", name);
    chk_msg(rc > 0 && rc < sz, "Can not copy TELFIL path.");
    return;
error:
    exit(1);
}


/**
 *  Save aparameters from CORSIKA run header.
 *
 *  @param  runh CORSIKA run header block
 *  @return (none)
*/
void telrnh_(cors_real_t runh[273]) {
    taro = mliEventTapeWriter_init();
    chk_msg(
        mliEventTapeWriter_open(&taro, output_path, CHERENKOV_BUFFER_SIZE),
        "Can't open EventTapeWriter."
    );
    chk_msg(
        mliEventTapeWriter_write_runh(&taro, runh),
        "Can't write RUNH to EventTape."
    );
    primary_file = fopen(PRIMARY_PATH, "rb");
    chk_msg(primary_file, "Can't open primary_file.");
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
 *  ]
 *  defining the primary particle.
 */
void extprm_(
    cors_real_dbl_t *type,
    cors_real_dbl_t *eprim,
    double *thetap,
    double *phip,
    double *thick0) {
    double type_, eprim_, thetap_, phip_, thick0_;

    chk_fread(&type_, sizeof(double), 1, primary_file);
    chk_fread(&eprim_, sizeof(double), 1, primary_file);
    chk_fread(&thetap_, sizeof(double), 1, primary_file);
    chk_fread(&phip_, sizeof(double), 1, primary_file);
    chk_fread(&thick0_, sizeof(double), 1, primary_file);

    (*type) = type_;
    (*eprim) = eprim_;
    (*thetap) = thetap_;
    (*phip) = phip_;
    (*thick0) = thick0_;

    return;
error:
    exit(1);
}


/**
 *  Start of new event. Save event parameters.
 *
 *  @param  evth    CORSIKA event header block
 *  @param  prmpar  CORSIKA primary particle block
 *  @return (none)
*/
void televt_(cors_real_t evth[273], cors_real_dbl_t prmpar[PRMPAR_SIZE]) {
    chk_msg(
        mliEventTapeWriter_write_evth(&taro, evth),
        "Can't write EVTH to EventTapeWriter."
    );
    return;
error:
    exit(1);
}


/**
 *  Store photon-bunch.
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
    cors_real_now_t *lambda) {
    float bunch[8];
    bunch[0] = (float)(*px);
    bunch[1] = (float)(*py);
    bunch[2] = (float)(*pu);
    bunch[3] = (float)(*pv);
    bunch[4] = (float)(*ctime);
    bunch[5] = (float)(*zem);
    bunch[6] = (float)(*bsize);
    bunch[7] = (float)(*lambda);
    chk_msg(
        mliEventTapeWriter_write_cherenkov_bunch(&taro, bunch),
        "Can't write Cherenkov-bunch to EventTapeWriter."
    );
    return 1;
error:
    exit(1);
    return -1;
}


/**
 *  End of event.
*/
void telend_(cors_real_t evte[273]) {
    return;
}


/**
 *   End of run. Finalize and close tar-file.
 *
 *  @param  rune  CORSIKA run end block
*/
void telrne_(cors_real_t rune[273]) {
    chk_msg(mliEventTapeWriter_close(&taro), "Can't close EventTapeWriter.");
    return;
error:
    exit(1);
}


//-------------------- UNUSED --------------------------------------------------
void telset_(
    cors_real_now_t *x,
    cors_real_now_t *y,
    cors_real_now_t *z,
    cors_real_now_t *r);
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

/* particle output */
/* --------------- */
void ppprnh_(cors_real_t runh[273]);
void ppprne_(cors_real_t rune[273]);
void pppevt_(cors_real_t evth[273]);
void pppend_(cors_real_t evte[273]);
void pppout_(cors_real_t datab[273]);

FILE *ppp_file = NULL;

void ppprnh_(cors_real_t runh[273]) {
    fprintf(stderr, "%s, %d, %s\n", __FILE__, __LINE__, __func__);
    chk_msg(output_path[0] != '\0', "Expected output_path to be set.");
    const uint64_t sz = sizeof(output_path);
    char ppp_output_path[sizeof(output_path) + 128] = "";
    const uint64_t ppp_sz = sizeof(ppp_output_path);

    const int rc = snprintf(ppp_output_path, ppp_sz, "%s.par.dat", output_path);
    chk_msg(
        rc > 0 && rc < ppp_sz,
        "Can not copy output_path into ppp_output_path."
    );
    chk_msg(ppp_file == NULL, "Expected ppp_file to be NULL");

    ppp_file = fopen(ppp_output_path, "w+b");
    chk_msg(ppp_file, "Can't open ppp_file.");

    chk_fwrite(runh, sizeof(float), 273, ppp_file);
    fflush(ppp_file);
    return;
error:
    exit(1);
}

void pppevt_(cors_real_t evth[273]) {
    fprintf(stderr, "%s, %d, %s\n", __FILE__, __LINE__, __func__);
    chk_fwrite(evth, sizeof(float), 273, ppp_file);
    fflush(ppp_file);
    return;
error:
    exit(1);
}

void pppout_(cors_real_t datab[273]) {
    fprintf(stderr, "%s, %d, %s\n", __FILE__, __LINE__, __func__);
    chk_fwrite(datab, sizeof(float), 273, ppp_file);
    return;
error:
    exit(1);
}

void pppend_(cors_real_t evte[273]) {
    fprintf(stderr, "%s, %d, %s\n", __FILE__, __LINE__, __func__);
    chk_fwrite(evte, sizeof(float), 273, ppp_file);
    fflush(ppp_file);
    return;
error:
    exit(1);
}

void ppprne_(cors_real_t rune[273]) {
    fprintf(stderr, "%s, %d, %s\n", __FILE__, __LINE__, __func__);
    chk_fwrite(rune, sizeof(float), 273, ppp_file);
    fflush(ppp_file);
    return;
error:
    exit(1);
}
