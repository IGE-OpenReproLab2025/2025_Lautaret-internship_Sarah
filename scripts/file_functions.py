import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import glob
from pandas import Series, DataFrame, Timedelta
from matplotlib.dates import DateFormatter, DayLocator, HourLocator, MonthLocator
import xarray as xr


def read_csv_station(file_dir, annee, station):
    """Read the data of meteo France station file and put it in a DataFrame

    Get the data and create a datetime index DataFrame

    """
    file = file_dir+annee+'_'+station+'_jour.csv'
    df = pd.read_csv(file, sep = '\t')
    df['DATE'] = pd.to_datetime(df['DATE'], format='%Y%m%d')
    df.set_index('DATE', inplace=True)
    df = df.add_suffix('_'+station, axis=1)
    return df


def read_csv_lautaret(file_dir, annee) : 
    """Read the data from Flux'Alp station clean file

    Get the data and create a datetime index DataFrame

    """
    file = file_dir+annee+'_Lautaret_halfhour.csv'
    df = pd.read_csv(file, index_col=False)
    if annee in ['2022-2023', '2023-2024'] :
        df['datetime'] = pd.to_datetime(df['Unnamed: 0'])
        df['Unnamed: 0'] = pd.to_datetime(df['Unnamed: 0'])
        df.set_index('datetime', inplace=True)
    else :
        df['datetime'] = pd.to_datetime(df['TIMESTAMP'])
        df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'])
        df.set_index('datetime', inplace=True)
    return df


def make_no_snow_filter(albedo):
    """ Filter the grass from snow depth using albedo

    Filter created by dda, returns a serie where there should be no snow
    Create a smooth albedo to detect the no_snow period
    And then need to fill up the last time slot of the DataFrame
    
    """
   
    albedo_smooth = (albedo.resample('d').median()
                          .rolling(3,center=True,closed='both').median()
                          .rolling(3,center=True,closed='both').mean()
                          .bfill()
                     )
    
    albedo_smooth[albedo_smooth.index[-1]
                  +Timedelta('1D')-Timedelta('30min')] = albedo_smooth.iloc[-1]
    albedo = albedo_smooth.resample('30min').asfreq().interpolate(method='linear')
    
    no_snow = albedo<0.35
    return no_snow


def snow_accumulation(snow_depth) :
    """ Calculation of snow accumulation based on snow depth

    Returns the snow diff of a row with the other and the snow accumulation 
    
    """
    snow_diff = snow_depth.diff()
    snow_acc = snow_diff
    (snow_acc < 0) == 0
    return snow_diff, snow_acc


def densite_crocus(temp, vent):
    """ Calcul of freshly fallen snow density with crocus formula based on air temperature and wind speed

    """
    densite = 109 + 6*(temp) + 26*(vent**0.5)
    return densite


def catch_efficiency_unshield(temperature, wind) :
    """ Calcul catch efficieny for unshielded rain gauge

    Returns the effiency coefficient (between 0 and 1) based on the air temperature and wind speed
    Biblio : https://hess.copernicus.org/articles/21/3525/2017/ , Analysis of single-Alter-shielded and unshielded measurements of mixed and solid precipitation from WMO-SPICE, Kochendorfer (2017a) 

    """
    wind_speed = wind.copy()
    a = 0.0785
    b = 0.729
    c = 0.407
    for i, value in enumerate(wind_speed) :
        if value > 7.2 :
            wind_speed.iloc[i] = 7.2
    ce = np.exp(-(a*wind_speed)*(1-np.arctan(b*temperature)+c))
    return ce


def catch_efficiency_single_alter(temperature, wind) : 
    """ Calcul catch efficieny for a rain gauge with a single alter

    Returns the effiency coefficient (between 0 and 1) based on the air temperature and wind speed
    Biblio : https://hess.copernicus.org/articles/21/3525/2017/ , Analysis of single-Alter-shielded and unshielded measurements of mixed and solid precipitation from WMO-SPICE, Kochendorfer (2017a) 

    """
    wind_speed = wind.copy()
    a = 0.0348
    b = 1.366
    c = 0.779
    for i, value in enumerate(wind_speed) :
        if value > 7.2 :
            wind_speed.iloc[i] = 7.2
    ce = np.exp(-(a*wind_speed)*(1-np.arctan(b*temperature)+c))
    return ce

def convert_relativH_to_speH(relativ_H,temp_K, Patm_Pa) : 
    """Convert the relative humidity (%) into specific humidity (g/kg)

    Use the formulation of Clausius-Clapeyron to calculate the saturation vapour pressure. 
    Which is then used to calculate the water vapor pressure in the air, and with the atmospheric pressure come back to the specific pressure.

    """
    L_v = 2257000         # J/kg
    T3 = 273.16           # Triple point Temp.
    R_wat = 8.32/0.018    # Perfect gas constant/Molar mass of water vapour

    P_satvap = 611*np.exp(L_v*(1/T3 - 1/temp_K)/R_wat)   
    P_watvap = relativ_H/100*P_satvap
    speH = 0.622*P_watvap/(Patm_Pa-P_watvap)
    return speH


def calcule_date_from_iteration_PF(iteration, date_start, date_end):
    """ Calculate the date from an iteration point

    Return the date when giving an iteration of Parflow (30min) with the start and end of the temporal serie

    """
    date_start = date_start+' 00:00:00'
    date_end = date_end+' 23:30:00'

    dates = pd.date_range(date_start, date_end, freq ='30min')
    df = pd.DataFrame({'date' : dates})

    return str(df.at[iteration-1, 'date'])

def calcule_iteration_from_date_PF(date, date_start, date_end):
    """ Calculate the iteration point from a date

    Return the iteration point (step 30min) when giving a date with the start and end of the temporal serie

    """
    date_start = date_start+' 00:00:00'
    date_end = date_end+' 23:30:00'

    dates = pd.date_range(date_start, date_end, freq ='30min')
    df = pd.DataFrame({'date' : dates})

    it = list(range(1,len(df)+1,1))
    df['num_iteration'] = it
    
    return int(df.loc[df['date']== date, 'num_iteration'])




def plot_compare_alb_forcing(simuold, simunew, obs=None, date_start=None, date_end=None) :
    """ Plot used to compare albedo from two different simulations (source's code changed or not) with observed temperature, precip and snow depth (observed and simulated)

    
    """
    fig, ax = plt.subplots(4,figsize=(15,8), sharex=True, gridspec_kw={'height_ratios': [3, 1, 1,1.5]})

    if date_start == None :
        date_start, date_end = simuold.date_start, simuold.date_end
    dur = slice(date_start,date_end)
    
    obs.alb_process.resample(time='D').mean().sel(time=dur).plot(ax = ax[0], label='Albedo observed', color = '#6b20aa') #.sel(time = '2008')    
    simuold.clm.alb_process.resample(time='D').mean().sel(time=dur).plot(ax = ax[0],label='Old albedo simulated', color = '#f1968d') #.sel(time = '2008')
    simunew.clm.alb_process.resample(time='D').mean().sel(time=dur).plot(ax = ax[0],label='New albedo simulated', color = '#8b0d00')
    ax[0].set_ylim([0,1])
    ax[0].xaxis.set_major_locator(MonthLocator(bymonth=[1,2,3,4,5,6,7,8,9,10,11,12]))
    ax[0].set_ylabel('Albedo')

    P = simuold.forc.P.resample(time = 'D').sum().sel(time=dur)*30*60
    T = simuold.forc.T.resample(time = 'D').mean().sel(time=dur) - 273.15

    #Précipitations
    P.plot(ax = ax[1], label = 'Precipitations', color='#011977')
    ax[1].set_ylabel('Precipitations\n (mm/j)', fontsize = 10)
    
    #Température
    T.plot(ax = ax[2], label = 'Temperature', color='#eb9109')
    ax[2].set_ylabel('Temperature\n (°C)', fontsize = 10)

    #Hauteur de neige
    obs.Snow_Depth.resample(time='D').max().sel(time=dur).plot(ax=ax[3], label ='Snow depth observed', color='#70ba04')
    simuold.clm.snow_depth.resample(time='D').max().sel(time=dur).plot(ax=ax[3], label ='Old snow depth simulated', color='#82cdca')
    simunew.clm.snow_depth.resample(time='D').max().sel(time=dur).plot(ax=ax[3], label ='New snow depth simulated', color='#13afaf')
    ax[3].set_ylabel('Snow depth (m)', fontsize = 10)
    
    
    for ca in ax :
        ca.legend(loc ="upper right")
        ca.set_xlabel("")
        ca.set_title("")
        ca.set_xlim(pd.Timestamp(date_start),pd.Timestamp(date_end))
        ca.grid(color='grey', linestyle=':', linewidth=1)
        
    plt.suptitle(date_end[:4]+" : Albedo comparison and meteo forcings", fontsize = 18, fontweight='bold')
    plt.subplots_adjust(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0.2, hspace=0.05)