import pandas as pd
import numpy as np
from pandas import Series, DataFrame, Timedelta


def calculate_length_gap(serie):
    """ Calculation of gap's length in a datetime serie's data

    Returns a datetime serie with the length of the gap following the datetime index

    """
    serie_nan = serie.isna()
    nan_cumsum = serie_nan.apply(int).diff().abs().cumsum()
    only_nan = nan_cumsum.loc[serie_nan==True].reset_index()
    
    col_date, col_values = only_nan.columns
    len_gap = only_nan.groupby(only_nan[col_values]).agg({col_date:'min', col_values :len})
    return len_gap.set_index(col_date)


def half_hour_mean_value(serie):
    """  Create a monthly mean day-cycle from a serie of multiple years

    Return a multiIndex serie : level 0 = month (from 1 to 12), level 1 = half-hour monthly mean 
    
    """
    mean_value = serie.groupby([serie.index.month, serie.index.time]).mean()
    return mean_value


def mean_value_maker(df):
    """ Create a function that gets a value from a specific serie at a specific hour

    df here is the monthly mean day-cycle
    dt is the specific hour to get
    
    """
    def mean_value(dt):
        dt = pd.to_datetime(dt)
        m = dt.month
        t = dt.time()
        out = df.loc[t]     
        return out
    return mean_value


def calcul_trend(serie) :  
    """ Calculation of the line trend of a !!! 24h serie !!!

    Returns the line trend serie of a time serie, base time is in minutes

    """
    a = (serie.iloc[-1] - serie.iloc[0])/1410    #(1410 = amount of minutes from 00:00 to 23:30)
    if np.isnan(a):
        a = 0
    b = serie.iloc[0]
    if np.isnan(b):
        b = 0   #serie.mean()
    
    time = pd.to_datetime(serie.index.astype(str), format = 'mixed', yearfirst=True, utc = True)
    t = pd.Series([t.seconds for t in np.diff(np.array(time))]).cumsum().div(60)
    y = t.mul(a).add(b)
    y = pd.concat([pd.Series(b),y]).reset_index(drop=True)
    return y


def trend_removal(mean):   
    """  Remove the line trend in a serie
    
    !!! Need to use a 24h serie to calcul the trend !!!
    Returns a serie without a line trend ==> a serie with a mean equals to zero
    
    """
    idx = mean.index
    mean_trend = calcul_trend(mean)
    mean = mean.reset_index(drop=True)
    mean_corr = mean.sub(mean_trend) 
    mean_corr.index = pd.DatetimeIndex(idx.astype(str)).time
    return mean_corr


## Returns a serie of the datetime gap start and a second serie of the datetime gap end
def get_serie_missing_values(serie):
    """ Get the start datetime index and end datetime index of the gaps in a list

    Returns a list for the gap start and another one for the gap end

    """
    gap_start = serie.loc[serie.isna().astype(int).diff() == 1]
    gap_start = serie.loc[gap_start.index - pd.Timedelta(30, unit='min')]
    gap_end = serie.loc[serie.isna().astype(int).diff() == -1]
    return gap_start, gap_end

## Function that fills the gaps in 
## , does'nt create a copy
def gap_filling(df, col, no_b=None):
    """ Function that fills the gaps in a column of a dataframe

    Method : 
    --------
    
    # 1 - Get a list of the start dates and end dates of the gaps
    For each gaps :
    # 2 - Get the monthly mean day-cycle and remove the line trend
    # 3 - Adjust the mean day-cycle of the adjacent values of the gap (right before and right after the gap)
            Special condition possible :: 
                - No adjusting : no added biais (for SW down variable)
 ### TO REVIEW  - Condition for long gap (~24h that starts around the max of the mean-day-cycle) : the biais equals to the mean of adjacent value - the max of the mean monthly day-cycle
    
    Returns the same dataframe gap filled with the monthly mean day-cycle adjusted
    
    """

    start, end = get_serie_missing_values(df[col])
    mean = half_hour_mean_value(df[col])

    r = -1
    for i, x in start.items():
        r = r +1

        month = i.month
        mean_corr = trend_removal(mean[month])

        b = (x + end.iloc[r])/2

        ## special condition if the gap is big and starting approximately around noon ==> the biais can't be only the mean of the value adjacente
        ## get the biais equals to the mean of adjacent value - the max of the mean monthly day-cycle
        if (pd.to_datetime(end.index[r]) - pd.to_datetime(str(i))) > pd.Timedelta(18,unit='h') and (str(i.time()) in ['11:00:00', '11:30:00', '12:00:00', '12:30:00', '13:00:00', '13:30:00', '14:00:00']):
            b = b - mean_corr.max()

        if no_b == True:
            b = 0
        
        mean_adjusted = mean_corr.add(b)
        get_mean_value = mean_value_maker(mean_adjusted)

        serie = df.loc[str(i):end.index[r],col]
        for row, value in serie.items() :
            serie.loc[row] = get_mean_value(row)
        df.loc[serie.index,col] = serie
    return df[col]


def no_precip(serie):
    """Function that replace NaN values with zeros

    Used to fill gaps where there is no precipitation

    """
    serie.loc[serie.isna()] = 0
    return serie