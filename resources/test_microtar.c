// gcc test_microtar.c -o TestMicroTar -lm

#include <stdio.h>
#include <string.h>

#include "microtar.h"


int main() {
    double hans = 1337.42;
    FILE *f;
    f = fopen("test_buffer.bin", "wb");
    for (int i = 0; i < 1000*1000; i++) {
        fwrite(&hans, 1, sizeof(double), f);
        hans += 1.0;
    }
    fclose(f);

    mtar_t tar;
    const char *str1 = "Hello world";
    const char *str2 = "Goodbye world";

    /* Open archive for writing */
    mtar_open(&tar, "test.tar", "w");

    /* Write strings to files `test1.txt` and `test2.txt` */
    mtar_write_file_header(&tar, "test1.txt", strlen(str1));
    mtar_write_data(&tar, str1, strlen(str1));
    mtar_write_file_header(&tar, "test2.txt", strlen(str2));
    mtar_write_data(&tar, str2, strlen(str2));

    f = fopen("test_buffer.bin", "rb");
    fseek(f, 0L, SEEK_END);
    uint64_t fsize = ftell(f);
    rewind(f);
    mtar_write_file_header(&tar, "test3_from_stream.bin", fsize);
    mtar_write_stream(&tar, f, fsize);
    fclose(f);

    /* Finalize -- this needs to be the last thing done before closing */
    mtar_finalize(&tar);

    /* Close archive */
    mtar_close(&tar);
}