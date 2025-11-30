from enum import Enum
import pandas as pd
import glob
from datetime import datetime
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import NullFormatter
import matplotlib.colors as mcolors
import numpy as np
#%%
csv_path = r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/samples/11-29/mock_plankton_data.csv"
output_path= r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/samples/11-29/"

class PlanktonType(Enum):
    #the variable names in the CSV file
    DIAT = "diatoms_hirata"
    DINO = "dinoflagellates_hirata"
    GREEN = "greenalgae_hirata"
    PRYM = "prymnesiophytes_hirata"

NAMES={
    PlanktonType.DIAT:"Diatoms",
    PlanktonType.DINO:"Dinoflagellates",
    PlanktonType.GREEN:"Green Algae",
    PlanktonType.PRYM:"Prymnesiophytes"
}

COLORS = {
    PlanktonType.DIAT: (126/255, 33/255, 148/255),
    PlanktonType.DINO: (255/255, 156/255, 17/255),
    PlanktonType.GREEN: (0/255, 210/255, 0),
    PlanktonType.PRYM: (0/255, 95/255, 185/255),
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

def extractYears(dates: list):
    """Extracts unique years from a list of date objects, in the order they appear"""
    years=[]
    for date in dates:
        if date.year not in years:
            years.append(date.year)
    return years

def createDatesDict(dates,years):
    """Organizes a list of date objects into a dictionary keyed by year, 
    normalizing each date to a reference year (2000)
    """
    dates_dict={year: [] for year in years}
    for date in dates:
        dates_dict[date.year].append(date.replace(year=2000))
    for year in dates_dict.keys():
        dates_dict[year].sort()
    return dates_dict

def extract_data(df: pd.DataFrame, allData,dates_dict):
    """Populates a nested data structure with plankton concentration values, organized 
    by region, plankton type, and year."""   
    for regionNum in range(1,5,1):
        mask=(df['region']==regionNum)
        region_df=df.loc[mask].copy() #selects only the data corresponding to the region
        
        region_df['date'] = pd.to_datetime(region_df['date'])
        
        for year in dates_dict.keys():
            all_dates = dates_dict[year]
            date_to_idx = {date: i for i, date in enumerate(sorted(all_dates))} #maps each date to an index

            year_mask = region_df['date'].dt.year == year
            year_df = region_df.loc[year_mask]
            for plankton_type in PlanktonType:
                full_list = np.full(len(all_dates), np.nan)
                
                normalized_dates = year_df['date'].apply(lambda d: d.replace(year=2000))
                indices = normalized_dates.map(date_to_idx).values
                
                full_list[indices] = year_df[plankton_type.value  + "_avg"].values 
                
                allData[regionNum][plankton_type][year].extend(full_list.tolist())

def heat_map(region, plankton_type,allData,dates_dict,save):
    "creates a heat map of chlorophyll-a concentration attributed to a specific type of plankton in a specific region, over time"
    fig, ax = plt.subplots(figsize=(14, 8))
    years = sorted(dates_dict.keys())
    
    data_grid = np.full((len(years), 12), np.nan)
    
    for year_idx, year in enumerate(years):
        dates  = pd.to_datetime(dates_dict[year])      
        values = np.array(allData[region][plankton_type][year])

        for month in range(1,13):
            mask = (dates.month == month)
            if mask.sum() > 0:
                data_grid[year_idx, month-1] = values[mask].mean() #if there are multiple datapoints from a month, average them
    
    #range of colors of heatmap is from white to color defined in COLORS dictionary
    cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", [(1, 1, 1), COLORS[plankton_type]])
    im = ax.imshow(data_grid,
               cmap=cmap,     
               aspect='auto',
               vmin=0, vmax=0.6, #TODO: choose max value for heatmap
               interpolation='nearest',
               origin='lower')  
    
    #write numerical value in center of each datapoint
    for i in range(len(years)):
        for j in range(12):
            if not np.isnan(data_grid[i, j]):
                text_color = "white" if data_grid[i, j] > 0.5 else "black"
                
                ax.text(j, i, f"{data_grid[i, j]:.3f}",
                        ha='center', va='center',
                        fontsize=10,
                        color=text_color,
                        fontweight='bold')
    
    ax.set_yticks(np.arange(len(years)))
    ax.set_yticklabels(years)
    
    ax.set_xticks(np.arange(12))
    ax.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun',
                        'Jul','Aug','Sep','Oct','Nov','Dec'])
    
    ax.set_title(f"Region {region} – {NAMES[plankton_type]}\n"
                 "Monthly average Chlorophyll-a concentration",
                 fontsize=16, pad=20)
    ax.set_ylabel("Year", fontsize=14)
    ax.set_xlabel("Month", fontsize=14)
    
    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Chlorophyll-a Concentration (mg per m^3)", rotation=270, labelpad=20, fontsize=12)
    
    ax.set_xticks(np.arange(-0.5, 12.5), minor=True)
    ax.set_yticks(np.arange(-0.5, len(years), 1), minor=True)
    ax.grid(which='minor', color='white', linestyle='-', linewidth=1.5)
    ax.tick_params(which='minor', size=0)
    
    plt.tight_layout()
    
    if save:
        fig.savefig(output_path + "sampleheatmap.png", dpi=300, bbox_inches="tight")

if __name__ == '__main__':
    if not os.path.exists(csv_path):
        print("No CSV files found in the folder.")
    else:
        df=read_csv(csv_path) #read in csv to pandas dataframe object
        
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in df['date'].unique()] #create list of unique dates
                
        years=extractYears(dates) #obtain list of unique years
        dates_dict=createDatesDict(dates,years) #sort each month/day date object into its corresponding year in a dictionary
        
        #create empty dictionary, where keys are the numbers 1-4, representing the 4 regions
        #each region corresponds to a dictionary sorted by plankton type, and then year
        allData={}
        for i in range(1,5):
            allData[i]={
                    PlanktonType.DIAT:{year: [] for year in years},
                    PlanktonType.DINO:{year: [] for year in years},
                    PlanktonType.GREEN:{year: [] for year in years},
                    PlanktonType.PRYM:{year: [] for year in years}
            }
        
        extract_data(df,allData,dates_dict) #populate allData with the informatino from the pandas dataframe
        
        region=1
        plankton_type=PlanktonType.DIAT
        heat_map(region,plankton_type,allData,dates_dict,save=True)
            
        
                    