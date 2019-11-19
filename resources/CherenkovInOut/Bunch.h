#ifndef __CherenkovInOutBunch_H_INCLUDED__
#define __CherenkovInOutBunch_H_INCLUDED__

//-------------------- Bunch ---------------------------------------------------
struct Bunch{
   float size;
   float x;
   float y;
   float cx;
   float cy;
   float arrival_time;
   float emission_altitude;
   float wavelength;
   float mother_mass;
   float mother_charge;
};

double Bunch_cz(struct Bunch* bunch) {
   return sqrt(1.0 - bunch->cx*bunch->cx - bunch->cy*bunch->cy);
}

double Bunch_slope_x(struct Bunch* bunch) {
   return bunch->cx/Bunch_cz(bunch);
}

double Bunch_slope_y(struct Bunch* bunch) {
   return bunch->cy/Bunch_cz(bunch);
}

void Bunch_to_string(struct Bunch* bunch, char* out) {
   char size_str[1024];
   sprintf(size_str, "%f", bunch->size);

   char x_str[1024];
   sprintf(x_str, "%f", bunch->x);

   char y_str[1024];
   sprintf(y_str, "%f", bunch->y);

   char cx_str[1024];
   sprintf(cx_str, "%f", bunch->cx);

   char cy_str[1024];
   sprintf(cy_str, "%f", bunch->cy);

   char arrival_time_str[1024];
   sprintf(arrival_time_str, "%f", bunch->arrival_time);

   char emission_altitude_str[1024];
   sprintf(emission_altitude_str, "%f", bunch->emission_altitude);

   char wavelength_str[1024];
   sprintf(wavelength_str, "%f", bunch->wavelength);

   char mother_mass_str[1024];
   sprintf(mother_mass_str, "%f", bunch->mother_mass);

   char mother_charge_str[1024];
   sprintf(mother_charge_str, "%f", bunch->mother_charge);

   strcpy(out, "Bunch(");
   strcat(out, "size "); strcat(out, size_str); strcat(out, ", ");
   strcat(out, "x "); strcat(out, x_str); strcat(out, "cm, ");
   strcat(out, "y "); strcat(out, y_str); strcat(out, "cm, ");
   strcat(out, "cx "); strcat(out, cx_str); strcat(out, ", ");
   strcat(out, "cy "); strcat(out, cy_str); strcat(out, ", ");
   strcat(out, "t "); strcat(out, arrival_time_str); strcat(out, "ns, ");
   strcat(out, "z0 "); strcat(out, emission_altitude_str); strcat(out, "cm, ");
   strcat(out, "lambda "); strcat(out, wavelength_str); strcat(out, "nm, ");
   strcat(out, "mother mass "); strcat(out, mother_mass_str); strcat(out, "GeV, ");
   strcat(out, "mother charge "); strcat(out, mother_charge_str);
   strcat(out, ")");
}

void Bunch_warn_if_size_above_one(struct Bunch* bunch) {
   if(bunch->size > 1.0) {
      char bunch_str[4096];
      Bunch_to_string(bunch, bunch_str);
      fprintf(
         stderr, 
         "Warning: Photon bunch size > 1.0 in %s\n", 
         bunch_str
      );
   }
}

int Bunch_reaches_observation_level(
   struct Bunch* bunch,
   double random_uniform_0to1
) {
   return random_uniform_0to1 <= bunch->size;
}

#endif // __CherenkovInOutBunch_H_INCLUDED__ 