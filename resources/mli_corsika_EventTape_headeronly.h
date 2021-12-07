#include <stdio.h>
#include <stdint.h>
#include <limits.h>
#include <stdlib.h>
#include <ctype.h>
#include <math.h>
#include <float.h>
#include <stdarg.h>
#include <stddef.h>
#include <assert.h>
#include <string.h>
#include <errno.h>



/* chk_debug.h */
/* Copyright 2018-2020 Sebastian Achim Mueller */
#ifndef CHK_DEBUG_H_
#define CHK_DEBUG_H_


/*
 *  Based on Zed Shawn's awesome Debug Macros from his book:
 *  Learn C the hard way
 */

#define chk_clean_errno() (errno == 0 ? "None" : strerror(errno))
#define chk(C) chk_msg(C, "Not expected.")
#define chk_mem(C) chk_msg((C), "Out of memory.")

#define chk_eprint(MSG)                                                        \
        fprintf(stderr,                                                        \
                "[ERROR] (%s:%d: errno: %s) " MSG "\n",                        \
                __FILE__,                                                      \
                __LINE__,                                                      \
                chk_clean_errno())

#define chk_msg(C, MSG)                                                        \
        if (!(C)) {                                                            \
                chk_eprint(MSG);                                               \
                errno = 0;                                                     \
                goto error;                                                    \
        }

#define chk_bad(MSG)                                                           \
        {                                                                      \
                chk_eprint(MSG);                                               \
                errno = 0;                                                     \
                goto error;                                                    \
        }

#define chk_malloc(PTR, TYPE, NUM)                                             \
        {                                                                      \
                PTR = (TYPE *)malloc(NUM * sizeof(TYPE));                      \
                chk_mem(PTR);                                                  \
        }

#define chk_fwrite(PTR, SIZE_OF_TYPE, NUM, F)                                  \
        {                                                                      \
                const uint64_t num_written =                                   \
                        fwrite(PTR, SIZE_OF_TYPE, NUM, F);                     \
                chk_msg(num_written == NUM, "Can not write to file.");         \
        }

#define chk_fread(PTR, SIZE_OF_TYPE, NUM, F)                                   \
        {                                                                      \
                const uint64_t num_read = fread(PTR, SIZE_OF_TYPE, NUM, F);    \
                chk_msg(num_read == NUM, "Can not read from file.");           \
        }

#endif



/* mli_version.h */
/* Copyright 2018-2020 Sebastian Achim Mueller */
#ifndef MLI_VERSION_H_
#define MLI_VERSION_H_


#define MLI_VERSION_MAYOR 1
#define MLI_VERSION_MINOR 5
#define MLI_VERSION_PATCH 2

void mli_logo_fprint(FILE *f);
void mli_authors_and_affiliations_fprint(FILE *f);
#endif



/* mli_math.h */
/* Copyright 2018-2020 Sebastian Achim Mueller */
#ifndef MLI_MATH_H_
#define MLI_MATH_H_


#define MLI_PI 3.14159265358979323846
#define MLI_2PI 6.28318530717958623199
#define MLI_2_OVER_SQRT3 1.1547005383792517
#define MLI_SQRT3_OVER_2 0.8660254037844386
#define MLI_EPSILON 1e-9
#define MLI_NAN 0. / 0.
#define MLI_IS_NAN(a) ((a) != (a))
#define MLI_MIN2(a, b) (((a) < (b)) ? (a) : (b))
#define MLI_MAX2(a, b) (((a) > (b)) ? (a) : (b))
#define MLI_ROUND(num) (num - floor(num) > 0.5) ? ceil(num) : floor(num)
#define MLI_NEAR_INT(x) ((x) > 0 ? (int64_t)((x) + 0.5) : (int64_t)((x)-0.5))

#define MLI_MIN3(a, b, c)                                                      \
        ((((a) < (b)) && ((a) < (c))) ? (a) : (((b) < (c)) ? (b) : (c)))

#define MLI_MAX3(a, b, c)                                                      \
        ((((a) > (b)) && ((a) > (c))) ? (a) : (((b) > (c)) ? (b) : (c)))

#define MLI_ARRAY_SET(arr, val, num)                                           \
        do {                                                                   \
                uint64_t i;                                                    \
                for (i = 0; i < num; i++) {                                    \
                        arr[i] = val;                                          \
                }                                                              \
        } while (0)

#define MLI_UPPER_COMPARE(points, num_points, point_arg, return_idx)           \
        do {                                                                   \
                uint64_t first, last, middle;                                  \
                first = 0u;                                                    \
                last = num_points - 1u;                                        \
                middle = (last - first) / 2;                                   \
                if (num_points == 0) {                                         \
                        return_idx = 0;                                        \
                } else {                                                       \
                        if (point_arg >= points[num_points - 1u]) {            \
                                return_idx = num_points;                       \
                        } else {                                               \
                                while (first < last) {                         \
                                        if (points[middle] > point_arg) {      \
                                                last = middle;                 \
                                        } else {                               \
                                                first = middle + 1u;           \
                                        }                                      \
                                        middle = first + (last - first) / 2;   \
                                }                                              \
                                return_idx = last;                             \
                        }                                                      \
                }                                                              \
        } while (0)

#define MLI_NCPY(src, dst, num)                                                \
        do {                                                                   \
                uint64_t i;                                                    \
                for (i = 0; i < num; i++) {                                    \
                        dst[i] = src[i];                                       \
                }                                                              \
        } while (0)

double mli_std(
        const double vals[],
        const uint64_t size,
        const double vals_mean);
double mli_mean(const double vals[], const uint64_t size);
void mli_linspace(
        const double start,
        const double stop,
        double *points,
        const uint64_t num_points);
void mli_histogram(
        const double *bin_edges,
        const uint64_t num_bin_edges,
        uint64_t *underflow_bin,
        uint64_t *bins,
        uint64_t *overflow_bin,
        const double point);
uint64_t mli_upper_compare_double(
        const double *points,
        const uint64_t num_points,
        const double point_arg);
double mli_square(const double a);
double mli_hypot(const double a, const double b);
double mli_deg2rad(const double angle_in_deg);
double mli_rad2deg(const double angle_in_rad);
double mli_bin_center_in_linear_space(
        const double start,
        const double stop,
        const uint64_t num_bins,
        const uint64_t bin);
double mli_linear_interpolate_1d(
        const double weight,
        const double start,
        const double end);
double mli_linear_interpolate_2d(
        const double xarg,
        const double x0,
        const double y0,
        const double x1,
        const double y1);
#endif



/* mli_cstr.h */
/* Copyright 2018-2020 Sebastian Achim Mueller */
#ifndef MLI_CSTR_H_
#define MLI_CSTR_H_

int mli_cstr_ends_with(const char *str, const char *sufix);
int mli_cstr_starts_with(const char *str, const char *prefix);
int mli_cstr_has_prefix_suffix(
        const char *str,
        const char *prefix,
        const char *sufix);

int mli_cstr_split(
        const char *str,
        const char delimiter,
        char *token,
        const uint64_t token_length);
int mli_cstr_is_CRLF(const char *s);
int mli_cstr_is_CR(const char *s);
int mli_cstr_assert_only_NUL_LF_TAB_controls(const char *str);
int mli_cstr_assert_only_NUL_LF_TAB_controls_dbg(
        const char *str,
        const int dbg);

uint64_t mli_cstr_count_chars_up_to(
        const char *str,
        const char c,
        const uint64_t num_chars_to_scan);

int mli_cstr_lines_fprint(
        FILE *f,
        const char *str,
        const uint64_t line,
        const uint64_t line_radius);
void mli_cstr_path_strip_this_dir(char *dst, const char *src);

void mli_cstr_path_basename_without_extension(const char *filename, char *key);
void mli_cstr_strip_spaces(const char *in, char *out);

int mli_cstr_match_templeate(
        const char *s,
        const char *t,
        const char digit_wildcard);

#endif



/* mli_cstr_numbers.h */
/* Copyright 2018-2020 Sebastian Achim Mueller */
#ifndef MLI_CSTR_NUMBERS_H_
#define MLI_CSTR_NUMBERS_H_


int mli_cstr_nto_int64(
        int64_t *out,
        const char *s,
        const uint64_t base,
        const uint64_t length);
int mli_cstr_to_int64(int64_t *out, const char *s, const uint64_t base);

int mli_cstr_nto_uint64(
        uint64_t *out,
        const char *s,
        const uint64_t base,
        const uint64_t length);
int mli_cstr_to_uint64(uint64_t *out, const char *s, const uint64_t base);

int mli_cstr_nto_double(double *out, const char *s, const uint64_t length);
int mli_cstr_to_double(double *out, const char *s);

int mli_cstr_print_uint64(
        uint64_t u,
        char *s,
        const uint64_t max_num_chars,
        const uint64_t base,
        const uint64_t min_num_digits);

#endif



/* mli_quadratic_equation.h */
/* Copyright 2019 Sebastian A. Mueller */
#ifndef MLI_QUADRATIC_EQUATION_H_
#define MLI_QUADRATIC_EQUATION_H_

int mli_quadratic_equation(
        const double p,
        const double q,
        double *minus_solution,
        double *plus_solution);

#endif



/* mliVec.h */
/* Copyright 2018-2020 Sebastian Achim Mueller */
#ifndef MLIVEC_H_
#define MLIVEC_H_


struct mliVec {
        double x;
        double y;
        double z;
};

void mliVec_print(const struct mliVec v);
uint32_t mliVec_octant(const struct mliVec a);
int mliVec_equal(const struct mliVec a, const struct mliVec b);
int mliVec_equal_margin(
        const struct mliVec a,
        const struct mliVec b,
        const double distance_margin);
struct mliVec mliVec_mirror(const struct mliVec in, const struct mliVec normal);
double mliVec_norm_between(const struct mliVec a, const struct mliVec b);
double mliVec_angle_between(const struct mliVec a, const struct mliVec b);
struct mliVec mliVec_normalized(struct mliVec a);
double mliVec_norm(const struct mliVec a);
struct mliVec mliVec_multiply(const struct mliVec v, const double a);
double mliVec_dot(const struct mliVec a, const struct mliVec b);
struct mliVec mliVec_cross(const struct mliVec a, const struct mliVec b);
struct mliVec mliVec_substract(const struct mliVec a, const struct mliVec b);
struct mliVec mliVec_add(const struct mliVec a, const struct mliVec b);
struct mliVec mliVec_set(const double x, const double y, const double z);
int mliVec_sign3_bitmask(const struct mliVec a, const double epsilon);
#endif



/* mliRay.h */
/* Copyright 2018-2020 Sebastian Achim Mueller */
#ifndef MLIRAY_H_
#define MLIRAY_H_


struct mliRay {
        struct mliVec support;
        struct mliVec direction;
} mliRay;

struct mliVec mliRay_at(const struct mliRay *ray, const double t);
struct mliRay mliRay_set(
        const struct mliVec support,
        const struct mliVec direction);
int mliRay_sphere_intersection(
        const struct mliVec support,
        const struct mliVec direction,
        const double radius,
        double *minus_solution,
        double *plus_solution);
#endif



/* mliPhoton.h */
/* Copyright 2018-2020 Sebastian Achim Mueller */
#ifndef MLIPHOTON_H_
#define MLIPHOTON_H_


struct mliPhoton {
        struct mliRay ray;
        double wavelength;
        int64_t id;
};

#endif



/* mliTar.h */
/**
 * Copyright (c) 2017 rxi
 * Copyright (c) 2019 Sebastian A. Mueller
 *                    Max-Planck-Institute for nuclear-physics, Heidelberg
 *
 * This library is free software; you can redistribute it and/or modify it
 * under the terms of the MIT license.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */

#ifndef MLITAR_H_
#define MLITAR_H_


#define MLI_TAR_NORMAL_FILE '0'
#define MLI_TAR_HARD_LINK '1'
#define MLI_TAR_SYMBOLIC_LINK '2'
#define MLI_TAR_CHARACTER_SPECIAL '3'
#define MLI_TAR_BLOCK_SPECIAL '4'
#define MLI_TAR_DIRECTORY '5'
#define MLI_TAR_FIFO '6'
#define MLI_TAR_NAME_LENGTH 100
#define MLI_TAR_OCTAL 8u
#define MLI_TAR_MAX_FILESIZE_OCTAL 8589934592lu /* 8^11 */

struct mliTarHeader {
        uint64_t mode;
        uint64_t owner;
        uint64_t size;
        uint64_t mtime;
        uint64_t type;
        char name[MLI_TAR_NAME_LENGTH];
        char linkname[MLI_TAR_NAME_LENGTH];
};

struct mliTarHeader mliTarHeader_init(void);
int mliTarHeader_set_directory(struct mliTarHeader *h, const char *name);
int mliTarHeader_set_normal_file(
        struct mliTarHeader *h,
        const char *name,
        const uint64_t size);

struct mliTar {
        FILE *stream;
        uint64_t pos;
        uint64_t remaining_data;
};

struct mliTar mliTar_init(void);
int mliTar_open(struct mliTar *tar, const char *filename, const char *mode);
int mliTar_finalize(struct mliTar *tar);
int mliTar_close(struct mliTar *tar);

int mliTar_read_header(struct mliTar *tar, struct mliTarHeader *h);
int mliTar_read_data(struct mliTar *tar, void *ptr, uint64_t size);

int mliTar_write_header(struct mliTar *tar, const struct mliTarHeader *h);
int mliTar_write_data(struct mliTar *tar, const void *data, uint64_t size);

/* internal */
int mliTar_uint64_to_field12_2001star_base256(uint64_t val, char *field);
int mliTar_field12_to_uint64_2001star_base256(const char *field, uint64_t *val);

#endif



/* mliDynArray.h */
/* Copyright 2018-2020 Sebastian Achim Mueller */
#ifndef MLIDYNARRAY_H_
#define MLIDYNARRAY_H_


#define MLIDYNARRAY_DEFINITON(LIB, NAME, PAYLOAD_TYPE)                         \
                                                                               \
        struct LIB##Dyn##NAME {                                                \
                uint64_t capacity;                                             \
                uint64_t size;                                                 \
                PAYLOAD_TYPE *array;                                           \
        };                                                                     \
                                                                               \
        struct LIB##Dyn##NAME LIB##Dyn##NAME##_init(void);                     \
                                                                               \
        void LIB##Dyn##NAME##_free(struct LIB##Dyn##NAME *dh);                 \
                                                                               \
        int LIB##Dyn##NAME##_malloc(                                           \
                struct LIB##Dyn##NAME *dh, const uint64_t size);               \
                                                                               \
        int LIB##Dyn##NAME##_malloc_set_size(                                  \
                struct LIB##Dyn##NAME *dh, const uint64_t size);               \
                                                                               \
        int LIB##Dyn##NAME##_push_back(                                        \
                struct LIB##Dyn##NAME *dh, PAYLOAD_TYPE item);

#define MLIDYNARRAY_IMPLEMENTATION(LIB, NAME, PAYLOAD_TYPE)                    \
                                                                               \
        struct LIB##Dyn##NAME LIB##Dyn##NAME##_init(void)                      \
        {                                                                      \
                struct LIB##Dyn##NAME dh;                                      \
                dh.capacity = 0u;                                              \
                dh.size = 0u;                                                  \
                dh.array = NULL;                                               \
                return dh;                                                     \
        }                                                                      \
                                                                               \
        void LIB##Dyn##NAME##_free(struct LIB##Dyn##NAME *dh)                  \
        {                                                                      \
                free(dh->array);                                               \
                (*dh) = LIB##Dyn##NAME##_init();                               \
        }                                                                      \
                                                                               \
        int LIB##Dyn##NAME##_malloc(                                           \
                struct LIB##Dyn##NAME *dh, const uint64_t size)                \
        {                                                                      \
                LIB##Dyn##NAME##_free(dh);                                     \
                dh->capacity = MLI_MAX2(2, size);                              \
                dh->size = 0;                                                  \
                chk_malloc(dh->array, PAYLOAD_TYPE, dh->capacity);             \
                return 1;                                                      \
        error:                                                                 \
                return 0;                                                      \
        }                                                                      \
                                                                               \
        int LIB##Dyn##NAME##_malloc_set_size(                                  \
                struct LIB##Dyn##NAME *dh, const uint64_t size)                \
        {                                                                      \
                chk(LIB##Dyn##NAME##_malloc(dh, size));                        \
                dh->size = size;                                               \
                return 1;                                                      \
        error:                                                                 \
                return 0;                                                      \
        }                                                                      \
                                                                               \
        int LIB##Dyn##NAME##_push_back(                                        \
                struct LIB##Dyn##NAME *dh, PAYLOAD_TYPE item)                  \
        {                                                                      \
                if (dh->size == dh->capacity) {                                \
                        dh->capacity = dh->capacity * 2;                       \
                        dh->array = (PAYLOAD_TYPE *)realloc(                   \
                                (void *)dh->array,                             \
                                dh->capacity * sizeof(PAYLOAD_TYPE));          \
                        chk_mem(dh->array);                                    \
                }                                                              \
                                                                               \
                dh->array[dh->size] = item;                                    \
                dh->size += 1;                                                 \
                                                                               \
                return 1;                                                      \
        error:                                                                 \
                return 0;                                                      \
        }

#endif



/* mli_corsika_version.h */
/* Copyright 2018-2020 Sebastian Achim Mueller */
#ifndef MLI_CORSIKA_VERSION_H_
#define MLI_CORSIKA_VERSION_H_

#define MLI_CORSIKA_VERSION_MAYOR 0
#define MLI_CORSIKA_VERSION_MINOR 2
#define MLI_CORSIKA_VERSION_PATCH 0

#endif



/* mli_corsika_utils.h */
/* Copyright 2020 Sebastian A. Mueller */
#ifndef MLI_CORSIKA_UTILS_H_
#define MLI_CORSIKA_UTILS_H_


float mli_4chars_to_float(const char *four_char_word);

#define MLI_CORSIKA_HEADER_SIZE (sizeof(float) * 273)
#define MLI_CORSIKA_BUNCH_SIZE (sizeof(float) * 8)

#define MLI_CORSIKA_RUNH_RUN_NUMBER 1
#define MLI_CORSIKA_RUNH_SLOPE_OF_ENERGY_SPECTRUM 15
#define MLI_CORSIKA_RUNH_ENERGY_RANGE_START 16
#define MLI_CORSIKA_RUNH_ENERGY_RANGE_STOP 17
#define MLI_CORSIKA_RUNH_NUM_OBSERVATION_LEVELS 4

#define MLI_CORSIKA_EVTH_EVENT_NUMBER 1
#define MLI_CORSIKA_EVTH_PARTICLE_ID 2
#define MLI_CORSIKA_EVTH_ENERGY_GEV 3
#define MLI_CORSIKA_EVTH_ZENITH_RAD 10
#define MLI_CORSIKA_EVTH_AZIMUTH_RAD 11
#define MLI_CORSIKA_EVTH_FIRST_INTERACTION_HEIGHT_CM 6

#endif



/* mli_corsika_CorsikaPhotonBunch.h */
/* Copyright 2016 Sebastian A. Mueller, Dominik Neise */
#ifndef MLI_CORSIKA_CORSIKAPHOTONBUNCH_H_
#define MLI_CORSIKA_CORSIKAPHOTONBUNCH_H_


struct mliCorsikaPhotonBunch {
        /*
         * x in cm
         * y in cm
         * cx
         * cy
         * time in nanoseconds since first interaction.
         * zem
         * photons
         * wavelength is in nanometer negative if scattered ?!
         */
        float x_cm;
        float y_cm;
        float cx_rad;
        float cy_rad;
        float time_ns;
        float z_emission_cm;
        float weight_photons;
        float wavelength_nm;
};

MLIDYNARRAY_DEFINITON(mli, CorsikaPhotonBunch, struct mliCorsikaPhotonBunch)

void mliCorsikaPhotonBunch_set_from_raw(
        struct mliCorsikaPhotonBunch *bunch,
        const float *raw);
void mliCorsikaPhotonBunch_to_raw(
        const struct mliCorsikaPhotonBunch *bunch,
        float *raw);

struct mliPhoton mliCorsikaPhotonBunch_to_merlict_photon(
        const struct mliCorsikaPhotonBunch bunch,
        const double production_distance_offset,
        const int64_t id);

struct mliVec mli_corsika_photon_direction_of_motion(
        const struct mliCorsikaPhotonBunch bunch);

struct mliVec mli_corsika_photon_support_on_observation_level(
        const struct mliCorsikaPhotonBunch bunch);

double mli_corsika_photon_wavelength(const struct mliCorsikaPhotonBunch bunch);

double mli_corsika_photon_emission_height(
        const struct mliCorsikaPhotonBunch bunch);

double mli_corsika_photon_relative_arrival_time_on_observation_level(
        const struct mliCorsikaPhotonBunch bunch);

#endif



/* mli_corsika_EventTape.h */
/* Copyright 2020 Sebastian A. Mueller */
#ifndef MLI_CORSIKA_EVENTTAPE_H_
#define MLI_CORSIKA_EVENTTAPE_H_


#define MLI_CORSIKA_EVENTTAPE_VERSION_MAYOR 0
#define MLI_CORSIKA_EVENTTAPE_VERSION_MINOR 1
#define MLI_CORSIKA_EVENTTAPE_VERSION_PATCH 0

struct mliEventTapeWriter {
        struct mliTar tar;
        int event_number;
        int cherenkov_bunch_block_number;
        struct mliDynCorsikaPhotonBunch buffer;
};
struct mliEventTapeWriter mliEventTapeWriter_init(void);
int mliEventTapeWriter_open(
        struct mliEventTapeWriter *tio,
        const char *path,
        const uint64_t num_bunches_buffer);
int mliEventTapeWriter_close(struct mliEventTapeWriter *tio);
int mliEventTapeWriter_write_runh(
        struct mliEventTapeWriter *tio,
        const float *runh);
int mliEventTapeWriter_write_evth(
        struct mliEventTapeWriter *tio,
        const float *evth);
int mliEventTapeWriter_write_cherenkov_bunch(
        struct mliEventTapeWriter *tio,
        const struct mliCorsikaPhotonBunch *bunch);
int mliEventTapeWriter_write_cherenkov_bunch_raw(
        struct mliEventTapeWriter *tio,
        const float *bunch_raw);
int mliEventTapeWriter_flush_cherenkov_bunch_block(
        struct mliEventTapeWriter *tio);
int mliEventTapeWriter_write_readme(struct mliEventTapeWriter *tio);

struct mliEventTapeReader {
        /* Current event-number */
        uint64_t event_number;

        /* Current cherenkov-block-number inside the current event */
        uint64_t cherenkov_bunch_block_number;

        /* Current bunch-number inside the current cherenkov-block */
        uint64_t block_at;
        uint64_t block_size;

        /* Underlying tape-archive */
        struct mliTar tar;

        /* Next file's tar-header in the underlying tape-archive */
        int has_tarh;
        struct mliTarHeader tarh;
};
struct mliEventTapeReader mliEventTapeReader_init(void);
int mliEventTapeReader_open(struct mliEventTapeReader *tio, const char *path);
int mliEventTapeReader_close(struct mliEventTapeReader *tio);
int mliEventTapeReader_read_runh(struct mliEventTapeReader *tio, float *runh);
int mliEventTapeReader_read_evth(struct mliEventTapeReader *tio, float *evth);
int mliEventTapeReader_read_cherenkov_bunch(
        struct mliEventTapeReader *tio,
        struct mliCorsikaPhotonBunch *bunch);
int mliEventTapeReader_read_cherenkov_bunch_raw(
        struct mliEventTapeReader *tio,
        float *bunch_raw);

int mliEventTapeReader_tarh_is_valid_cherenkov_block(
        const struct mliEventTapeReader *tio);
int mliEventTapeReader_tarh_might_be_valid_cherenkov_block(
        const struct mliEventTapeReader *tio);
int mliEventTapeReader_read_readme_until_runh(struct mliEventTapeReader *tio);

#endif



/* mli_version.c */
/* Copyright 2018-2020 Sebastian Achim Mueller */

void mli_logo_fprint(FILE *f)
{
        fprintf(f,
                "\n  "
                "                                        _/  _/              "
                "_/\n  "
                "   _/_/_/  _/_/      _/_/    _/  _/_/  _/        _/_/_/  "
                "_/_/_/_/\n  "
                "  _/    _/    _/  _/_/_/_/  _/_/      _/  _/  _/          "
                "_/\n  "
                " _/    _/    _/  _/        _/        _/  _/  _/          _/\n "
                " "
                "_/    _/    _/    _/_/_/  _/        _/  _/    _/_/_/      "
                "_/_/\n  "
                "\n");
}

void mli_authors_and_affiliations_fprint(FILE *f)
{
        fprintf(f,
                "  Sebastian Achim Mueller (1,2*,3^)\n"
                "\n"
                "  [1] Max-Planck-Institute for Nuclear Physics, \n"
                "      Saupfercheckweg 1, 69117 Heidelberg, Germany\n"
                "\n"
                "  [2] Institute for Particle Physics and Astrophysics,\n"
                "      ETH-Zurich, Otto-Stern-Weg 5, 8093 Zurich, Switzerland\n"
                "\n"
                "  [3] Experimental Physics Vb, Astroparticle Physics,\n"
                "      TU-Dortmund, Otto-Hahn-Str. 4a, 44227 Dortmund, "
                "Germany\n"
                "\n"
                "   *  (2015 - 2019)\n"
                "   ^  (2013 - 2015)\n");
}



/* mli_math.c */
/* Copyright 2018-2020 Sebastian Achim Mueller */

double mli_rad2deg(const double angle_in_rad)
{
        return 180. * angle_in_rad / MLI_PI;
}

double mli_deg2rad(const double angle_in_deg)
{
        return angle_in_deg * (1. / 180.) * MLI_PI;
}

double mli_hypot(const double a, const double b) { return sqrt(a * a + b * b); }

double mli_square(const double a) { return a * a; }

/*
 *  parameters
 *  ----------
 *      points          Sorted array in ascending order.
 *      num_points      Number of points.
 *      point_arg       The point to find the upper-bound for.
 */
uint64_t mli_upper_compare_double(
        const double *points,
        const uint64_t num_points,
        const double point_arg)
{
        uint64_t upper_index = 0;
        MLI_UPPER_COMPARE(points, num_points, point_arg, upper_index);
        return upper_index;
}

void mli_histogram(
        const double *bin_edges,
        const uint64_t num_bin_edges,
        uint64_t *underflow_bin,
        uint64_t *bins,
        uint64_t *overflow_bin,
        const double point)
{
        uint64_t idx_upper =
                mli_upper_compare_double(bin_edges, num_bin_edges, point);
        if (idx_upper == 0) {
                (*underflow_bin) += 1u;
        } else if (idx_upper == num_bin_edges) {
                (*overflow_bin) += 1u;
        } else {
                bins[idx_upper - 1] += 1u;
        }
}

void mli_linspace(
        const double start,
        const double stop,
        double *points,
        const uint64_t num_points)
{
        uint64_t i;
        const double range = stop - start;
        const double step = range / (double)(num_points - 1u);
        for (i = 0; i < num_points; i++) {
                points[i] = (double)i * step + start;
        }
}

double mli_mean(const double vals[], const uint64_t size)
{
        uint64_t i;
        double sum = 0;
        for (i = 0; i < size; i++) {
                sum = sum + vals[i];
        }
        return sum / (double)size;
}

double mli_std(const double vals[], const uint64_t size, const double vals_mean)
{
        uint64_t i;
        double s = 0.;
        for (i = 0; i < size; i++) {
                s = s + (vals[i] - vals_mean) * (vals[i] - vals_mean);
        }
        return sqrt(s / (double)size);
}

double mli_bin_center_in_linear_space(
        const double start,
        const double stop,
        const uint64_t num_bins,
        const uint64_t bin)
{
        const double width = stop - start;
        const double bin_width = width / (double)num_bins;
        return start + bin * bin_width + 0.5 * bin_width;
}

double mli_linear_interpolate_1d(
        const double weight,
        const double start,
        const double end)
{
        return start + weight * (end - start);
}

double mli_linear_interpolate_2d(
        const double xarg,
        const double x0,
        const double y0,
        const double x1,
        const double y1)
{
        /*
         *      |
         *  y1 -|            o
         *      |
         *  y0 -|    o
         *      |       xarg
         *      +----|---|---|----
         *          x0       x1
         *
         *  f(x) = m*x + b
         *  m = (y1 - y0)/(x1 - x0)
         *  y0 = m*x0 + b
         *  b = y0 - m*x0
         */
        const double m = (y1 - y0) / (x1 - x0);
        const double b = y0 - m * x0;
        return m * xarg + b;
}



/* mli_cstr.c */
/* Copyright 2018-2020 Sebastian Achim Mueller */

int mli_cstr_ends_with(const char *str, const char *sufix)
{
        uint64_t len_str, len_sufix;
        if (!str || !sufix) {
                return 0;
        }
        len_str = strlen(str);
        len_sufix = strlen(sufix);
        if (len_sufix > len_str) {
                return 0;
        }
        return strncmp(str + len_str - len_sufix, sufix, len_sufix) == 0;
}

int mli_cstr_starts_with(const char *str, const char *prefix)
{
        uint64_t len_str, len_prefix;
        if (!str || !prefix) {
                return 0;
        }
        len_str = strlen(str);
        len_prefix = strlen(prefix);
        if (len_prefix > len_str) {
                return 0;
        }
        return strncmp(str, prefix, len_prefix) == 0;
}

int mli_cstr_has_prefix_suffix(
        const char *str,
        const char *prefix,
        const char *sufix)
{
        uint64_t has_pre = 1;
        uint64_t has_suf = 1;
        if (prefix != NULL) {
                has_pre = mli_cstr_starts_with(str, prefix);
        }

        if (sufix != NULL) {
                has_suf = mli_cstr_ends_with(str, sufix);
        }

        if (has_pre == 1 && has_suf == 1) {
                return 1;
        } else {
                return 0;
        }
}

int mli_cstr_split(
        const char *str,
        const char delimiter,
        char *token,
        const uint64_t token_length)
{
        uint64_t i = 0;
        memset(token, '\0', token_length);
        for (i = 0; i < token_length; i++) {
                if (str[i] == '\0') {
                        break;
                } else if (str[i] == delimiter) {
                        break;
                } else {
                        token[i] = str[i];
                }
        }
        return i;
}

int mli_cstr_is_CRLF(const char *s)
{
        if (s[0] == '\0') {
                return 0;
        }
        if (s[1] == '\0') {
                return 0;
        }
        if (s[0] == '\r' && s[1] == '\n') {
                return 1;
        }
        return 0;
}

int mli_cstr_is_CR(const char *s)
{
        if (s[0] == '\0') {
                return 0;
        }
        if (s[0] == '\r') {
                return 1;
        }
        return 0;
}

int mli_cstr_assert_only_NUL_LF_TAB_controls(const char *str)
{
        return mli_cstr_assert_only_NUL_LF_TAB_controls_dbg(str, 1);
}

int mli_cstr_assert_only_NUL_LF_TAB_controls_dbg(const char *str, const int dbg)
{
        uint64_t pos = 0;
        while (str[pos] != '\0') {
                if (str[pos] >= 32 && str[pos] < 127) {
                        /* all fine */
                } else {
                        if (str[pos] == '\n') {
                                /* fine */
                        } else if (str[pos] == '\t') {
                                /* fine */
                        } else {
                                if (dbg) {
                                        fprintf(stderr,
                                                "Control code %u "
                                                "at column %ld in string.\n",
                                                (uint8_t)str[pos],
                                                pos);
                                }
                                return 0;
                        }
                }
                pos += 1;
        }
        return 1;
}

uint64_t mli_cstr_count_chars_up_to(
        const char *str,
        const char c,
        const uint64_t num_chars_to_scan)
{
        uint64_t i = 0;
        uint64_t count = 0u;
        while (str[i] != '\0' && i < num_chars_to_scan) {
                if (str[i] == c) {
                        count++;
                }
                i++;
        }
        return count;
}

int mli_fprint_line_match(
        FILE *f,
        const int64_t line,
        const int64_t line_number)
{
        chk(fprintf(f, "% 6d", (int32_t)line));
        if (line == line_number) {
                chk(fprintf(f, "->|  "));
        } else {
                chk(fprintf(f, "  |  "));
        }
        return 1;
error:
        return 0;
}

int mli_cstr_lines_fprint(
        FILE *f,
        const char *text,
        const uint64_t line_number,
        const uint64_t line_radius)
{
        int64_t _line_number = (int64_t)line_number;
        int64_t _line_radius = (int64_t)line_radius;
        int64_t line_start = MLI_MAX2(_line_number - _line_radius, 1);
        int64_t line_stop = line_number + line_radius;
        int64_t line = 1;
        int64_t i = 0;

        chk_msg(line_radius > 1, "Expected line_radius > 1.");

        chk(fprintf(f, "  line     text\n"));
        chk(fprintf(f, "        |\n"));

        while (text[i]) {
                int prefix = (line + 1 >= line_start) && (line < line_stop);
                int valid = (line >= line_start) && (line <= line_stop);
                if (text[i] == '\n') {
                        line++;
                }
                if (prefix && i == 0) {
                        chk(mli_fprint_line_match(f, line, _line_number));
                }
                if (valid) {
                        chk(putc(text[i], f));
                }
                if (prefix && text[i] == '\n') {
                        chk(mli_fprint_line_match(f, line, _line_number));
                }
                i++;
        }
        chk(putc('\n', f));

        return 1;
error:
        return 0;
}

void mli_cstr_path_strip_this_dir(char *dst, const char *src)
{
        const char *_src = &src[0];
        memset(dst, '\0', strlen(src));
        while (mli_cstr_starts_with(_src, "./") && _src[0] != '\0') {
                _src += 2;
        }
        strcpy(dst, _src);
}

void mli_cstr_path_basename_without_extension(const char *filename, char *key)
{
        uint64_t i = 0u;
        uint64_t o = 0u;

        while (1) {
                if (filename[i] == '\0') {
                        goto finalize;
                }
                if (filename[i] == '/') {
                        i += 1;
                        break;
                }
                i += 1;
        }

        while (1) {
                if (filename[i] == '\0') {
                        goto finalize;
                }
                if (filename[i] == '.') {
                        i += 1;
                        break;
                }
                key[o] = filename[i];
                i += 1;
                o += 1;
        }

finalize:
        key[o] = '\0';
}

void mli_cstr_strip_spaces(const char *in, char *out)
{
        uint64_t i = 0u;
        uint64_t o = 0u;
        while (in[i] && isspace(in[i])) {
                i += 1;
        }
        while (in[i] && !isspace(in[i])) {
                out[o] = in[i];
                i += 1;
                o += 1;
        }
        out[o] = '\0';
}

int mli_cstr_match_templeate(
        const char *s,
        const char *t,
        const char digit_wildcard)
{
        uint64_t i;
        if (strlen(s) != strlen(t)) {
                return 0;
        }
        for (i = 0; i < strlen(s); i++) {
                if (t[i] == digit_wildcard) {
                        if (!isdigit(s[i])) {
                                return 0;
                        }
                } else {
                        if (s[i] != t[i]) {
                                return 0;
                        }
                }
        }
        return 1;
}



/* mli_cstr_numbers.c */
/* Copyright 2018-2020 Sebastian Achim Mueller */

int mli_cstr_nto_int64(
        int64_t *out,
        const char *s,
        const uint64_t base,
        const uint64_t expected_num_chars)
{
        char *end;
        uint64_t actual_num_chars = 0u;
        int64_t l;
        chk_msg(!(s[0] == '\0' || isspace(s[0])),
                "Can not convert string to int64, bad string.");
        errno = 0;
        l = strtol(s, &end, base);
        chk_msg(errno != ERANGE,
                "Can not convert string to int64, over-, under-flow.");
        chk_msg(end != NULL, "Can not convert string to int64, bad string.");
        actual_num_chars = end - s;
        chk_msg(actual_num_chars == expected_num_chars,
                "Integer has not the expected number of chars.");
        *out = l;
        return 1;
error:
        return 0;
}

int mli_cstr_to_int64(int64_t *out, const char *s, const uint64_t base)
{
        chk_msg(mli_cstr_nto_int64(out, s, base, strlen(s)),
                "Can not convert string to int64.");
        return 1;
error:
        return 0;
}

int mli_cstr_nto_uint64(
        uint64_t *out,
        const char *s,
        const uint64_t base,
        const uint64_t expected_num_chars)
{
        int64_t tmp;
        chk(mli_cstr_nto_int64(&tmp, s, base, expected_num_chars));
        chk_msg(tmp >= 0, "Expected a positive integer.");
        (*out) = tmp;
        return 1;
error:
        return 0;
}

int mli_cstr_to_uint64(uint64_t *out, const char *s, const uint64_t base)
{
        int64_t tmp;
        chk(mli_cstr_to_int64(&tmp, s, base));
        chk_msg(tmp >= 0, "Expected a positive integer.");
        (*out) = tmp;
        return 1;
error:
        return 0;
}

int mli_cstr_nto_double(
        double *out,
        const char *s,
        const uint64_t expected_num_chars)
{
        char *end;
        uint64_t actual_num_chars = 0u;
        double l;
        chk_msg(!(s[0] == '\0' || isspace(s[0])),
                "Can not convert string to float64, bad string.");
        errno = 0;
        l = strtod(s, &end);
        chk_msg(errno != ERANGE,
                "Can not convert string to float64, over-, under-flow.");
        chk_msg(end != NULL, "Can not convert string to float64.");

        actual_num_chars = end - s;
        chk_msg(actual_num_chars == expected_num_chars,
                "float64 has not the expected number of chars.");
        *out = l;
        return 1;
error:
        return 0;
}

int mli_cstr_to_double(double *out, const char *s)
{
        chk_msg(mli_cstr_nto_double(out, s, strlen(s)),
                "Can not convert string to float64.");
        return 1;
error:
        return 0;
}

int mli_cstr_print_uint64(
        uint64_t u,
        char *s,
        const uint64_t max_num_chars,
        const uint64_t base,
        const uint64_t min_num_digits)
{
        char literals[] = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'};
        char tmp[128] = {'\0'};
        uint64_t remainder = 0u;
        uint32_t remainder32 = 0u;
        uint64_t quotient = u;
        int64_t digs = 0u;
        int64_t pos = 0;
        int64_t i = 0;
        int64_t num_leading_zeors = 0;

        chk_msg(base <= 10, "Expected base <= 10");
        chk_msg(base > 1, "Expected base > 1");
        chk_msg(max_num_chars < sizeof(tmp), "Exceeded max num. chars.");
        chk_msg(min_num_digits < max_num_chars, "Exceeded max num. chars.");

        do {
                remainder = quotient % base;
                quotient = quotient / base;
                remainder32 = (uint32_t)remainder;
                tmp[digs] = literals[remainder32];
                digs++;
                chk_msg(digs < (int64_t)sizeof(tmp),
                        "Exceeded max num. chars.");
        } while (quotient > 0u);

        num_leading_zeors = min_num_digits - digs;
        if (num_leading_zeors < 0) {
                num_leading_zeors = 0;
        }

        for (i = 0; i < num_leading_zeors; i++) {
                chk_msg(pos < (int64_t)max_num_chars,
                        "Exceeded max num. chars.");
                s[pos] = '0';
                pos++;
        }

        for (i = 0; i < digs; i++) {
                chk_msg(pos < (int64_t)max_num_chars,
                        "Exceeded max num. chars.");
                s[pos] = tmp[digs - i - 1];
                pos++;
        }

        chk_msg(pos < (int64_t)max_num_chars, "Exceeded max num. chars.");
        s[pos] = '\0';

        return 1;
error:
        return 0;
}



/* mli_quadratic_equation.c */
/* Copyright 2019 Sebastian A. Mueller */

int mli_quadratic_equation(
        const double p,
        const double q,
        double *minus_solution,
        double *plus_solution)
{
        /*
         *  y = a*x^2 + b*x + c
         *  p = b/a
         *  q = c/a
         *  x_m = -p/2 - sqrt((-p/2)^2 - q)
         *  x_p = -p/2 + sqrt((-p/2)^2 - q)
         */
        const double p_over_2 = 0.5 * p;
        const double inner_part_of_squareroot = p_over_2 * p_over_2 - q;
        double squareroot;
        if (inner_part_of_squareroot >= 0.0) {
                squareroot = sqrt(inner_part_of_squareroot);
                (*minus_solution) = -p_over_2 - squareroot;
                (*plus_solution) = -p_over_2 + squareroot;
                return 1;
        } else {
                return 0;
        }
}



/* mliVec.c */
/* Copyright 2018-2020 Sebastian Achim Mueller */

struct mliVec mliVec_set(const double x, const double y, const double z)
{
        struct mliVec out;
        out.x = x;
        out.y = y;
        out.z = z;
        return out;
}

struct mliVec mliVec_add(const struct mliVec a, const struct mliVec b)
{
        struct mliVec out;
        out.x = a.x + b.x;
        out.y = a.y + b.y;
        out.z = a.z + b.z;
        return out;
}

struct mliVec mliVec_substract(const struct mliVec a, const struct mliVec b)
{
        struct mliVec out;
        out.x = a.x - b.x;
        out.y = a.y - b.y;
        out.z = a.z - b.z;
        return out;
}

struct mliVec mliVec_cross(const struct mliVec a, const struct mliVec b)
{
        struct mliVec out;
        out.x = (a.y * b.z - a.z * b.y);
        out.y = (a.z * b.x - a.x * b.z);
        out.z = (a.x * b.y - a.y * b.x);
        return out;
}

double mliVec_dot(const struct mliVec a, const struct mliVec b)
{
        return a.x * b.x + a.y * b.y + a.z * b.z;
}

struct mliVec mliVec_multiply(const struct mliVec v, const double a)
{
        struct mliVec out;
        out.x = v.x * a;
        out.y = v.y * a;
        out.z = v.z * a;
        return out;
}

double mliVec_norm(const struct mliVec a) { return sqrt(mliVec_dot(a, a)); }

struct mliVec mliVec_normalized(struct mliVec a)
{
        return mliVec_multiply(a, 1. / mliVec_norm(a));
}

double mliVec_angle_between(const struct mliVec a, const struct mliVec b)
{
        struct mliVec a_normalized = mliVec_multiply(a, 1. / mliVec_norm(a));
        struct mliVec b_normalized = mliVec_multiply(b, 1. / mliVec_norm(b));
        return acos(mliVec_dot(a_normalized, b_normalized));
}

double mliVec_norm_between(const struct mliVec a, const struct mliVec b)
{
        return mliVec_norm(mliVec_substract(a, b));
}

struct mliVec mliVec_mirror(const struct mliVec in, const struct mliVec normal)
{
        /*
         *      This is taken from
         *      (OPTI 421/521 – Introductory Optomechanical Engineering)
         *      J.H. Bruge
         *      University of Arizona
         *
         *                     k1    n     k2
         *                      \    /\   /
         *                       \   |   /
         *                        \  |  /
         *                         \ | /
         *      ____________________\|/______________________
         *      mirror-surface
         *
         *      k1: incidate ray
         *      k2: reflected ray
         *      n:  surface normal
         *
         *      n = [nx,ny,nz]^T
         *
         *      It can be written:
         *
         *      k2 = M*k1
         *
         *      M = EYE - 2*n*n^T
         *
         *      using EYE =  [1 0 0]
         *                   [0 1 0]
         *                   [0 0 1]
         */
        struct mliVec out;
        out.x = (1. - 2. * normal.x * normal.x) * in.x +
                -2. * normal.x * normal.y * in.y +
                -2. * normal.x * normal.z * in.z;

        out.y = -2. * normal.x * normal.y * in.x +
                (1. - 2. * normal.y * normal.y) * in.y +
                -2. * normal.y * normal.z * in.z;

        out.z = -2. * normal.x * normal.z * in.x +
                -2. * normal.y * normal.z * in.y +
                (1. - 2. * normal.z * normal.z) * in.z;
        return out;
}

int mliVec_equal_margin(
        const struct mliVec a,
        const struct mliVec b,
        const double distance_margin)
{
        struct mliVec diff;
        double distance_squared;
        diff = mliVec_substract(a, b);
        distance_squared = mliVec_dot(diff, diff);
        return distance_squared <= distance_margin * distance_margin;
}

int mliVec_equal(const struct mliVec a, const struct mliVec b)
{
        if (fabs(a.x - b.x) > DBL_EPSILON)
                return 0;
        if (fabs(a.y - b.y) > DBL_EPSILON)
                return 0;
        if (fabs(a.z - b.z) > DBL_EPSILON)
                return 0;
        return 1;
}

uint32_t mliVec_octant(const struct mliVec a)
{
        /*
         *  encodes the octant sectors where the vector is pointing to
         *      x y z sector
         *      - - -   0
         *      - - +   1
         *      - + -   2
         *      - + +   3
         *      + - -   4
         *      + - +   5
         *      + + -   6
         *      + + +   7
         */
        const uint32_t sx = a.x >= 0.;
        const uint32_t sy = a.y >= 0.;
        const uint32_t sz = a.z >= 0.;
        return 4 * sx + 2 * sy + 1 * sz;
}

int mliVec_sign3_bitmask(const struct mliVec a, const double epsilon)
{
        /* bits: 7  6  5  4  3  2  1  0  */
        /*             xp yp zp xn yn zn */

        const int xn = a.x < epsilon ? 4 : 0;   /* 2**2 */
        const int xp = a.x > -epsilon ? 32 : 0; /* 2**5 */

        const int yn = a.y < epsilon ? 2 : 0;   /* 2**1 */
        const int yp = a.y > -epsilon ? 16 : 0; /* 2**4 */

        const int zn = a.z < epsilon ? 1 : 0;  /* 2**0 */
        const int zp = a.z > -epsilon ? 8 : 0; /* 2**3 */

        return (xn | xp | yn | yp | zn | zp);
}



/* mliRay.c */
/* Copyright 2018-2020 Sebastian Achim Mueller */

struct mliRay mliRay_set(
        const struct mliVec support,
        const struct mliVec direction)
{
        struct mliRay ray;
        ray.support = support;
        ray.direction = mliVec_multiply(direction, 1. / mliVec_norm(direction));
        return ray;
}

struct mliVec mliRay_at(const struct mliRay *ray, const double t)
{
        struct mliVec out;
        out.x = ray->support.x + t * ray->direction.x;
        out.y = ray->support.y + t * ray->direction.y;
        out.z = ray->support.z + t * ray->direction.z;
        return out;
}

int mliRay_sphere_intersection(
        const struct mliVec support,
        const struct mliVec direction,
        const double radius,
        double *minus_solution,
        double *plus_solution)
{
        const double sup_times_dir = mliVec_dot(support, direction);
        const double dir_times_dir = mliVec_dot(direction, direction);
        const double sup_times_sup = mliVec_dot(support, support);
        const double radius_square = radius * radius;

        const double p = 2.0 * (sup_times_dir / dir_times_dir);
        const double q = sup_times_sup / dir_times_dir - radius_square;

        return mli_quadratic_equation(p, q, minus_solution, plus_solution);
}



/* mliPhoton.c */
/* Copyright 2018-2020 Sebastian Achim Mueller */



/* mliTar.c */
/**
 * Copyright (c) 2017 rxi
 * Copyright (c) 2019 Sebastian A. Mueller
 *                    Max-Planck-Institute for nuclear-physics, Heidelberg
 */


struct mliTarRawHeader {
        char name[MLI_TAR_NAME_LENGTH];
        char mode[8];
        char owner[8];
        char group[8];
        char size[12];
        char mtime[12];
        char checksum[8];
        char type;
        char linkname[MLI_TAR_NAME_LENGTH];
        char _padding[255];
};

struct mliTar mliTar_init(void)
{
        struct mliTar out;
        out.stream = NULL;
        out.pos = 0u;
        out.remaining_data = 0u;
        return out;
}

struct mliTarHeader mliTarHeader_init(void)
{
        struct mliTarHeader h;
        h.mode = 0;
        h.owner = 0;
        h.size = 0;
        h.mtime = 0;
        h.type = 0;
        memset(h.name, '\0', sizeof(h.name));
        memset(h.linkname, '\0', sizeof(h.linkname));
        return h;
}

int mliTarHeader_set_normal_file(
        struct mliTarHeader *h,
        const char *name,
        const uint64_t size)
{
        (*h) = mliTarHeader_init();
        chk_msg(strlen(name) < sizeof(h->name), "Filename is too long.");
        memcpy(h->name, name, strlen(name));
        h->size = size;
        h->type = MLI_TAR_NORMAL_FILE;
        h->mode = 0664;
        return 1;
error:
        return 0;
}

int mliTarHeader_set_directory(struct mliTarHeader *h, const char *name)
{
        (*h) = mliTarHeader_init();
        chk_msg(strlen(name) < sizeof(h->name), "Dirname is too long.");
        memcpy(h->name, name, strlen(name));
        h->type = MLI_TAR_DIRECTORY;
        h->mode = 0775;
        return 1;
error:
        return 0;
}

/* write */

int mliTar_twrite(struct mliTar *tar, const void *data, const uint64_t size)
{
        int64_t res = fwrite(data, 1, size, tar->stream);
        chk_msg(res >= 0, "Failed writing to tar.");
        chk_msg((uint64_t)res == size, "Failed writing to tar.");
        tar->pos += size;
        return 1;
error:
        return 0;
}

/* read */

int mliTar_tread(struct mliTar *tar, void *data, const uint64_t size)
{
        int64_t res = fread(data, 1, size, tar->stream);
        chk_msg(res >= 0, "Failed reading from tar.");
        chk_msg((uint64_t)res == size, "Failed reading from tar.");
        tar->pos += size;
        return 1;
error:
        return 0;
}

/* close */

int mliTar_close(struct mliTar *tar)
{
        fclose(tar->stream);
        (*tar) = mliTar_init();
        return 1;
}

uint64_t mliTar_round_up(uint64_t n, uint64_t incr)
{
        return n + (incr - n % incr) % incr;
}

uint64_t mliTar_checksum(const struct mliTarRawHeader *rh)
{
        uint64_t i;
        unsigned char *p = (unsigned char *)rh;
        uint64_t res = 256;
        for (i = 0; i < offsetof(struct mliTarRawHeader, checksum); i++) {
                res += p[i];
        }
        for (i = offsetof(struct mliTarRawHeader, type); i < sizeof(*rh); i++) {
                res += p[i];
        }
        return res;
}

int mliTar_write_null_bytes(struct mliTar *tar, uint64_t n)
{
        uint64_t i;
        char nul = '\0';
        for (i = 0; i < n; i++) {
                chk_msg(mliTar_twrite(tar, &nul, 1), "Failed to write nulls");
        }
        return 1;
error:
        return 0;
}

int mliTar_field_to_uint(
        uint64_t *out,
        const char *field,
        const uint64_t field_size)
{
        char buff[MLI_TAR_NAME_LENGTH] = {'\0'};
        chk(field_size < MLI_TAR_NAME_LENGTH);
        memcpy(buff, field, field_size);

        /* Take care of historic 'space' (32 decimal) termination */
        /* Convert all 'space' terminations to '\0' terminations. */

        if (buff[field_size - 1] == 32) {
                buff[field_size - 1] = 0;
        }
        if (buff[field_size - 2] == 32) {
                buff[field_size - 2] = 0;
        }

        chk(mli_cstr_to_uint64(out, buff, MLI_TAR_OCTAL));
        return 1;
error:
        return 0;
}

int mliTar_raw_to_header(
        struct mliTarHeader *h,
        const struct mliTarRawHeader *rh)
{
        uint64_t chksum_actual, chksum_expected;
        chksum_actual = mliTar_checksum(rh);

        /* Build and compare checksum */
        chk_msg(mliTar_field_to_uint(
                        &chksum_expected, rh->checksum, sizeof(rh->checksum)),
                "bad checksum string.");
        chk_msg(chksum_actual == chksum_expected, "bad checksum.");

        /* Load raw header into header */
        chk_msg(mliTar_field_to_uint(&h->mode, rh->mode, sizeof(rh->mode)),
                "bad mode");
        chk_msg(mliTar_field_to_uint(&h->owner, rh->owner, sizeof(rh->owner)),
                "bad owner");
        if (rh->size[0] == -128) {
                chk_msg(mliTar_field12_to_uint64_2001star_base256(
                                rh->size, &h->size),
                        "bad size, mode: base-256");
        } else {
                chk_msg(mliTar_field_to_uint(
                                &h->size, rh->size, sizeof(rh->size)),
                        "bad size, mode: base-octal");
        }
        chk_msg(mliTar_field_to_uint(&h->mtime, rh->mtime, sizeof(rh->mtime)),
                "bad mtime");
        h->type = rh->type;
        memcpy(h->name, rh->name, sizeof(h->name));
        memcpy(h->linkname, rh->linkname, sizeof(h->linkname));

        return 1;
error:
        return 0;
}

int mliTar_uint_to_field(
        const uint64_t val,
        char *field,
        const uint64_t fieldsize)
{
        chk(mli_cstr_print_uint64(
                val, field, fieldsize, MLI_TAR_OCTAL, fieldsize - 1));
        return 1;
error:
        return 0;
}

int mliTar_uint64_to_field12_2001star_base256(uint64_t val, char *field)
{
        uint8_t tmp[12];
        int64_t i = 0;
        for (i = 11; i > 0; i--) {
                tmp[i] = (uint8_t)(val % 256u);
                val = val / 256u;
        }

        chk_msg(val == 0u, "Expected value to be less than 256**11.");
        /* set highest bit in leftmost byte to 1 */
        tmp[0] = (uint8_t)128u;

        memcpy(field, tmp, 12);
        return 1;
error:
        return 0;
}

int mliTar_field12_to_uint64_2001star_base256(const char *field, uint64_t *val)
{
        uint8_t tmp[12];
        uint64_t i = 0u;
        const uint64_t powers[] = {
                0x100000000000000,
                0x1000000000000,
                0x10000000000,
                0x100000000,
                0x1000000,
                0x10000,
                0x100,
                0x1,
        };

        memcpy(tmp, field, 12);
        chk_msg(tmp[0] == 128u,
                "Expected field[0] == 128, indicating 256-base, 2001star.");
        chk_msg(tmp[1] == 0u,
                "Expected field[1] == 0, 256**10 exceeds uint64.");
        chk_msg(tmp[2] == 0u,
                "Expected field[2] == 0, 256**09 exceeds uint64.");
        chk_msg(tmp[3] == 0u,
                "Expected field[3] == 0, 256**08 exceeds uint64.");

        (*val) = 0u;
        for (i = 4; i < 12; i++) {
                (*val) = (*val) + powers[i - 4] * (uint64_t)tmp[i];
        }
        return 1;
error:
        return 0;
}

int mliTar_make_raw_header(
        struct mliTarRawHeader *rh,
        const struct mliTarHeader *h)
{
        uint64_t chksum;

        /* Load header into raw header */
        memset(rh, 0, sizeof(*rh));
        chk_msg(mliTar_uint_to_field(h->mode, rh->mode, sizeof(rh->mode)),
                "bad mode");
        chk_msg(mliTar_uint_to_field(h->owner, rh->owner, sizeof(rh->owner)),
                "bad owner");
        if (h->size >= MLI_TAR_MAX_FILESIZE_OCTAL) {
                chk_msg(mliTar_uint64_to_field12_2001star_base256(
                                h->size, rh->size),
                        "bad size, mode: base-256");
        } else {
                chk_msg(mliTar_uint_to_field(
                                h->size, rh->size, sizeof(rh->size)),
                        "bad size, mode: base-octal");
        }
        chk_msg(mliTar_uint_to_field(h->mtime, rh->mtime, sizeof(rh->mtime)),
                "bad mtime");
        rh->type = h->type ? h->type : MLI_TAR_NORMAL_FILE;
        memcpy(rh->name, h->name, sizeof(rh->name));
        memcpy(rh->linkname, h->linkname, sizeof(rh->linkname));

        /* Calculate and write checksum */
        chksum = mliTar_checksum(rh);
        chk_msg(mli_cstr_print_uint64(
                        chksum,
                        rh->checksum,
                        sizeof(rh->checksum),
                        MLI_TAR_OCTAL,
                        sizeof(rh->checksum) - 2),
                "bad checksum");

        rh->checksum[sizeof(rh->checksum) - 1] = 32;

        chk_msg(rh->checksum[sizeof(rh->checksum) - 2] == 0,
                "Second last char in checksum must be '\\0', i.e. 0(decimal).");
        chk_msg(rh->checksum[sizeof(rh->checksum) - 1] == 32,
                "Last char in checksum must be ' ', i.e. 32(decimal).");

        return 1;
error:
        return 0;
}

int mliTar_open(struct mliTar *tar, const char *filename, const char *mode)
{
        *tar = mliTar_init();

        /* Assure mode is always binary */
        if (strchr(mode, 'r'))
                mode = "rb";
        if (strchr(mode, 'w'))
                mode = "wb";
        if (strchr(mode, 'a'))
                mode = "ab";

        tar->stream = fopen(filename, mode);
        chk_msg(tar->stream, "Failed to open tar-file.");

        return 1;
error:
        return 0;
}

int mliTar_raw_header_is_null(const struct mliTarRawHeader *rh)
{
        uint64_t i = 0u;
        unsigned char *p = (unsigned char *)rh;
        for (i = 0; i < sizeof(struct mliTarRawHeader); i++) {
                if (p[i] != '\0') {
                        return 0;
                }
        }
        return 1;
}

int mliTar_read_header(struct mliTar *tar, struct mliTarHeader *h)
{
        struct mliTarRawHeader rh;

        chk_msg(mliTar_tread(tar, &rh, sizeof(rh)),
                "Failed to read raw header");

        if (mliTar_raw_header_is_null(&rh)) {
                return 0;
        }

        chk_msg(mliTar_raw_to_header(h, &rh), "Failed to parse raw header.");
        tar->remaining_data = h->size;
        return 1;
error:
        return 0;
}

int mliTar_read_data(struct mliTar *tar, void *ptr, uint64_t size)
{
        chk_msg(tar->remaining_data >= size,
                "Expect size to be read >= remaining_data");
        chk_msg(mliTar_tread(tar, ptr, size), "Failed to read payload-data.");
        tar->remaining_data -= size;

        if (tar->remaining_data == 0) {
                uint64_t i;
                const uint64_t next_record = mliTar_round_up(tar->pos, 512);
                const uint64_t padding_size = next_record - tar->pos;
                char padding;

                for (i = 0; i < padding_size; i++) {
                        chk_msg(mliTar_tread(tar, &padding, 1),
                                "Failed to read padding-block "
                                "to reach next record.");
                }
        }

        return 1;
error:
        return 0;
}

int mliTar_write_header(struct mliTar *tar, const struct mliTarHeader *h)
{
        struct mliTarRawHeader rh;
        chk_msg(mliTar_make_raw_header(&rh, h), "Failed to make raw-header");
        tar->remaining_data = h->size;
        chk_msg(mliTar_twrite(tar, &rh, sizeof(rh)), "Failed to write header.");
        return 1;
error:
        return 0;
}

int mliTar_write_data(struct mliTar *tar, const void *data, uint64_t size)
{
        chk_msg(tar->remaining_data >= size,
                "Expect tar->remaining_data >= size to be written.");
        chk_msg(mliTar_twrite(tar, data, size),
                "Failed to write payload-data.");
        tar->remaining_data -= size;

        if (tar->remaining_data == 0) {
                const uint64_t next_record = mliTar_round_up(tar->pos, 512);
                const uint64_t padding_size = next_record - tar->pos;
                chk_msg(mliTar_write_null_bytes(tar, padding_size),
                        "Failed to write padding zeros.");
        }
        return 1;
error:
        return 0;
}

int mliTar_finalize(struct mliTar *tar)
{
        chk_msg(mliTar_write_null_bytes(
                        tar, sizeof(struct mliTarRawHeader) * 2),
                "Failed to write two final null records.");
        return 1;
error:
        return 0;
}



/* mliDynArray.c */
/* Copyright 2018-2020 Sebastian Achim Mueller */



/* mli_corsika_utils.c */
/* Copyright 2020 Sebastian A. Mueller*/

float mli_4chars_to_float(const char *four_char_word)
{
        float f;
        assert(strlen(four_char_word) == 4);
        memcpy(&f, four_char_word, sizeof(float));
        return f;
}



/* mli_corsika_CorsikaPhotonBunch.c */
/* Copyright 2016 Sebastian A. Mueller */

MLIDYNARRAY_IMPLEMENTATION(
        mli,
        CorsikaPhotonBunch,
        struct mliCorsikaPhotonBunch)

void mliCorsikaPhotonBunch_set_from_raw(
        struct mliCorsikaPhotonBunch *bunch,
        const float *raw)
{
        bunch->x_cm = raw[0];
        bunch->y_cm = raw[1];
        bunch->cx_rad = raw[2];
        bunch->cy_rad = raw[3];
        bunch->time_ns = raw[4];
        bunch->z_emission_cm = raw[5];
        bunch->weight_photons = raw[6];
        bunch->wavelength_nm = raw[7];
}

void mliCorsikaPhotonBunch_to_raw(
        const struct mliCorsikaPhotonBunch *bunch,
        float *raw)
{
        raw[0] = bunch->x_cm;
        raw[1] = bunch->y_cm;
        raw[2] = bunch->cx_rad;
        raw[3] = bunch->cy_rad;
        raw[4] = bunch->time_ns;
        raw[5] = bunch->z_emission_cm;
        raw[6] = bunch->weight_photons;
        raw[7] = bunch->wavelength_nm;
}

struct mliPhoton mliCorsikaPhotonBunch_to_merlict_photon(
        const struct mliCorsikaPhotonBunch bunch,
        const double production_distance_offset,
        const int64_t id)
{
        /*
        Returns an mliPhoton that will reach the observation-level in
        the same way as the corsika-photon-bunch. The weight of the
        corsika-photon-bunch is not taken into account here.

        Parameters
        ----------
        bunch :
                The corsika-photon-bunch
        production_distance_offset : double
                An arbitrary distance for the photon to travel until they
                reach the observation-level. If 0.0, the distance for a
                merlict photon is only defined by the relative arrival time
                on the observation-level.
                Ensure this offset is at least as big as your detector system
                so that photons do not start inside your detector.
        id : int64
                The photon's id.
        */

        const double VACUUM_SPPED_OF_LIGHT = 299792458.0;
        const struct mliVec photon_direction_of_motion =
                mli_corsika_photon_direction_of_motion(bunch);

        const struct mliRay ray_running_upwards_to_production = mliRay_set(
                mli_corsika_photon_support_on_observation_level(bunch),
                mliVec_multiply(photon_direction_of_motion, -1.0));

        const double offset =
                (production_distance_offset +
                 VACUUM_SPPED_OF_LIGHT *
                         mli_corsika_photon_relative_arrival_time_on_observation_level(
                                 bunch));

        const struct mliVec photon_emission_position =
                mliRay_at(&ray_running_upwards_to_production, offset);

        struct mliPhoton photon;
        photon.ray.support = photon_emission_position;
        photon.ray.direction = photon_direction_of_motion;
        photon.wavelength = mli_corsika_photon_wavelength(bunch);
        photon.id = id;
        return photon;
}

struct mliVec mli_corsika_photon_direction_of_motion(
        const struct mliCorsikaPhotonBunch bunch)
{ /*
       KIT-CORSIKA coordinate-system

                         /\ z-axis
                         |
                         |\ p
                         | \ a
                         |  \ r
                         |   \ t
                         |    \ i
                         |     \ c
                         |      \ l
                         |       \ e
                         |        \
                         |  theta  \ m
                         |       ___\ o
                         |___----    \ m      ___
                         |            \ e       /| y-axis (west)
                         |             \ n    /
                         |              \ t /
                         |               \/u
                         |              / \ m
                         |            /    \
                         |          /       \
                         |        /__________\
                         |      /      ___---/
                         |    /   __---    /
                         |  /__--- phi \ /
         ________________|/--__________/______\ x-axis (north)
                        /|                    /
                      /  |
                    /    |
                  /


          Extensive Air Shower Simulation with CORSIKA, Figure 1, page 114
          (Version 7.6400 from December 27, 2017)

          Direction-cosines:

          cx = sin(theta) * cos(phi)
          cy = sin(theta) * sin(phi)

          The zenith-angle theta opens relative to the negative z-axis.

          It is the momentum of the Cherenkov-photon, which is pointing
          down towards the observation-plane.
  */
        const double cz_rad =
                sqrt(1.0 - bunch.cx_rad * bunch.cx_rad -
                     bunch.cy_rad * bunch.cy_rad);
        return mliVec_set(bunch.cx_rad, bunch.cy_rad, -cz_rad);
}

struct mliVec mli_corsika_photon_support_on_observation_level(
        const struct mliCorsikaPhotonBunch bunch)
{
        return mliVec_set(
                (double)bunch.x_cm * 1e-2, (double)bunch.y_cm * 1e-2, 0.0);
}

double mli_corsika_photon_wavelength(const struct mliCorsikaPhotonBunch bunch)
{
        return fabs((double)bunch.wavelength_nm * 1e-9);
}

double mli_corsika_photon_emission_height(
        const struct mliCorsikaPhotonBunch bunch)
{
        return (double)bunch.z_emission_cm * 1e-2;
}

double mli_corsika_photon_relative_arrival_time_on_observation_level(
        const struct mliCorsikaPhotonBunch bunch)
{
        return (double)bunch.time_ns * 1e-9;
}



/* mli_corsika_EventTape.c */
/* Copyright 2020 Sebastian A. Mueller */

/* writer */
/* ====== */
struct mliEventTapeWriter mliEventTapeWriter_init(void)
{
        struct mliEventTapeWriter tio;
        tio.tar = mliTar_init();
        tio.event_number = 0;
        tio.cherenkov_bunch_block_number = 1;
        tio.buffer = mliDynCorsikaPhotonBunch_init();
        return tio;
}

int mliEventTapeWriter_close(struct mliEventTapeWriter *tio)
{
        if (tio->tar.stream) {
                if (tio->event_number) {
                        chk_msg(mliEventTapeWriter_flush_cherenkov_bunch_block(
                                        tio),
                                "Can't finalize final event's "
                                "cherenkov-bunch-block");
                }
                chk_msg(mliTar_finalize(&tio->tar), "Can't finalize tar-file.");
                chk_msg(mliTar_close(&tio->tar), "Can't close tar-file.");
        }
        mliDynCorsikaPhotonBunch_free(&tio->buffer);
        (*tio) = mliEventTapeWriter_init();
        return 1;
error:
        return 0;
}

int mliEventTapeWriter_open(
        struct mliEventTapeWriter *tio,
        const char *path,
        const uint64_t num_bunches_buffer)
{
        chk_msg(mliEventTapeWriter_close(tio),
                "Can't close and free previous tar-io-writer.");
        chk_msg(mliTar_open(&tio->tar, path, "w"), "Can't open tar.");
        chk_msg(mliDynCorsikaPhotonBunch_malloc(
                        &tio->buffer, num_bunches_buffer),
                "Can't malloc cherenkov-bunch-buffer.");
        chk_msg(mliEventTapeWriter_write_readme(tio), "Can't write info.")

                return 1;
error:
        return 0;
}

int mliEventTapeWriter_write_readme(struct mliEventTapeWriter *tio)
{
        struct mliTarHeader tarh = mliTarHeader_init();
        char vers[1024];
        uint64_t p = 0;
        p += sprintf(vers + p, "MLI_VERSION_MAYOR %d\n", MLI_VERSION_MAYOR);
        p += sprintf(vers + p, "MLI_VERSION_MINOR %d\n", MLI_VERSION_MINOR);
        p += sprintf(vers + p, "MLI_VERSION_PATCH %d\n", MLI_VERSION_PATCH);
        p +=
                sprintf(vers + p,
                        "MLI_CORSIKA_VERSION_MAYOR %d\n",
                        MLI_CORSIKA_VERSION_MAYOR);
        p +=
                sprintf(vers + p,
                        "MLI_CORSIKA_VERSION_MINOR %d\n",
                        MLI_CORSIKA_VERSION_MINOR);
        p +=
                sprintf(vers + p,
                        "MLI_CORSIKA_VERSION_PATCH %d\n",
                        MLI_CORSIKA_VERSION_PATCH);
        p +=
                sprintf(vers + p,
                        "MLI_CORSIKA_EVENTTAPE_VERSION_MAYOR %d\n",
                        MLI_CORSIKA_EVENTTAPE_VERSION_MAYOR);
        p +=
                sprintf(vers + p,
                        "MLI_CORSIKA_EVENTTAPE_VERSION_MINOR %d\n",
                        MLI_CORSIKA_EVENTTAPE_VERSION_MINOR);
        p +=
                sprintf(vers + p,
                        "MLI_CORSIKA_EVENTTAPE_VERSION_PATCH %d\n",
                        MLI_CORSIKA_EVENTTAPE_VERSION_PATCH);
        chk_msg(p < sizeof(vers), "Info string is too long.");

        chk_msg(mliTarHeader_set_normal_file(&tarh, "readme/version.txt", p),
                "Can't set tar-header for 'readme/version.txt'.");
        chk_msg(mliTar_write_header(&tio->tar, &tarh),
                "Can't write tar-header for 'readme/version.txt' to tar.");
        chk_msg(mliTar_write_data(&tio->tar, vers, p),
                "Can't write data of 'readme/version.txt' to tar.");

        return 1;
error:
        return 0;
}

int mliEventTapeWriter_write_corsika_header(
        struct mliEventTapeWriter *tio,
        const char *path,
        const float *corsika_header)
{
        struct mliTarHeader tarh = mliTarHeader_init();
        chk_msg(mliTarHeader_set_normal_file(
                        &tarh, path, MLI_CORSIKA_HEADER_SIZE),
                "Can't set tar-header for corsika-header.");

        chk_msg(mliTar_write_header(&tio->tar, &tarh),
                "Can't write tar-header for corsika-header to tar.");

        chk_msg(mliTar_write_data(
                        &tio->tar, corsika_header, MLI_CORSIKA_HEADER_SIZE),
                "Can't write data of corsika-header to tar.");
        return 1;
error:
        return 0;
}

int mliEventTapeWriter_write_runh(
        struct mliEventTapeWriter *tio,
        const float *runh)
{
        chk_msg(mliEventTapeWriter_write_corsika_header(
                        tio, "RUNH.float32", runh),
                "Can't write 'RUNH.float32' to tario.");
        return 1;
error:
        return 0;
}

int mliEventTapeWriter_write_evth(
        struct mliEventTapeWriter *tio,
        const float *evth)
{
        char path[MLI_TAR_NAME_LENGTH] = {'\0'};

        /* finalize previous event */

        if (tio->event_number) {
                chk_msg(mliEventTapeWriter_flush_cherenkov_bunch_block(tio),
                        "Can't finalize previous event's "
                        "cherenkov-bunch-block");
        }
        tio->event_number = (int)(MLI_ROUND(evth[1]));
        chk_msg(tio->event_number > 0, "Expected event_number > 0.");

        tio->cherenkov_bunch_block_number = 1;

        sprintf(path, "events/%09d/EVTH.float32", tio->event_number);
        chk_msg(mliEventTapeWriter_write_corsika_header(tio, path, evth),
                "Can't write 'EVTH.float32' to tario.");
        return 1;
error:
        return 0;
}

int mliEventTapeWriter_flush_cherenkov_bunch_block(
        struct mliEventTapeWriter *tio)
{
        char path[MLI_TAR_NAME_LENGTH] = {'\0'};
        struct mliTarHeader tarh = mliTarHeader_init();
        float bunch_raw[8] = {0.0};
        uint64_t i = 0;

        sprintf(path,
                "events/%09d/cherenkov_bunches/%09d.x8.float32",
                tio->event_number,
                tio->cherenkov_bunch_block_number);

        chk_msg(mliTarHeader_set_normal_file(
                        &tarh, path, tio->buffer.size * MLI_CORSIKA_BUNCH_SIZE),
                "Can't set cherenkov-bunch-block's tar-header.");

        chk_msg(mliTar_write_header(&tio->tar, &tarh),
                "Can't write tar-header for cherenkov-bunch-block to tar.");

        for (i = 0; i < tio->buffer.size; i++) {
                mliCorsikaPhotonBunch_to_raw(&tio->buffer.array[i], bunch_raw);
                chk_msg(mliTar_write_data(
                                &tio->tar, bunch_raw, MLI_CORSIKA_BUNCH_SIZE),
                        "Can't write cherenkov-bunch-block to tar-file.");
        }

        tio->buffer.size = 0;

        tio->cherenkov_bunch_block_number += 1;
        return 1;
error:
        return 0;
}

int mliEventTapeWriter_write_cherenkov_bunch(
        struct mliEventTapeWriter *tio,
        const struct mliCorsikaPhotonBunch *bunch)
{
        if (tio->buffer.size == tio->buffer.capacity) {
                chk_msg(mliEventTapeWriter_flush_cherenkov_bunch_block(tio),
                        "Can't finalize cherenkov-bunch-block.");
                chk_msg(tio->buffer.size == 0, "Expected buffer to be empty.");
        }
        tio->buffer.array[tio->buffer.size] = (*bunch);
        tio->buffer.size += 1;
        return 1;
error:
        return 0;
}

int mliEventTapeWriter_write_cherenkov_bunch_raw(
        struct mliEventTapeWriter *tio,
        const float *bunch_raw)
{
        struct mliCorsikaPhotonBunch bunch;
        mliCorsikaPhotonBunch_set_from_raw(&bunch, bunch_raw);
        chk_msg(mliEventTapeWriter_write_cherenkov_bunch(tio, &bunch),
                "Can't add raw-bunch to tar-io.");
        return 1;
error:
        return 0;
}

/* reader */
/* ====== */

struct mliEventTapeReader mliEventTapeReader_init(void)
{
        struct mliEventTapeReader tio;
        tio.tar = mliTar_init();
        tio.tarh = mliTarHeader_init();
        tio.event_number = 0;
        tio.cherenkov_bunch_block_number = 0;
        tio.block_at = 0;
        tio.block_size = 0;
        return tio;
}

int mliEventTapeReader_close(struct mliEventTapeReader *tio)
{
        if (tio->tar.stream) {
                chk_msg(mliTar_close(&tio->tar), "Can't close tar-file.");
        }

        (*tio) = mliEventTapeReader_init();
        return 1;
error:
        return 0;
}

int mliEventTapeReader_open(struct mliEventTapeReader *tio, const char *path)
{
        chk_msg(mliEventTapeReader_close(tio),
                "Can't close and free previous tar-io-reader.");
        chk_msg(mliTar_open(&tio->tar, path, "r"), "Can't open tar.");
        tio->has_tarh = mliTar_read_header(&tio->tar, &tio->tarh);

        chk_msg(mliEventTapeReader_read_readme_until_runh(tio),
                "Can't read info.");

        return 1;
error:
        return 0;
}

int mliEventTapeReader_read_readme_until_runh(struct mliEventTapeReader *tio)
{
        int i = 0;
        while (1) {
                chk_msg(i < 128, "Expected < 128 files before 'RUNH.float32'.");
                if (tio->has_tarh) {
                        if (strcmp(tio->tarh.name, "RUNH.float32") == 0) {
                                break;
                        } else {
                                /* read readme's payload */
                                int c;
                                char payload;
                                for (c = 0; c < tio->tarh.size; c++) {
                                        chk_msg(mliTar_read_data(
                                                        &tio->tar, &payload, 1),
                                                "Can't read readme's data.");
                                }
                                tio->has_tarh = mliTar_read_header(
                                        &tio->tar, &tio->tarh);
                                i += 1;
                        }
                } else {
                        break;
                }
        }
        return 1;
error:
        return 0;
}

int mliEventTapeReader_read_runh(struct mliEventTapeReader *tio, float *runh)
{
        chk_msg(tio->has_tarh, "Expected next tar-header.");
        chk_msg(strcmp(tio->tarh.name, "RUNH.float32") == 0,
                "Expected file to be 'RUNH.float32.'");
        chk_msg(tio->tarh.size == MLI_CORSIKA_HEADER_SIZE,
                "Expected RUNH to have size 273*sizeof(float)");
        chk_msg(mliTar_read_data(&tio->tar, (void *)runh, tio->tarh.size),
                "Can't read RUNH from tar.");
        chk_msg(runh[0] == mli_4chars_to_float("RUNH"),
                "Expected RUNH[0] == 'RUNH'");
        tio->has_tarh = mliTar_read_header(&tio->tar, &tio->tarh);
        return 1;
error:
        return 0;
}

int mliEventTapeReader_read_evth(struct mliEventTapeReader *tio, float *evth)
{
        uint64_t event_number_path, event_number_evth;
        char match[MLI_TAR_NAME_LENGTH] = "events/ddddddddd/EVTH.float32";

        if (!tio->has_tarh) {
                return 0;
        }
        chk_msg(mli_cstr_match_templeate(tio->tarh.name, match, 'd'),
                "Expected EVTH filename to match "
                "'events/ddddddddd/EVTH.float32'.");
        chk_msg(tio->tarh.size == MLI_CORSIKA_HEADER_SIZE,
                "Expected EVTH to have size 273*sizeof(float)");
        chk_msg(mliTar_read_data(&tio->tar, (void *)evth, tio->tarh.size),
                "Can't read EVTH from tar.");
        chk_msg(evth[0] == mli_4chars_to_float("EVTH"),
                "Expected EVTH[0] == 'EVTH'");
        chk_msg(mli_cstr_nto_uint64(
                        &event_number_path, &tio->tarh.name[7], 10, 9),
                "Can't parse event-number from path.");
        event_number_evth = (uint64_t)evth[MLI_CORSIKA_EVTH_EVENT_NUMBER];
        chk_msg(event_number_evth == event_number_path,
                "Expected same event-number in path and EVTH.");
        tio->event_number = event_number_evth;
        tio->cherenkov_bunch_block_number = 1;

        /* now there must follow a cherenkov-bunch-block */
        tio->has_tarh = mliTar_read_header(&tio->tar, &tio->tarh);
        chk_msg(tio->has_tarh, "Expected cherenkov-bunch-block after EVTH.");
        chk_msg(mliEventTapeReader_tarh_is_valid_cherenkov_block(tio),
                "Cherenkov-bunch-block's tar-header doesn't match.");

        chk_msg(tio->tarh.size % MLI_CORSIKA_BUNCH_SIZE == 0,
                "Expected cherenkov-bunch-block-size "
                "to be multiple of bunch-size.");
        tio->block_size = tio->tarh.size / MLI_CORSIKA_BUNCH_SIZE;
        tio->block_at = 0;
        return 1;
error:
        return 0;
}

int mliEventTapeReader_tarh_might_be_valid_cherenkov_block(
        const struct mliEventTapeReader *tio)
{
        char match[MLI_TAR_NAME_LENGTH] =
                "events/ddddddddd/cherenkov_bunches/ddddddddd.x8.float32";
        return mli_cstr_match_templeate(tio->tarh.name, match, 'd');
}

int mliEventTapeReader_tarh_is_valid_cherenkov_block(
        const struct mliEventTapeReader *tio)
{
        uint64_t event_number_path, block_number_path;
        chk_msg(tio->has_tarh, "Expected a next tar-header.");

        chk_msg(mliEventTapeReader_tarh_might_be_valid_cherenkov_block(tio),
                "Expected cherenkov-bunch-block-name to be valid.");

        chk_msg(mli_cstr_nto_uint64(
                        &event_number_path, &tio->tarh.name[7], 10, 9),
                "Can't parse event-number from path.");

        chk_msg(event_number_path == tio->event_number,
                "Expected same event-number in cherenkov-block-path and EVTH.");

        chk_msg(mli_cstr_nto_uint64(
                        &block_number_path, &tio->tarh.name[28 + 7], 10, 9),
                "Can't parse cherenkov-block-number from path.");

        chk_msg(block_number_path == tio->cherenkov_bunch_block_number,
                "Expected different cherenkov-bunch-block-number in "
                "cherenkov-block-path.");
        return 1;
error:
        return 0;
}

int mliEventTapeReader_read_cherenkov_bunch(
        struct mliEventTapeReader *tio,
        struct mliCorsikaPhotonBunch *bunch)
{
        float raw[8];
        int rc = mliEventTapeReader_read_cherenkov_bunch_raw(tio, raw);
        if (rc == 1) {
                mliCorsikaPhotonBunch_set_from_raw(bunch, raw);
                return 1;
        } else {
                return 0;
        }
}

int mliEventTapeReader_read_cherenkov_bunch_raw(
        struct mliEventTapeReader *tio,
        float *bunch_raw)
{
        if (tio->block_at == tio->block_size) {
                tio->cherenkov_bunch_block_number += 1;
                tio->has_tarh = mliTar_read_header(&tio->tar, &tio->tarh);

                if (!tio->has_tarh) {
                        return 0;
                }
                if (!mliEventTapeReader_tarh_might_be_valid_cherenkov_block(
                            tio)) {
                        return 0;
                }
                chk_msg(mliEventTapeReader_tarh_is_valid_cherenkov_block(tio),
                        "Cherenkov-bunch-block's tar-header doesn't match.");

                chk_msg(tio->tarh.size % MLI_CORSIKA_BUNCH_SIZE == 0,
                        "Expected cherenkov-bunch-block-size "
                        "to be multiple of bunch-size.");
                tio->block_size = tio->tarh.size / MLI_CORSIKA_BUNCH_SIZE;
                tio->block_at = 0;
        }

        if (tio->block_size == 0) {
                tio->has_tarh = mliTar_read_header(&tio->tar, &tio->tarh);
                return 0;
        }

        chk_msg(mliTar_read_data(
                        &tio->tar, (void *)(bunch_raw), MLI_CORSIKA_BUNCH_SIZE),
                "Failed to read cherenkov_bunch.");

        tio->block_at += 1;

        return 1;
error:
        return 0;
}



