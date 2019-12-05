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
#include <assert.h>

#include "microtar.h"

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


typedef float cors_real_t;
typedef double cors_real_now_t;
typedef double cors_real_dbl_t;
typedef double cors_dbl_t;

/* =============================================================== */
/* functions called from CORSIKA in fortran77                      */
void telfil_(char *name);
void prmfil_(char *name);
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
    double *thick0,
    int* iseed);


/* =============================================================== */
/* CORSIKA function called from this module: */
extern double heigh_(double *thickness);
extern double refidx_(double *height);

//-------------------- init ----------------------------------------------------
int event_number;
int num_photons_in_event;

char primary_path[1024] = "";
FILE *primary_file;

char* cherenkov_buffer_path = "cherenkov_buffer.float32";
FILE *cherenkov_buffer;

char output_path[1024] = "";
mtar_t tar;

//-------------------- CORSIKA bridge ------------------------------------------

/**
 * Define the output file for photon-bunches.
 * @param  name    Output-file-name.
*/
void telfil_(char *name) {
    const uint64_t sz = sizeof(output_path);
    const int rc = snprintf(output_path, sz, "%s", name);
    iact_check(rc > 0 && rc < sz, "Can not copy TELFIL path.");
    return;
error:
    assert(0);
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
    assert(0);
}


/**
 *  Save aparameters from CORSIKA run header.
 *
 *  @param  runh CORSIKA run header block
 *  @return (none)
*/
void telrnh_(cors_real_t runh[273]) {
    iact_check(
        mtar_open(&tar, output_path, "w") == MTAR_ESUCCESS,
        "Can not open tar.");
    iact_check(
        mtar_write_file_header(
            &tar, "runh.float32", 273*sizeof(cors_real_t)) == MTAR_ESUCCESS,
        "Can not write tar-header of 'runh.float32' to tar.");
    iact_check(
        mtar_write_data(&tar, runh, 273*sizeof(cors_real_t)) == MTAR_ESUCCESS,
        "Can not write data of 'runh.float32' to tar.");

    primary_file = fopen(primary_path, "rb");
    iact_check(primary_file, "Can not open primary_file.");
    return;
error:
    assert(0);
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
    assert(0);
}

/**
 *  Start of new event. Save event parameters.
 *
 *  @param  evth    CORSIKA event header block
 *  @param  prmpar  CORSIKA primary particle block
 *  @return (none)
*/
void televt_(cors_real_t evth[273], cors_real_dbl_t prmpar[PRMPAR_SIZE]) {
    event_number = (int)(round(evth[1]));
    iact_check(event_number > 0, "Expected event_number > 0.");

    char evth_filename[1024] = "";
    snprintf(
        evth_filename,
        sizeof(evth_filename),
        "%09d.evth.float32", event_number);

    iact_check(
        mtar_write_file_header(
            &tar, evth_filename, 273*sizeof(cors_real_t)) == MTAR_ESUCCESS,
        "Can not write tar-header of EVTH to tar-file.");
    iact_check(
        mtar_write_data(&tar, evth, 273*sizeof(cors_real_t)) == MTAR_ESUCCESS,
        "Can not write data of EVTH to tar-file.");

    cherenkov_buffer = fopen(cherenkov_buffer_path, "w");
    iact_check(cherenkov_buffer, "Can not open cherenkov_buffer.");

    num_photons_in_event = 0;
    return;
error:
    assert(0);
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
    float bsize_f = (float)(*bsize);
    float px_f = (float)(*px);
    float py_f = (float)(*py);
    float pu_f = (float)(*pu);
    float pv_f = (float)(*pv);
    float ctime_f = (float)(*ctime);
    float zem_f = (float)(*zem);
    float lambda_f = (float)(*lambda);
    iact_fwrite(&px_f, sizeof(float), 1, cherenkov_buffer);
    iact_fwrite(&py_f, sizeof(float), 1, cherenkov_buffer);
    iact_fwrite(&pu_f, sizeof(float), 1, cherenkov_buffer);
    iact_fwrite(&pv_f, sizeof(float), 1, cherenkov_buffer);
    iact_fwrite(&ctime_f, sizeof(float), 1, cherenkov_buffer);
    iact_fwrite(&zem_f, sizeof(float), 1, cherenkov_buffer);
    iact_fwrite(&bsize_f, sizeof(float), 1, cherenkov_buffer);
    iact_fwrite(&lambda_f, sizeof(float), 1, cherenkov_buffer);
    num_photons_in_event = num_photons_in_event + 1;
    return 0;
error:
    assert(0);
    return -1;
}


/**
 *  End of event. Write photon-bunches into tar-file.
*/
void telend_(cors_real_t evte[273]) {
    int64_t sizeof_cherenkov_buffer = ftell(cherenkov_buffer);
    iact_check(sizeof_cherenkov_buffer >= 0, "Can't ftell cherenkov_buffer");

    iact_check(fclose(cherenkov_buffer) == 0, "Can't close cherenkov_buffer.");

    cherenkov_buffer = fopen(cherenkov_buffer_path, "r");
    iact_check(cherenkov_buffer, "Can not re-open cherenkov_buffer for read.");

    char bunch_filename[1024] = "";
    snprintf(
        bunch_filename,
        sizeof(bunch_filename),
        "%09d.cherenkov_bunches.Nx8_float32", event_number);

    iact_check(
        mtar_write_file_header(
            &tar, bunch_filename, sizeof_cherenkov_buffer) == MTAR_ESUCCESS,
        "Can't write tar-header of bunches to tar-file.");
    iact_check(
        mtar_write_data_from_stream(
            &tar, cherenkov_buffer, sizeof_cherenkov_buffer) == MTAR_ESUCCESS,
        "Can't write data of bunches to tar-file.");

    iact_check(fclose(cherenkov_buffer) == 0, "Can't close cherenkov_buffer.");
    return;
error:
    assert(0);
}


/**
 *   End of run. Finalize and close tar-file.
 *
 *  @param  rune  CORSIKA run end block
*/
void telrne_(cors_real_t rune[273]) {
    iact_check(
        mtar_finalize(&tar) == MTAR_ESUCCESS,
        "Can't finalize tar-file.");
    iact_check(
        mtar_close(&tar) == MTAR_ESUCCESS,
        "Can't close tar-file.");
    iact_check(
        fclose(primary_file) == 0,
        "Can't close primary_file.");
    return;
error:
    assert(0);
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
