/* Copyright (c) 2019 Sebastian A. Mueller                                    */
/*                    Max-Planck-Institute for nuclear-physics, Heidelberg    */

/* gcc test_microtar.c -o TestMicroTar -lm -std=c89 -Wall -pedantic           */
/* g++ test_microtar.c -o TestMicroTar -lm -Wall -pedantic                    */

#include <stdio.h>
#include <string.h>
#include <string.h>

#include "microtar.h"

#define CHECK(test) \
    do { \
        if ( !(test) ) { \
            printf("In %s, line %d\n", __FILE__, __LINE__); \
            printf("Expected true\n"); \
            return EXIT_FAILURE; \
        } \
    } while (0)


int main() {

  /* open non existing file */
  {
    mtar_t tar;
    CHECK(mtar_open(&tar, "_does_not_exist.tar", "r") != 0);
  }

  /* Write two text-files */
  {
    mtar_t tar;
    mtar_header_t header;
    const char *str1 = "Hello world";
    const char *str2 = "Goodbye world";
    char str_back[1024];

    CHECK(mtar_open(&tar, "_test_two_files.tar", "w") == 0);
    CHECK(mtar_write_file_header(&tar, "test1.txt", strlen(str1)) == 0);
    CHECK(mtar_write_data(&tar, str1, strlen(str1)) == 0);
    CHECK(mtar_write_file_header(&tar, "test2.txt", strlen(str2)) == 0);
    CHECK(mtar_write_data(&tar, str2, strlen(str2)) == 0);
    CHECK(mtar_finalize(&tar) == 0);
    CHECK(mtar_close(&tar) == 0);

    /* open again for reading */
    CHECK(mtar_open(&tar, "_test_two_files.tar", "r") == 0);

    CHECK(mtar_read_header(&tar, &header) == 0);
    CHECK(strncmp(header.name, "test1.txt", strlen("test1.txt")) == 0);
    CHECK(header.size == strlen(str1));
    CHECK(mtar_read_data(&tar, str_back, strlen(str1)) == 0);
    str_back[strlen(str1)] = '\0';
    CHECK(strncmp(str_back, str1, 1024) == 0);

    CHECK(mtar_next(&tar) == 0);
    CHECK(mtar_read_header(&tar, &header) == 0);
    CHECK(strncmp(header.name, "test2.txt", strlen("test2.txt")) == 0);
    CHECK(header.size == strlen(str2));
    CHECK(mtar_read_data(&tar, str_back, strlen(str2)) == 0);
    str_back[strlen(str2)] = '\0';
    CHECK(strncmp(str_back, str2, 1024) == 0);

    CHECK(mtar_next(&tar) == 0);
    CHECK(mtar_read_header(&tar, &header) != 0);
    CHECK(mtar_close(&tar) == 0);
  }

  /* find files based on filename */
  {
    mtar_t tar;
    mtar_header_t header;
    CHECK(mtar_open(&tar, "_test_two_files.tar", "r") == 0);
    CHECK(mtar_find(&tar, "test2.txt", &header) == 0);
    CHECK(strncmp(header.name, "test2.txt", strlen("test2.txt")) == 0);

    CHECK(mtar_find(&tar, "test1.txt", &header) == 0);
    CHECK(strncmp(header.name, "test1.txt", strlen("test1.txt")) == 0);

    CHECK(mtar_find(&tar, "does_not_exist.txt", &header) != 0);
    CHECK(mtar_close(&tar) == 0);
  }

  /* Write from file larger 4 Giga Byte  a.k.a. 32bit limit */
  {
    uint64_t hans = 1337;
    uint64_t i;
    int64_t fsize, res_write;
    mtar_t tar;
    mtar_header_t header;
    uint64_t num_uint64_in_buffer = 672*1000*1000;

    const char *runh = "I might be a run-header.";
    const char *evth = "And might be an event-header.";
    const char *rune = "I might be some stuff at the end.";

    FILE *f;
    f = fopen("_test_buffer.bin", "wb");
    CHECK(f != NULL);
    for (i = 0; i < num_uint64_in_buffer; i++) {
      res_write = fwrite(&hans, 1, sizeof(uint64_t), f);
      CHECK(res_write == sizeof(uint64_t));
      hans += 1;
    }
    CHECK(fclose(f) == 0);

    CHECK(mtar_open(&tar, "_test_from_file.tar", "w") == 0);
    CHECK(mtar_write_file_header(&tar, "runh.txt", strlen(runh)) == 0);
    CHECK(mtar_write_data(&tar, runh, strlen(runh)) == 0);
    CHECK(mtar_write_file_header(&tar, "evth.txt", strlen(evth)) == 0);
    CHECK(mtar_write_data(&tar, evth, strlen(evth)) == 0);

    f = fopen("_test_buffer.bin", "rb");
    CHECK(f != NULL);
    CHECK(fseek(f, 0L, SEEK_END) == 0);
    fsize = ftell(f);
    CHECK(fsize >= -1);
    rewind(f);
    CHECK(mtar_write_file_header(&tar, "cherenkov-bunches.u8", fsize) == 0);
    CHECK(mtar_write_data_from_stream(&tar, f, fsize) == 0);
    CHECK(fclose(f) == 0);

    CHECK(mtar_write_file_header(&tar, "rune.txt", strlen(rune)) == 0);
    CHECK(mtar_write_data(&tar, rune, strlen(rune)) == 0);
    CHECK(mtar_finalize(&tar) == 0);
    CHECK(mtar_close(&tar) == 0);


    /* read back and check size */
    CHECK(mtar_open(&tar, "_test_from_file.tar", "r") == 0);
    CHECK(mtar_find(&tar, "cherenkov-bunches.u8", &header) == 0);

    hans = 1337;
    for (i = 0; i < num_uint64_in_buffer; i++) {
      uint64_t tmp;
      CHECK(mtar_read_data(&tar, &tmp, sizeof(uint64_t)) == 0);
      /* fprintf(stderr, "%ld %ld %ld\n", i, hans, tmp); */
      CHECK(tmp == hans);
      hans += 1;
    }

    CHECK(mtar_next(&tar) == 0);
    CHECK(mtar_read_header(&tar, &header) == 0);
    CHECK(strncmp(header.name, "rune.txt", strlen("rune.txt")) == 0);
    CHECK(header.size == strlen(rune));
    CHECK(mtar_close(&tar) == 0);
  }
  return 0;
}