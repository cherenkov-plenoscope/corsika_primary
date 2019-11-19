#ifndef __CherenkovInOutPhoton_H_INCLUDED__
#define __CherenkovInOutPhoton_H_INCLUDED__

#include <math.h>
#include <stdint.h>

//-------------------- Photon --------------------------------------------------
struct Photon{
   int16_t x;
   int16_t y;
   int16_t cx;
   int16_t cy;
   float arrival_time;
   uint8_t wavelength;
   int8_t mother_charge;
   uint16_t emission_altitude;
};

int16_t round_to_nearest_int(const float number) {
   return number > 0 ? (int16_t)(number + 0.5) : (int16_t)(number - 0.5);
}

const float max_int16 = 32767.0;
const float max_uint8 = 255.0;
const float max_radius = 260e2; //560m diameter -> 8mm
const float max_emission_altidute = 100.0*1000.0*1.0e2; //100km -> 3.05m
const float min_emission_altidute = 0.0; 
const float max_relative_arrival_time = 3276.8; //ns -> 0.1ns
const float max_wavelength = 1200; //nm 
const float min_wavelength = 200; //nm


int16_t compress_position(const float pos) {
   return round_to_nearest_int((pos/max_radius)*max_int16);
}
float decompress_position(const int16_t pos) {
   return ((float)pos/max_int16)*max_radius;
}


int16_t compress_incident_direction(const float cx) {
   return round_to_nearest_int(cx*max_int16);
}
float decompress_incident_direction(const int16_t cx) {
   return (float)cx/max_int16;
}


int16_t compress_emission_altitude(float alt) {
   alt = fabs(alt);
   return round_to_nearest_int((alt/max_emission_altidute)*max_int16);
}
float decompress_emission_altitude(const uint16_t alt) {
   return ((float)alt/max_int16)*max_emission_altidute;
}


uint8_t compress_wavelength(float wavelength) {
   wavelength = fabs(wavelength);
   float out = (wavelength - min_wavelength)/(max_wavelength - min_wavelength)*max_uint8;
   return round_to_nearest_int(out);
}
float decompress_wavelength(const uint8_t wavelength) {
   return ((float)wavelength/max_uint8)*(max_wavelength - min_wavelength) + min_wavelength;
}


int8_t compress_mother_charge(const float charge) {
   return round_to_nearest_int(charge);
}
float decompress_mother_charge(const int8_t charge) {
   return (float)charge;
}


void Photon_init_from_bunch(struct Photon* photon, const struct Bunch* bunch) {
   photon->x = compress_position(bunch->x);
   photon->y = compress_position(bunch->y);
   photon->cx = compress_incident_direction(bunch->cx);
   photon->cy = compress_incident_direction(bunch->cy);
   photon->arrival_time = bunch->arrival_time;
   photon->wavelength = compress_wavelength(bunch->wavelength);
   photon->emission_altitude = compress_emission_altitude(bunch->emission_altitude);
   photon->mother_charge = compress_mother_charge(bunch->mother_charge);
}

#endif // __CherenkovInOutPhoton_H_INCLUDED__ 