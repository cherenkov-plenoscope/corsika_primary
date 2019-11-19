#ifndef __CherenkovInOut_H_INCLUDED__
#define __CherenkovInOut_H_INCLUDED__

#include "Photon.h"

//-------------------- CherenkovInOut ------------------------------------------
const double VACUUM_SPEED_OF_LIGHT = 29.9792458;

struct CherenkovInOut {
   char output_path [1024];
   char runh_path [1024];
   char evth_template_path [1024];
   char photon_block_template_path [1024];
   char readme_path [1024];
   double observation_level;
   double speed_of_light_in_air_on_observation_level;
   double time_offset;
   FILE *current_photons;
};

void CherenkovInOut_init(struct CherenkovInOut* sane, char* output_path) {
   sane->current_photons = NULL;
   strcpy(sane->output_path, output_path);

   strcpy(sane->runh_path, sane->output_path);
   strcat(sane->runh_path, ".runh");

   strcpy(sane->evth_template_path, sane->output_path);
   strcat(sane->evth_template_path, ".evth.");

   strcpy(sane->photon_block_template_path, sane->output_path);
   strcat(sane->photon_block_template_path, ".photons.");

   strcpy(sane->readme_path, sane->output_path);
   strcat(sane->readme_path, ".README.md");

   sane->observation_level = -1.0;
   sane->speed_of_light_in_air_on_observation_level = VACUUM_SPEED_OF_LIGHT;
   sane->time_offset = 0.0;
}

void CherenkovInOut_assert_file_is_open(
   struct CherenkovInOut* sane, 
   FILE* file, 
   char* name
) {
   if(file == NULL) {
      char message [2048];
      strcpy(message, "CherenkovInOut: unable to open specific file: '");
      strcat(message, name);
      strcat(message, "'\n");
      fputs(message, stderr);
      exit(1);      
   }
}

void CherenkovInOut_write_readme(struct CherenkovInOut* sane) {
   char readme[] = 
   "Cherenkov I/O\n"
   "-------------\n"
   "\n"
   ".runh\n"
   "-----\n"
   "     float32 array [273 x 1], CORSIKA run header.\n"
   "\n"
   ".evth.XXX\n"
   "---------\n"
   "     float32 array [273 x 1], CORSIKA event header of event XXX.\n"
   "\n"
   ".photons.XXX\n"
   "------------\n"
   "     struct array [number_of_photons x 1], photons of event XXX.\n"
   "\n"
   "Photon struct\n"
   "-------------\n"
   "     int16    _x  incident position on observation plane [cm]\n"
   "     int16    _y  incident position on observation plane [cm]\n"
   "              pos = (_pos/max_int16)*260e2\n"
   "\n"
   "     int16    _cx incident direction relative to surface normal of observation plane [1]\n"
   "     int16    _cy incident direction relative to surface normal of observation plane [1]\n"
   "              cx = _cx/max_int16\n"
   "\n"
   "     float32  arrival time on observation plane, relative to primary's first interaction [ns]\n"
   "\n"
   "     uint8    _wavelength in nano meter [nm]\n"
   "              wavelength = (_wavelength/max_uint8)*(1e3) + 2e2\n"
   "\n"
   "     uint8    mother particle electric charge [1]\n"
   "\n"
   "     uint16   _emission_altitude above sea level (not above observation plane) [cm]\n"
   "              emission_altitude = (_emission_altitude/max_int16)*100*1e3*1e2\n"
   "\n"
   "     Total photon size is 2+2+2+2+4+1+2+1 = 16 bytes\n"
   "\n"
   "\n"
   "To blame\n"
   "--------\n"
   "     Sebastian Achim Mueller, ETH Zurich 2016.\n";

   FILE* out;
   out = fopen(sane->readme_path, "w");
   CherenkovInOut_assert_file_is_open(sane, out, sane->readme_path);
   fputs(readme, out);
   fclose(out);    
}

void CherenkovInOut_evth_path(
   struct CherenkovInOut* sane, 
   int event_number, 
   char* evth_path
) {
   char evt_num[1024];
   sprintf(evt_num, "%d", event_number);
   strcpy(evth_path, sane->evth_template_path);
   strcat(evth_path, evt_num);
}

void CherenkovInOut_photons_path(
   struct CherenkovInOut* sane, 
   int event_number, 
   char* photons_path
) {
   char evt_num[1024];
   sprintf(evt_num, "%d", event_number);
   strcpy(photons_path, sane->photon_block_template_path);
   strcat(photons_path, evt_num);
}

void CherenkovInOut_assign_observation_level(
   struct CherenkovInOut* sane, 
   cors_real_t runh[273]
) {
   sane->observation_level = runh[4 + (int)runh[4]];
   double oht = sane->observation_level;
   sane->speed_of_light_in_air_on_observation_level = 
      VACUUM_SPEED_OF_LIGHT/refidx_(&oht);
}

void CherenkovInOut_write_runh(
   struct CherenkovInOut* sane, 
   cors_real_t runh[273]
) {
   CherenkovInOut_assign_observation_level(sane, runh);
   CherenkovInOut_write_readme(sane);
   FILE* out;
   out = fopen(sane->runh_path, "wb");
   fwrite(&runh, sizeof(cors_real_t), 273, out);
   fclose(out);  
}

void CherenkovInOut_assign_time_offset(
   struct CherenkovInOut* sane, 
   cors_real_t evth[273]
) {
   double z_first_interaction = evth[6];
   double zenith_angle = evth[10];
   double t = 0.0;
   if(z_first_interaction < 0.0)
      sane->time_offset = (heigh_(&t)-sane->observation_level) / cos(zenith_angle) / VACUUM_SPEED_OF_LIGHT;
   else// Time is counted since first interaction.
      sane->time_offset = (z_first_interaction - sane->observation_level) / cos(zenith_angle) / VACUUM_SPEED_OF_LIGHT;  
}

void CherenkovInOut_write_evth(
   struct CherenkovInOut* sane, 
   cors_real_t evth[273], 
   int event_number
) {
   CherenkovInOut_assign_time_offset(sane, evth);
   char evth_path[1024];
   CherenkovInOut_evth_path(sane, event_number, evth_path);
   FILE* out;
   out = fopen(evth_path, "wb");
   CherenkovInOut_assert_file_is_open(sane, out, evth_path);
   fwrite(&evth, sizeof(cors_real_t), 273, out);
   fclose(out);  
}

void CherenkovInOut_open_photon_block(
   struct CherenkovInOut* sane, 
   int event_number
) {
   char photons_path[1024];
   CherenkovInOut_photons_path(sane, event_number, photons_path);
   sane->current_photons = fopen(photons_path, "wb"); 
   CherenkovInOut_assert_file_is_open(sane, sane->current_photons, photons_path);
}

void CherenkovInOut_append_photon(
   struct CherenkovInOut* sane, 
   struct Photon* photon
) {
   fwrite(photon, sizeof((*photon)), 1, sane->current_photons);
}

void CherenkovInOut_close_photon_block(struct CherenkovInOut* sane) {
   fclose(sane->current_photons); 
}

#endif // __CherenkovInOut_H_INCLUDED__ 