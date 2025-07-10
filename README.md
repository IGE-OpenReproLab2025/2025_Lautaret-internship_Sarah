# Project : Comparison of hydrological models for a better understanding of water ressources

The main goal is to study the water ressources on a small alpin catchment, near the Lautaret's pass, through a hydrological model : ParFlow-CLM. \
The study area is the Charmasses catchment, it covers 15.28 ha and is located in the mid-mountain region at around 2,000 m altitude. The watershed is a gently sloping meadow, snow-covered from November to April, with a predominantly nival hydraulic regime. This catchment is instrumented with the Flux'Alp tower that registers data from the critical zone.

Based on this data, the forcing input file is created. The data series must be cleaned and gapfilled before being implemented in the modele. The data used is the one cleaned by Didier Voisin, here : *https://gricad-gitlab.univ-grenoble-alpes.fr/lautaret/fluxalp/-/tree/master/data_clean_hydro_year?ref_type=heads*.

In this repo, is presented one method to prepare the 1D forcing file for ParFlow-CLM simulations on the Charmasse's catchment.


## Contributors 
Jean-Martial Cohard, Didier Voisin, Alix Reverdy

## Material

- **`notebooks/`** - executable Jupyter notebook
- **`report/`** - one poster presenting the method, one doc of popularization of hydrology modelling
- **`scripts/`** - modules used in the notebook

## Licence
CC0 1.0 Universal
