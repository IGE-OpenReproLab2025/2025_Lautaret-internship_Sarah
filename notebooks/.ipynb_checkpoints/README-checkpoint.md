# Preparation of the forcing inpu file to run ParFlow-CLM on the Charmasses catchment

In this repo you will find one method to prepare the Flux'alp's data to put it in the forcing file of 1D simulation of ParFlow-CLM on the Charmasses's catchment.

This method is applied to the period of the hydrological years 2018-2019 to 2023-2024. The data used is the one cleaned by Didier Voisin, here : *https://gricad-gitlab.univ-grenoble-alpes.fr/lautaret/fluxalp/-/tree/master/data_clean_hydro_year?ref_type=heads*.

The parflow forcing format is : (with the corresponding Flux'alp data below)\
Short wave radiation (W/m2) ; Long wave radiation (W/m2) ; Precipitation (mm/s)    ; Air temperature (K) ; x-direction wind speed (m/s) ; y-direction wind speed (m/s) ; Atmospheric pressure (Pa) ; Specific humidity (kg/kg) \
short_up_Avg (W/m2)         ; long_up_cor_Avg (W/m2)     ; Quantity_raw (mm/30min) ; AirTC_Avg (°C)      ; WindSpeed_Avg (m/s)          ; WindSpeed_Avg (m/s)          ; Patm_Avg (hPa)            ; HRair_Avg (%)

## Contributors 
Author : Sarah Vermaut \
Supervisors : Jean-Martial Cohard, Didier Voisin, Alix Reverdy

## Material
1. Undercatch correction for solid precipitation
In this step, the solid precipitation is corrected with a catchment efficiency coefficient of the gauge depending on meteo conditions (temperature and wind speed). [Kochendorfer, 2017] \
The resulting data of this step is in the file ***/resulting_data/1-Fluxalp_corrected-snow-precip_2018_2024.dat***

2.  Automatic gapfilling
A part of the gaps are filled with an linear interpolation (gaps of 30min to 3h for all variables excpet precipitation for which it's gaps of 30min to 2h). And the longer gaps are filled based on the monthly average daily-cycle, which is unskewed and then adapted to the real data.

3. Manual gapfilling for precipitation
For precippiptation, a special look is necessary. A first step is to locate the gaps and find the one where it's sunny with the Lautaret's webcam to fill the gap with zero precipitation. Then, where there is precipitation, the gap is filled with the precipitation calculated from the crocus density's formula of fresh snow.


4. Observation of data gapfilled, 
Observation of the data that enable a begining of a critic of the method that needs to be persued further

5. Conversion of the data to the Parflow format 
Formatting the data with the last conversions 