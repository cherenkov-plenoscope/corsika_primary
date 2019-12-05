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

#ifndef MICROTAR_H
#define MICROTAR_H

#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>

#define MTAR_VERSION "1000.0.0"

#define mtar_clean_errno() (errno == 0 ? "None" : strerror(errno))

#define mtar_log_err(M) fprintf(stderr, "[ERROR] (%s:%d: errno: %s) " M "\n", \
  __FILE__, __LINE__, mtar_clean_errno())

#define mtar_check(A, M) if (!(A)) {mtar_log_err(M); errno = 0; goto error;}

enum {
  MTAR_ESUCCESS     =  0,
  MTAR_EFAILURE     = -1,
  MTAR_EOPENFAIL    = -2,
  MTAR_EREADFAIL    = -3,
  MTAR_EWRITEFAIL   = -4,
  MTAR_ESEEKFAIL    = -5,
  MTAR_EBADCHKSUM   = -6,
  MTAR_ENULLRECORD  = -7,
  MTAR_ENOTFOUND    = -8
};

enum {
  MTAR_TREG   = '0',
  MTAR_TLNK   = '1',
  MTAR_TSYM   = '2',
  MTAR_TCHR   = '3',
  MTAR_TBLK   = '4',
  MTAR_TDIR   = '5',
  MTAR_TFIFO  = '6'
};

typedef struct {
  uint64_t mode;
  uint64_t owner;
  uint64_t size;
  uint64_t mtime;
  uint64_t type;
  char name[100];
  char linkname[100];
} mtar_header_t;


typedef struct mtar_t mtar_t;

struct mtar_t {
  int64_t (*read)(mtar_t *tar, void *data, uint64_t size);
  int64_t (*write)(mtar_t *tar, const void *data, uint64_t size);
  int64_t (*seek)(mtar_t *tar, uint64_t pos);
  int64_t (*close)(mtar_t *tar);
  void *stream;
  uint64_t pos;
  uint64_t remaining_data;
  uint64_t last_header;
};


const char* mtar_strerror(int64_t err);

int64_t mtar_open(mtar_t *tar, const char *filename, const char *mode);
int64_t mtar_close(mtar_t *tar);

int64_t mtar_seek(mtar_t *tar, uint64_t pos);
int64_t mtar_rewind(mtar_t *tar);
int64_t mtar_next(mtar_t *tar);
int64_t mtar_find(mtar_t *tar, const char *name, mtar_header_t *h);
int64_t mtar_read_header(mtar_t *tar, mtar_header_t *h);
int64_t mtar_read_data(mtar_t *tar, void *ptr, uint64_t size);

int64_t mtar_write_header(mtar_t *tar, const mtar_header_t *h);
int64_t mtar_write_file_header(mtar_t *tar, const char *name, uint64_t size);
int64_t mtar_write_dir_header(mtar_t *tar, const char *name);
int64_t mtar_write_data(mtar_t *tar, const void *data, uint64_t size);
int64_t mtar_finalize(mtar_t *tar);

typedef struct {
  char name[100];
  char mode[8];
  char owner[8];
  char group[8];
  char size[12];
  char mtime[12];
  char checksum[8];
  char type;
  char linkname[100];
  char _padding[255];
} _mtar_raw_header_t;


static uint64_t _mtar_round_up(uint64_t n, uint64_t incr) {
  return n + (incr - n % incr) % incr;
}


static uint64_t _mtar_checksum(const _mtar_raw_header_t* rh) {
  uint64_t i;
  unsigned char *p = (unsigned char*) rh;
  uint64_t res = 256;
  for (i = 0; i < offsetof(_mtar_raw_header_t, checksum); i++) {
    res += p[i];
  }
  for (i = offsetof(_mtar_raw_header_t, type); i < sizeof(*rh); i++) {
    res += p[i];
  }
  return res;
}


static int64_t _mtar_tread(mtar_t *tar, void *data, uint64_t size) {
  int64_t err = tar->read(tar, data, size);
  tar->pos += size;
  return err;
}


static int64_t _mtar_twrite(mtar_t *tar, const void *data, uint64_t size) {
  int64_t err = tar->write(tar, data, size);
  tar->pos += size;
  return err;
}


static int64_t _mtar_write_null_bytes(mtar_t *tar, int64_t n) {
  int64_t i, err;
  char nul = '\0';
  for (i = 0; i < n; i++) {
    err = _mtar_twrite(tar, &nul, 1);
    if (err) {
      return err;
    }
  }
  return MTAR_ESUCCESS;
}


static int64_t _mtar_raw_to_header(
  mtar_header_t *h,
  const _mtar_raw_header_t *rh) {
  uint64_t chksum1, chksum2;

  /* If the checksum starts with a null byte we assume the record is NULL */
  if (*rh->checksum == '\0') {
    return MTAR_ENULLRECORD;
  }

  /* Build and compare checksum */
  chksum1 = _mtar_checksum(rh);
  sscanf(rh->checksum, "%lo", &chksum2);
  if (chksum1 != chksum2) {
    return MTAR_EBADCHKSUM;
  }

  /* Load raw header into header */
  sscanf(rh->mode, "%lo", &h->mode);
  sscanf(rh->owner, "%lo", &h->owner);
  sscanf(rh->size, "%lo", &h->size);
  sscanf(rh->mtime, "%lo", &h->mtime);
  h->type = rh->type;
  snprintf(h->name, sizeof(h->name), "%s", rh->name);
  snprintf(h->linkname, sizeof(h->linkname), "%s", rh->linkname);

  return MTAR_ESUCCESS;
}


static int64_t _mtar_header_to_raw(
  _mtar_raw_header_t *rh,
  const mtar_header_t *h) {
  uint64_t chksum;

  /* Load header into raw header */
  memset(rh, 0, sizeof(*rh));
  snprintf(rh->mode, sizeof(rh->mode), "%lo", h->mode);
  snprintf(rh->owner, sizeof(rh->owner), "%lo", h->owner);
  snprintf(rh->size, sizeof(rh->size), "%lo", h->size);
  snprintf(rh->mtime, sizeof(rh->mtime), "%lo", h->mtime);
  rh->type = h->type ? h->type : MTAR_TREG;
  snprintf(rh->name, sizeof(rh->name), "%s", h->name);
  snprintf(rh->linkname, sizeof(rh->linkname), "%s", h->linkname);

  /* Calculate and write checksum */
  chksum = _mtar_checksum(rh);
  snprintf(rh->checksum, sizeof(rh->checksum), "%06lo", chksum);
  rh->checksum[7] = ' ';

  return MTAR_ESUCCESS;
}


const char* mtar_strerror(int64_t err) {
  switch (err) {
    case MTAR_ESUCCESS     : return "success";
    case MTAR_EFAILURE     : return "failure";
    case MTAR_EOPENFAIL    : return "could not open";
    case MTAR_EREADFAIL    : return "could not read";
    case MTAR_EWRITEFAIL   : return "could not write";
    case MTAR_ESEEKFAIL    : return "could not seek";
    case MTAR_EBADCHKSUM   : return "bad checksum";
    case MTAR_ENULLRECORD  : return "null record";
    case MTAR_ENOTFOUND    : return "file not found";
  }
  return "unknown error";
}


static int64_t _mtar_file_write(mtar_t *tar, const void *data, uint64_t size) {
  int64_t res = fwrite(data, 1, size, (FILE*)tar->stream);
  return (res == (int64_t)size) ? MTAR_ESUCCESS : MTAR_EWRITEFAIL;
}

static int64_t _mtar_file_read(mtar_t *tar, void *data, uint64_t size) {
  int64_t res = fread(data, 1, size, (FILE*)tar->stream);
  return (res == size) ? MTAR_ESUCCESS : MTAR_EREADFAIL;
}

static int64_t _mtar_file_seek(mtar_t *tar, uint64_t offset) {
  int64_t res = fseek((FILE*)tar->stream, offset, SEEK_SET);
  return (res == 0) ? MTAR_ESUCCESS : MTAR_ESEEKFAIL;
}

static int64_t _mtar_file_close(mtar_t *tar) {
  fclose((FILE*)tar->stream);
  return MTAR_ESUCCESS;
}


int64_t mtar_open(mtar_t *tar, const char *filename, const char *mode) {
  int64_t err;
  mtar_header_t h;

  /* Init tar struct and functions */
  memset(tar, 0, sizeof(*tar));
  tar->write = _mtar_file_write;
  tar->read = _mtar_file_read;
  tar->seek = _mtar_file_seek;
  tar->close = _mtar_file_close;

  /* Assure mode is always binary */
  if ( strchr(mode, 'r') ) mode = "rb";
  if ( strchr(mode, 'w') ) mode = "wb";
  if ( strchr(mode, 'a') ) mode = "ab";
  /* Open file */
  tar->stream = fopen(filename, mode);
  if (!tar->stream) {
    return MTAR_EOPENFAIL;
  }
  /* Read first header to check it is valid if mode is `r` */
  if (*mode == 'r') {
    err = mtar_read_header(tar, &h);
    if (err != MTAR_ESUCCESS) {
      mtar_close(tar);
      return err;
    }
  }

  /* Return ok */
  return MTAR_ESUCCESS;
}


int64_t mtar_close(mtar_t *tar) {
  return tar->close(tar);
}


int64_t mtar_seek(mtar_t *tar, uint64_t pos) {
  int64_t err = tar->seek(tar, pos);
  tar->pos = pos;
  return err;
}


int64_t mtar_rewind(mtar_t *tar) {
  tar->remaining_data = 0;
  tar->last_header = 0;
  return mtar_seek(tar, 0);
}


int64_t mtar_next(mtar_t *tar) {
  int64_t err, n;
  mtar_header_t h;
  /* Load header */
  err = mtar_read_header(tar, &h);
  if (err) {
    return err;
  }
  /* Seek to next record */
  n = _mtar_round_up(h.size, 512) + sizeof(_mtar_raw_header_t);
  return mtar_seek(tar, tar->pos + n);
}


int64_t mtar_find(mtar_t *tar, const char *name, mtar_header_t *h) {
  int64_t err;
  mtar_header_t header;
  /* Start at beginning */
  err = mtar_rewind(tar);
  if (err) {
    return err;
  }
  /* Iterate all files until we hit an error or find the file */
  while ( (err = mtar_read_header(tar, &header)) == MTAR_ESUCCESS ) {
    if ( !strcmp(header.name, name) ) {
      if (h) {
        *h = header;
      }
      return MTAR_ESUCCESS;
    }
    mtar_next(tar);
  }
  /* Return error */
  if (err == MTAR_ENULLRECORD) {
    err = MTAR_ENOTFOUND;
  }
  return err;
}


int64_t mtar_read_header(mtar_t *tar, mtar_header_t *h) {
  int64_t err;
  _mtar_raw_header_t rh;
  /* Save header position */
  tar->last_header = tar->pos;
  /* Read raw header */
  err = _mtar_tread(tar, &rh, sizeof(rh));
  if (err) {
    return err;
  }
  /* Seek back to start of header */
  err = mtar_seek(tar, tar->last_header);
  if (err) {
    return err;
  }
  /* Load raw header into header struct and return */
  return _mtar_raw_to_header(h, &rh);
}


int64_t mtar_read_data(mtar_t *tar, void *ptr, uint64_t size) {
  int64_t err;
  /* If we have no remaining data then this is the first read, we get the size,
   * set the remaining data and seek to the beginning of the data */
  if (tar->remaining_data == 0) {
    mtar_header_t h;
    /* Read header */
    err = mtar_read_header(tar, &h);
    if (err) {
      return err;
    }
    /* Seek past header and init remaining data */
    err = mtar_seek(tar, tar->pos + sizeof(_mtar_raw_header_t));
    if (err) {
      return err;
    }
    tar->remaining_data = h.size;
  }
  /* Read data */
  err = _mtar_tread(tar, ptr, size);
  if (err) {
    return err;
  }
  tar->remaining_data -= size;
  /* If there is no remaining data we've finished reading and seek back to the
   * header */
  if (tar->remaining_data == 0) {
    return mtar_seek(tar, tar->last_header);
  }
  return MTAR_ESUCCESS;
}


int64_t mtar_write_header(mtar_t *tar, const mtar_header_t *h) {
  _mtar_raw_header_t rh;
  /* Build raw header and write */
  _mtar_header_to_raw(&rh, h);
  tar->remaining_data = h->size;
  return _mtar_twrite(tar, &rh, sizeof(rh));
}


int64_t mtar_write_file_header(mtar_t *tar, const char *name, uint64_t size) {
  mtar_header_t h;
  /* Build header */
  memset(&h, 0, sizeof(h));
  snprintf(h.name, sizeof(h.name), "%s", name);
  h.size = size;
  h.type = MTAR_TREG;
  h.mode = 0664;
  /* Write header */
  return mtar_write_header(tar, &h);
}


int64_t mtar_write_dir_header(mtar_t *tar, const char *name) {
  mtar_header_t h;
  /* Build header */
  memset(&h, 0, sizeof(h));
  snprintf(h.name, sizeof(h.name), "%s", name);
  h.type = MTAR_TDIR;
  h.mode = 0775;
  /* Write header */
  return mtar_write_header(tar, &h);
}


int64_t mtar_write_data(mtar_t *tar, const void *data, uint64_t size) {
  int64_t err;
  /* Write data */
  err = _mtar_twrite(tar, data, size);
  if (err) {
    return err;
  }
  tar->remaining_data -= size;
  /* Write padding if we've written all the data for this file */
  if (tar->remaining_data == 0) {
    return _mtar_write_null_bytes(
      tar,
      _mtar_round_up(tar->pos, 512) - tar->pos);
  }
  return MTAR_ESUCCESS;
}


int64_t mtar_write_data_from_stream(mtar_t *tar, FILE *stream, uint64_t size) {
  const uint64_t buffer_size = 1024*1024;
  int64_t res_read;
  uint64_t to_be_copied;
  char* buffer = (char*)malloc(buffer_size);
  mtar_check(buffer, "Out of Memory");

  to_be_copied = size;
  while (to_be_copied > 0) {
    int64_t block_size = to_be_copied < buffer_size ? to_be_copied:buffer_size;
    res_read = fread(buffer, sizeof(char), block_size, stream);
    mtar_check(res_read == block_size, "Failed to read from file-stream");

    mtar_check(mtar_write_data(tar, buffer, block_size) == MTAR_ESUCCESS,
      "Failed to write stream-buffer to tar-file.");
    to_be_copied = to_be_copied - block_size;
  }
  free(buffer);
  return MTAR_ESUCCESS;
error:
  free(buffer);
  return MTAR_EWRITEFAIL;
}

int64_t mtar_finalize(mtar_t *tar) {
  /* Write two NULL records */
  return _mtar_write_null_bytes(tar, sizeof(_mtar_raw_header_t) * 2);
}

#endif
