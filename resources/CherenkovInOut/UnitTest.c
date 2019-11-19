// gcc UnitTest.c -o CherenkovInOutTest -lm

#include <stdio.h>
#include <string.h>

#include "DetectorSphere.h"
#include "MT19937.h"
#include "Photon.h"

int number_of_tests;
int number_of_failed_tests;

int expect_near(int line, double a, double b, char* comment) {
    number_of_tests = number_of_tests + 1;
    printf(".");
    if(fabs(a-b) < 1e-6) {
        return 0;
    }else{
        number_of_failed_tests = number_of_failed_tests + 1;
        printf("F");
        char info[1024] = "\nError in line ";
        char line_str[1024];
        sprintf(line_str, "%d", line);
        strcat(info, line_str);
        strcat(info, ": ");
        strcat(info, comment);
        strcat(info, "\n");
        fputs(info, stdout);
        return 1;
    }
}

int expect_true(int line, int what, char* comment) {
    number_of_tests = number_of_tests + 1;
    printf(".");
    if(what) {
        return 0;
    }else{
        number_of_failed_tests = number_of_failed_tests + 1;
        printf("F");
        char info[1024] = "\nError in line ";
        char line_str[1024];
        sprintf(line_str, "%d", line);
        strcat(info, line_str);
        strcat(info, ": ");
        strcat(info, comment);
        strcat(info, "\n");
        fputs(info, stdout);
        return 1;
    }   
}


int main() {
    number_of_tests = 0;
    number_of_failed_tests = 0;
    printf("CherenkovInOut UnitTests: Start\n");

    // Init a DetectorSphere
    {
        struct DetectorSphere sphere;
        DetectorSphere_init(&sphere, 1.0, 2.0, 3.0, 55.0);

        expect_near(__LINE__, sphere.x, 1.0, "init x position of DetectorSphere");
        expect_near(__LINE__, sphere.y, 2.0, "init y position of DetectorSphere");
        expect_near(__LINE__, sphere.z, 3.0, "init z position of DetectorSphere");
        expect_near(__LINE__, sphere.radius, 55.0, "init radius of DetectorSphere");
    }

    // Frontal hit on DetectorSphere
    {
        struct DetectorSphere sphere;
        DetectorSphere_init(&sphere, 0.0, 0.0, 0.0, 1.0);

        struct Bunch bunch;
        bunch.x = 0.0;
        bunch.y = 0.0;
        bunch.cx = 0.0;
        bunch.cy = 0.0;

        int hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, hit, "DetectorSphere, frontal hit");
    }

    // Frontal but too far away on DetectorSphere
    {
        struct DetectorSphere sphere;
        DetectorSphere_init(&sphere, 0.0, 0.0, 0.0, 1.0);

        struct Bunch bunch;
        bunch.x = 1.1;
        bunch.y = 0.0;
        bunch.cx = 0.0;
        bunch.cy = 0.0;

        int hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, !hit, "DetectorSphere, frontal but too far away");
    }

    // zero radius sphere frontal
    {
        struct DetectorSphere sphere;
        DetectorSphere_init(&sphere, 0.0, 0.0, 0.0, 0.0);

        struct Bunch bunch;
        bunch.x = 0.0;
        bunch.y = 0.0;
        bunch.cx = 0.0;
        bunch.cy = 0.0;

        int hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, hit, "DetectorSphere, zero radius, but exact hit");
    }

    // zero radius with offset
    {
        struct DetectorSphere sphere;
        DetectorSphere_init(&sphere, 0.0, 0.0, 0.0, 0.0);

        struct Bunch bunch;
        bunch.x = 1e-6;
        bunch.y = 0.0;
        bunch.cx = 0.0;
        bunch.cy = 0.0;

        int hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, !hit, "DetectorSphere, zero radius and too far away");
    }


    // frontal, close to edge
    {
        struct DetectorSphere sphere;
        DetectorSphere_init(&sphere, 0.0, 0.0, 0.0, 1.0);

        struct Bunch bunch;
        bunch.x = 0.0;
        bunch.y = 0.0;
        bunch.cx = 0.0;
        bunch.cy = 0.0;
        int hit;

        bunch.x = 1.01;
        bunch.y = 0.0;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, !hit, "DetectorSphere, x, slightly off");

        bunch.x = 0.99;
        bunch.y = 0.0;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, hit, "DetectorSphere, x, slightly on");

        bunch.x = 0.0;
        bunch.y = 1.01;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, !hit, "DetectorSphere, y, slightly off");

        bunch.x = 0.0;
        bunch.y = 0.99;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, hit, "DetectorSphere, y, slightly on");

        bunch.x =-1.01;
        bunch.y = 0.0;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, !hit, "DetectorSphere, -x, slightly off");

        bunch.x =-0.99;
        bunch.y = 0.0;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, hit, "DetectorSphere, -x, slightly on");

        bunch.x = 0.0;
        bunch.y =-1.01;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, !hit, "DetectorSphere, -y, slightly off");

        bunch.x = 0.0;
        bunch.y =-0.99;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, hit, "DetectorSphere, -y, slightly on");
    }

    // inclined photon bunch 45 deg
    {
        struct DetectorSphere sphere;
        DetectorSphere_init(&sphere, 0.0, 0.0, 1.0, sqrt(0.5)+0.01);

        struct Bunch bunch;
        bunch.x = 0.0;
        bunch.y = 0.0;
        bunch.cx = 0.0;
        bunch.cy = 0.0;
        int hit;

        bunch.cx = 0.70710678118654757;
        bunch.cy = 0.0;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, hit, "DetectorSphere, cx 45 deg");

        bunch.cx = 0.0;
        bunch.cy = 0.70710678118654757;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, hit, "DetectorSphere, cy 45 deg");

        bunch.cx =-0.70710678118654757;
        bunch.cy = 0.0;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, hit, "DetectorSphere, cx -45 deg");

        bunch.cx = 0.0;
        bunch.cy =-0.70710678118654757;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, hit, "DetectorSphere, cy -45 deg");

        sphere.radius = sqrt(0.5)-0.01;

        bunch.cx = 0.70710678118654757;
        bunch.cy = 0.0;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, !hit, "DetectorSphere, cx 45 deg, but too far away");

        bunch.cx = 0.0;
        bunch.cy = 0.70710678118654757;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, !hit, "DetectorSphere, cy 45 deg, but too far away");

        bunch.cx =-0.70710678118654757;
        bunch.cy = 0.0;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, !hit, "DetectorSphere, cx -45 deg, but too far away");

        bunch.cx = 0.0;
        bunch.cy =-0.70710678118654757;
        hit = DetectorSphere_is_hit_by_photon(&sphere, &bunch);
        expect_true(__LINE__, !hit, "DetectorSphere, cy -45 deg, but too far away");
    }

    // transform_to_detector_frame
    {
        struct DetectorSphere sphere;
        DetectorSphere_init(&sphere, 0.0, 0.0, 0.0, 0.0);

        struct Bunch bunch;
        bunch.x = 1.0;
        bunch.y = 2.0;
        bunch.cx = 0.1;
        bunch.cy = 0.2;

        DetectorSphere_transform_to_detector_frame(&sphere, &bunch);
        expect_near(__LINE__, bunch.x, 1.0, "DetectorSphere_transform, expect no offset in x");
        expect_near(__LINE__, bunch.y, 2.0, "DetectorSphere_transform, expect no offset in y");
        expect_near(__LINE__, bunch.cx, 0.1, "DetectorSphere_transform, expect no offset in cx");
        expect_near(__LINE__, bunch.cy, 0.2, "DetectorSphere_transform, expect no offset in cy");
    }


    // transform_to_detector_frame, expect offset
    {
        struct DetectorSphere sphere;
        DetectorSphere_init(&sphere, 0.3, 1.0, 0.0, 0.0);

        struct Bunch bunch;
        bunch.x = 1.0;
        bunch.y = 2.0;
        bunch.cx = 0.1;
        bunch.cy = 0.2;

        DetectorSphere_transform_to_detector_frame(&sphere, &bunch);
        expect_near(__LINE__, bunch.x, 1.0 - 0.3, "DetectorSphere_transform, expect offset in x");
        expect_near(__LINE__, bunch.y, 2.0 - 1.0, "DetectorSphere_transform, expect offset in y");
        expect_near(__LINE__, bunch.cx, 0.1, "DetectorSphere_transform, expect no offset in cx");
        expect_near(__LINE__, bunch.cy, 0.2, "DetectorSphere_transform, expect no offset in cy");
    }


    // MersenneTwister seeds
    {
        struct MT19937 mt;
        MT19937_init(&mt, 0);

        uint32_t pseudo_random_numbers[10];
        for(int i=0; i<10; i++)
            pseudo_random_numbers[i] = MT19937_uint32(&mt);

        MT19937_init(&mt, 0);

        uint32_t pseudo_random_numbers_2[10];           
        for(int i=0; i<10; i++)
            pseudo_random_numbers_2[i] = MT19937_uint32(&mt);

        for(int i=0; i<10; i++)
            expect_true(
                __LINE__, 
                pseudo_random_numbers[i] == pseudo_random_numbers_2[i],
                "Prng results schould be the same when using the same seed"
            );
    }

    // MersenneTwister uniform mean
    {
        const int N = 1000*1000;
        double rns[N];

        struct MT19937 mt;
        MT19937_init(&mt, 0);

        for(int i=0; i<N; i++)
            rns[i] = MT19937_uniform(&mt);

        double sum = 0.0;
        for(int i=0; i<N; i++)
            sum = sum + rns[i];

        const double mean = sum/(double)N;
        expect_true(
            __LINE__, 
            fabs(mean - 0.5) < 1e-3,
            "The mean of the uniform distribution should be close to 0.5"
        );

        double sum_var = 0.0;
        for(int i=0; i<N; i++)
            sum_var = sum_var + (rns[i] - mean)*(rns[i] - mean);

        const double varianve = sum_var/((double)N - 1.0);
        const double stddev = sqrt(varianve);

        expect_true(
            __LINE__, 
            fabs(stddev - sqrt(1.0/12.0)) < 1e-3,
            "The std dev of the uniform distribution should be close to sqrt(1/12)"
        );
    }

    // Bunch reaching observation level
    {
        struct Bunch bunch;
        bunch.size = 1.0;
        expect_true(__LINE__,
            Bunch_reaches_observation_level(&bunch, 0.5),
            "100 percent probability to reach ground"
        );

        bunch.size = 0.5;
        expect_true(__LINE__,
            Bunch_reaches_observation_level(&bunch, 0.5),
            "Bunch expected to reach ground"
        );

        bunch.size = 0.4;
        expect_true(__LINE__,
            !Bunch_reaches_observation_level(&bunch, 0.5),
            "Bunch expected to not reach ground"
        );

        bunch.size = 0.0;
        expect_true(__LINE__,
            !Bunch_reaches_observation_level(&bunch, 0.5),
            "Bunch expected to not reach ground"
        );
    }

    //The nearest integer
    { 
        expect_true(__LINE__,
            round_to_nearest_int(-1.6) == -2,
            "nearest integer -1.6 -> -2");

        expect_true(__LINE__,
            round_to_nearest_int(-1.3) == -1,
            "nearest integer -1.3 -> -1");

        expect_true(__LINE__,
            round_to_nearest_int(-1.0) == -1,
            "nearest integer -1.0 -> -1");

        expect_true(__LINE__,
            round_to_nearest_int(-0.7) == -1,
            "nearest integer -0.7 -> -1");

        expect_true(__LINE__,
            round_to_nearest_int(-0.5) == -1,
            "nearest integer -0.5 -> -1");

        expect_true(__LINE__,
            round_to_nearest_int(-0.2) == 0,
            "nearest integer -0.2 -> 0");

        expect_true(__LINE__,
            round_to_nearest_int(0.0) == 0,
            "nearest integer 0.0 -> 0");

        expect_true(__LINE__,
            round_to_nearest_int(+0.2) == 0,
            "nearest integer  0.2 -> 0");

        expect_true(__LINE__,
            round_to_nearest_int(+0.5) == 1,
            "nearest integer  0.5 -> 1");

        expect_true(__LINE__,
            round_to_nearest_int(+0.7) == 1,
            "nearest integer  0.7 -> 1");

        expect_true(__LINE__,
            round_to_nearest_int(+1.0) == 1,
            "nearest integer  0.2 -> 0");

        expect_true(__LINE__,
            round_to_nearest_int(1.3) == 1,
            "nearest integer 1.3 -> 1");

        expect_true(__LINE__,
            round_to_nearest_int(1.6) == 2,
            "nearest integer 1.6 -> 2");
    }


    // compress position
    {
        float orig_x = 1234.345; //cm
        expect_true(__LINE__,
            fabs(orig_x - decompress_position(compress_position(orig_x))) < 0.9,
            "fine"
        );

        orig_x = 0.0;
        expect_true(__LINE__,
            fabs(orig_x - decompress_position(compress_position(orig_x))) < 0.9,
            ""
        );

        orig_x = max_radius + 1;
        expect_true(__LINE__,
            !fabs(orig_x - decompress_position(compress_position(orig_x))) < 0.9,
            "too large, will fail"
        );

        orig_x = max_radius - 1;
        expect_true(__LINE__,
            fabs(orig_x - decompress_position(compress_position(orig_x))) < 0.9,
            ""
        );

        orig_x = -1234.345;
        expect_true(__LINE__,
            fabs(orig_x - decompress_position(compress_position(orig_x))) < 0.9,
            ""
        );

        orig_x = -max_radius - 1;
        expect_true(__LINE__,
            !fabs(orig_x - decompress_position(compress_position(orig_x))) < 0.9,
            ""
        );


        orig_x = -max_radius - 1;
        expect_true(__LINE__,
            !fabs(orig_x - decompress_position(compress_position(orig_x))) < 0.9,
            ""
        );

        orig_x = -max_radius + 1;
        expect_true(__LINE__,
            fabs(orig_x - decompress_position(compress_position(orig_x))) < 0.9,
            ""
        );
    }


    // compress incident angle
    {
        float orig_cx = 0.923;
        expect_true(__LINE__,
            fabs(orig_cx - decompress_incident_direction(compress_incident_direction(orig_cx))) < 1e-5,
            ""
        );

        orig_cx = -0.923;
        expect_true(__LINE__,
            fabs(orig_cx - decompress_incident_direction(compress_incident_direction(orig_cx))) < 1e-5,
            ""
        );

        orig_cx = 0.0;
        expect_true(__LINE__,
            fabs(orig_cx - decompress_incident_direction(compress_incident_direction(orig_cx))) < 1e-5,
            ""
        );

        orig_cx = 1.0;
        expect_true(__LINE__,
            fabs(orig_cx - decompress_incident_direction(compress_incident_direction(orig_cx))) < 1e-5,
            ""
        );
    }


    // compress wavelength
    {
        float orig_w = 366.53;
        expect_true(__LINE__,
            fabs(orig_w - decompress_wavelength(compress_wavelength(orig_w))) < 2.0,
            ""
        );

        orig_w = 435.13;
        expect_true(__LINE__,
            fabs(orig_w - decompress_wavelength(compress_wavelength(orig_w))) < 2.0,
            ""
        );

        orig_w = min_wavelength;
        expect_true(__LINE__,
            fabs(orig_w - decompress_wavelength(compress_wavelength(orig_w))) < 2.0,
            ""
        );

        orig_w = min_wavelength - 1.0;
        expect_true(__LINE__,
            !fabs(orig_w - decompress_wavelength(compress_wavelength(orig_w))) < 2.0,
            ""
        );

        orig_w = max_wavelength;
        expect_true(__LINE__,
            fabs(orig_w - decompress_wavelength(compress_wavelength(orig_w))) < 2.0,
            ""
        );

        orig_w = max_wavelength + 1.0;
        expect_true(__LINE__,
            !fabs(orig_w - decompress_wavelength(compress_wavelength(orig_w))) < 2.0,
            ""
        );         
    }

    // compress wavelength
    {
        float orig_alt = min_emission_altidute;
        expect_true(__LINE__,
            fabs(orig_alt - decompress_emission_altitude(compress_emission_altitude(orig_alt))) < 100.0e2,
            ""
        );

        orig_alt = min_emission_altidute - 1.0;
        expect_true(__LINE__,
            !fabs(orig_alt - decompress_emission_altitude(compress_emission_altitude(orig_alt))) < 100.0e2,
            ""
        );

        orig_alt = max_emission_altidute;
        expect_true(__LINE__,
            !fabs(orig_alt - decompress_emission_altitude(compress_emission_altitude(orig_alt))) < 100.0e2,
            ""
        );

        orig_alt = max_emission_altidute + 1.0;
        expect_true(__LINE__,
            !fabs(orig_alt - decompress_emission_altitude(compress_emission_altitude(orig_alt))) < 100.0e2,
            ""
        );

        orig_alt = 24.355*1e3*1e2; //cm -> 25.355km
        expect_true(__LINE__,
            fabs(orig_alt - decompress_emission_altitude(compress_emission_altitude(orig_alt))) < 100.0e2,
            ""
        );

        orig_alt = 33.678*1e3*1e2; //cm -> 25.355km
        expect_true(__LINE__,
            fabs(orig_alt - decompress_emission_altitude(compress_emission_altitude(orig_alt))) < 100.0e2,
            ""
        );

        orig_alt = 78.245*1e3*1e2; //cm -> 25.355km
        expect_true(__LINE__,
            fabs(orig_alt - decompress_emission_altitude(compress_emission_altitude(orig_alt))) < 100.0e2,
            ""
        );


        // compress mother charge
        {
            float orig_c = -128;
            expect_true(__LINE__,
                fabs(orig_c - decompress_mother_charge(compress_mother_charge(orig_c))) < 0.5,
                ""
            );

            orig_c = -128 -1;
            expect_true(__LINE__,
                !fabs(orig_c - decompress_mother_charge(compress_mother_charge(orig_c))) < 0.5,
                ""
            );

            orig_c = +127;
            expect_true(__LINE__,
                fabs(orig_c - decompress_mother_charge(compress_mother_charge(orig_c))) < 0.5,
                ""
            );

            orig_c = +127 + 1;
            expect_true(__LINE__,
                !fabs(orig_c - decompress_mother_charge(compress_mother_charge(orig_c))) < 0.5,
                ""
            );

            orig_c = +1;
            expect_true(__LINE__,
                fabs(orig_c - decompress_mother_charge(compress_mother_charge(orig_c))) < 0.5,
                ""
            );

            orig_c = 0;
            expect_true(__LINE__,
                fabs(orig_c - decompress_mother_charge(compress_mother_charge(orig_c))) < 0.5,
                ""
            );

            orig_c = -1;
            expect_true(__LINE__,
                fabs(orig_c - decompress_mother_charge(compress_mother_charge(orig_c))) < 0.5,
                ""
            );
        }


        // Photon size
        {
            struct Photon photon;
            expect_true(__LINE__,
                sizeof(struct Photon) == 16,
                ""
            );
        }
    }
    printf("\nCherenkovInOut UnitTests: Finished\n");
    return number_of_failed_tests;
}