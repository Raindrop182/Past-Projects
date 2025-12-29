import pandas as pd
import numpy as np
from enum import Enum
import glob
import os
import math
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
from matplotlib.ticker import FormatStrFormatter, NullFormatter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
#%%
csv_path = r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/samples/12-28/alldata100bins.csv"
output_path= r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/samples/12-28/"

class PlanktonType(Enum):
    #the variable names in the CSV file
    DIAT = "diatoms_hirata"
    DINO = "dinoflagellates_hirata"
    GREEN = "greenalgae_hirata"
    PRYM = "prymnesiophytes_hirata"
    
COLORS = {
    PlanktonType.DIAT: (126/255, 33/255, 148/255),
    PlanktonType.DINO: (255/255, 156/255, 17/255),
    PlanktonType.GREEN: (0/255, 210/255, 0),
    PlanktonType.PRYM: (0/255, 95/255, 185/255),
}

NAMES={
    PlanktonType.DIAT:"Diatoms",
    PlanktonType.DINO:"Dinoflagellates",
    PlanktonType.GREEN:"Green Algae",
    PlanktonType.PRYM:"Prymnesiophytes"
}

def read_csv(csv_path: str) -> pd.DataFrame:
    """Reads csv file as dataframe object
    """
    #search for the row that contains all the variable names
    with open(csv_path, 'r') as f:
        numLinesBeforeHeader=0  
        for line in f:
            if line.startswith('date'): 
                break
            else:
                numLinesBeforeHeader+=1
        else:
            raise ValueError(f"Header row starting with 'date' not found in {csv_path}")
    
    #read in the csv file, starting with the row that contains all the variable names
    df = pd.read_csv(csv_path,sep=' ',skiprows=numLinesBeforeHeader,header=0,comment='#',on_bad_lines='skip')
    df.columns=[c.split(':')[0] for c in df.columns]
        
    return df

def extract_data(df: pd.DataFrame,plankton_type: PlanktonType):
    """Extract and align chlorophyll-related plankton data across all regions
    for a single plankton type.

    This function takes a DataFrame containing date-stamped plankton 
    measurements and returns a list of region-specific dictionaries. 
    Each dictionary contains NumPy arrays of the average, minimum, and 
    maximum chlorophyll values aligned to a common date index. Missing 
    values for dates with no observations in a region are filled with NaN.
    """
    data=[]
    
    all_dates = df['date'].unique()
    n_dates = len(all_dates)
    date_to_idx = {date: i for i, date in enumerate(sorted(all_dates))} #map each date to an index
    
    region=df['region']
    for region_num in range(1,5,1):
        region_dict={}
        
        mask=(region==region_num)
        region_df = df.loc[mask] #only select data from that region        
       
        full_avg  = np.full(n_dates, np.nan)
        full_min  = np.full(n_dates, np.nan)
        full_max  = np.full(n_dates, np.nan)
        
        indices = region_df['date'].map(date_to_idx).values #map each date from data in the region to an index
                    
        full_avg[indices]  = region_df[plankton_type.value  + "_avg"].values 
        full_min[indices]  = region_df[plankton_type.value  + "_min"].values
        full_max[indices]  = region_df[plankton_type.value  + "_max"].values

        region_dict['avg']=np.array(full_avg)
        region_dict['min']=np.array(full_min)
        region_dict['max']=np.array(full_max)

        data.append(region_dict)
    return data

def max_range(data):
    """
    returns the largest difference between the maximum and average across all the regions
    """
    max_range=0
    for region_num in range(1,5):
        max_values=data[region_num-1]['max']
        avg_values=data[region_num-1]['avg']
        max_range=max(max_range,max(max_values)-np.mean(avg_values))
    return max_range

def generate_trendline(plankton_type: PlanktonType,df: pd.DataFrame,save: bool):
    """Generate a multi-region trendline plot for a given plankton type.

    This function creates a 4-panel figure (one subplot per region) showing:
      - the minimum–maximum chlorophyll concentration range (shaded band),
      - the average concentration trendline,
      - gray intervals where no data exists for a region.
    """
    dates = np.sort(pd.to_datetime(df['date'].unique())) #unique ordered dates along the x-axis
    
    n_months = len(pd.period_range(dates.min(), dates.max(), freq='M'))
    width_per_month = 0.75 #defines how spaced apart each data point is
    fig_width = max(10, n_months * width_per_month)

    data=extract_data(df,plankton_type) 
    
    if max_range(data)>2: #if the max data points are much larger than the avg data points, split the y-axis
        broken_axis=True
        fig, axs = plt.subplots(
        4*2, 1, sharex=True,
        gridspec_kw={'height_ratios':[1,2]*4, 'hspace':0.2}, 
        figsize=(fig_width, 12))
    else:
        broken_axis=False
        fig, axs = plt.subplots(
        4, 1, sharex=True,
        gridspec_kw={'height_ratios':[1]*4, 'hspace':0.2}, 
        figsize=(fig_width, 12))           
        
    fig.supylabel("Chlorophyll-A Concentration",x=0.1)
    fig.suptitle(f" {NAMES[plankton_type]}",fontsize=20)
    
    for i, region_num in enumerate(range(1,5)):
        if broken_axis:
            ax_top = axs[i*2]
            ax_bottom = axs[i*2 + 1]
        else:
            ax_top=ax_bottom=axs[i]
        
        min_values=data[region_num-1]['min']
        max_values=data[region_num-1]['max']
        avg_values=data[region_num-1]['avg']
        
        nan_indices = np.isnan(avg_values)
        valid_indices = ~nan_indices
        
        ax_top.yaxis.set_major_formatter(FormatStrFormatter('%.2f')) #show only 2 decimal places on the y axis
        ax_bottom.yaxis.set_major_formatter(FormatStrFormatter('%.2f')) #show only 2 decimal places on the y axis}
            
        if broken_axis:
            # --- Top subplot: zoomed on max values ---
            ax_top.fill_between(dates[valid_indices], min_values[valid_indices], max_values[valid_indices], alpha=0.5, color='lightblue')
            ax_top.set_ylim(max(avg_values[valid_indices])*1.2, max(max_values[valid_indices]*1.2)  )
            ax_top.spines['bottom'].set_visible(False)
            ax_top.tick_params(bottom=False)
            
            # --- Bottom subplot: zoomed on average and min ---
            ax_bottom.fill_between(dates[valid_indices], min_values[valid_indices], max_values[valid_indices], alpha=0.5, color='lightblue')
            ax_bottom.plot(dates[valid_indices], avg_values[valid_indices], color='blue', marker='o',linewidth=2)
            ax_bottom.set_ylim(0, max(avg_values[valid_indices])*1.2) 
            ax_bottom.spines['top'].set_visible(False)
    
            # Add diagonal lines to indicate broken axis
            d = .015  # size of diagonal lines
            kwargs = dict(transform=ax_top.transAxes, color='k', clip_on=False)
            ax_top.plot((-d,+d), (-d,+d), **kwargs)        # top-left diagonal
            ax_top.plot((1-d,1+d), (-d,+d), **kwargs)      # top-right diagonal
            kwargs.update(transform=ax_bottom.transAxes)  # switch to bottom axes
            ax_bottom.plot((-d,+d), (1-d,1+d), **kwargs)  # bottom-left diagonal
            ax_bottom.plot((1-d,1+d), (1-d,1+d), **kwargs) # bottom-right diagonal
        
        else:            
            #plot max min range
            ax_top.fill_between(dates[valid_indices], min_values[valid_indices], max_values[valid_indices], color='lightblue', alpha=0.5)

            #plot trendline
            ax_top.plot(dates[valid_indices], avg_values[valid_indices], label='Trendline', color='blue', marker='o', markersize=5, markerfacecolor='black')
            
            ax_top.set_ylim(0,max(max_values[valid_indices])*1.2)
        
        #remove tick marks from all but the bottom axis of region 4
        if region_num!=4:
            ax_bottom.tick_params(axis='x', which='both',labelbottom=False, length=0)
            ax_top.tick_params(axis='x', which='both',labelbottom=False, length=0)
        else:
            if broken_axis:
                ax_top.tick_params(axis='x', which='both',labelbottom=False, length=0)
                        
        #plot gray bars for no data days
        for d in dates[nan_indices]:
            ax_top.axvspan(d - pd.Timedelta(days=3), d + pd.Timedelta(days=3),
                        color='gray', alpha=0.3)
            if broken_axis:
                ax_bottom.axvspan(d - pd.Timedelta(days=3), d + pd.Timedelta(days=3),
                        color='gray', alpha=0.3)

        ax_top.set_ylabel("mg/m^3", fontsize=12, y=-0.5 if broken_axis else 0.5, labelpad=15)
        ax_top.set_title("Region " + str(region_num),x=1.1,y=-0.5 if broken_axis else 0.5)

    ax_bottom.xaxis.set_minor_locator(mdates.MonthLocator()) #sets tick mark at start of month
    ax_bottom.xaxis.set_minor_formatter(NullFormatter()) #set no labels at the start of the month
    ax_bottom.tick_params(axis='x',which='minor', length=8)

    ax_bottom.xaxis.set_major_locator(mdates.MonthLocator(bymonthday=15)) #sets month label at middle of month
    ax_bottom.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax_bottom.tick_params(which='major', length=0, pad=8) #no tick marks in the middle of the month
    
    #makes the tick mark at January longer and bolder
    minor_ticks = ax_bottom.xaxis.get_minor_ticks()
    minor_locs = ax_bottom.xaxis.get_minorticklocs()  # positions in matplotlib date numbers
    for tick, loc in zip(minor_ticks, minor_locs):
        tick_date = mdates.num2date(loc)
        if tick_date.month == 1:
            tick.tick1line.set_markersize(18)  # bottom tick
            tick.tick1line.set_markeredgewidth(1.5)    # thickness
    
    #write the year underneath the month labels
    dates = pd.to_datetime(df['date'])
    years = list(range(dates.dt.year.min(), dates.dt.year.max()+1))
    year_positions = [pd.Timestamp(year=y, month=6, day=15) for y in years]
    for pos, y in zip(year_positions, years):
        ax_bottom.text(pos, 
                       -0.25,
                       str(y), 
                       ha='center', va='top', 
                       fontsize=12, fontweight='bold', transform=ax_bottom.get_xaxis_transform())
    
    
    legend_elements = [
    Patch(facecolor='lightblue', alpha=0.5, edgecolor='none', label='Min-Max Range'),
    plt.Line2D([0], [0], color='blue', label='Trendline'),
    Patch(facecolor='gray', edgecolor='none', alpha=0.3, label='Cloudy/Insufficient Data')]
    
    plt.figlegend(handles=legend_elements, loc='lower center', ncol=3, fontsize=10)
    plt.show()

    if save:
        fig.savefig(output_path+f"trendline-{plankton_type.value}100bins",bbox_inches="tight")


##############
if __name__ == '__main__':    
    if not os.path.exists(csv_path):
        print("No CSV files found in the folder.")
    else:
        df=read_csv(csv_path)
                                
        for plankton_type in PlanktonType:
            generate_trendline(plankton_type,df,save=True)

