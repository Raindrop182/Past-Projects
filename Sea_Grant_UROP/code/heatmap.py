from enum import Enum
import pandas as pd
import glob
from datetime import datetime
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import NullFormatter
import numpy as np
#%%
csv_path = r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/fakedata10years.csv"
output_path= r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/"

class DataType(Enum):
    #the variable names in the CSV file
    DIAT = "diatoms_hirata"
    DINO = "dinoflagellates_hirata"
    GREEN = "greenalgae_hirata"
    PRYM = "prymnesiophytes_hirata"

NAMES={DataType.DIAT:"Diatoms",DataType.DINO:"Dinoflagellates",DataType.GREEN:"Green Algae",DataType.PRYM:"Prymnesiophytes"}

def read_csv(csv_path: str) -> pd.DataFrame:
    """Reads csv file as dataframe object
    """
    
    #search for the row that contains all the variable names
    with open(csv_path, 'r') as f:
        numLinesBeforeHeader=0  
        for line in f:
            if line.startswith('date'): 
                header_row=line
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
    """Converts list of datetime objects to list of datetime years
    """
    years=[]
    for date in dates:
        if date.year not in years:
            years.append(date.year)
            
    return years

def createDatesDict(dates,years):
    """Creates dictionary with keys that are years
    Each year corresponds to a list of month-day time objects
    
    Params:
        dates: list of datetime objects
        years: list of datetime years
    """
    dates_dict={year: [] for year in years}
    for date in dates:
        dates_dict[date.year].append(date.replace(year=2000))
    return dates_dict

def extract_data(df: pd.DataFrame, allData,years):
    """save data from each region for each plankton type, by year
    """
    df['date'] = pd.to_datetime(df['date'])
    
    for regionNum in range(1,5,1):
        mask=(df['region']==regionNum)
        region_df=df.loc[mask] #selects only the data corresponding to the region
        
        for year in years:
             year_mask = region_df['date'].dt.year == year
             year_df = region_df.loc[year_mask]
             for plankton_type in DataType:
                 allData[regionNum][plankton_type][year].extend(year_df[plankton_type.value+"_avg"].tolist())

def heat_map(region, plankton_type,allData,dates_dict,save):
    """creates heat_map for a specific plankton type in a specific region over all the dates
    """
    fig, ax = plt.subplots(figsize=(14, 8))
    years = sorted(dates_dict.keys())
    
    data_grid = np.full((len(years), 12), np.nan)
    
    for year_idx, year in enumerate(years):
        dates  = pd.to_datetime(dates_dict[year])      
        values = np.array(allData[region][plankton_type][year])
        
        for month in range(1, 13):
            mask = (dates.month == month)
            if mask.sum() > 0:
                data_grid[year_idx, month-1] = values[mask].mean()
                
    im = ax.imshow(data_grid,
               cmap='YlGnBu',       
               aspect='auto',
               vmin=0, vmax=1,
               interpolation='nearest',
               origin='lower')  
    
    #write numerical concentration in center
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
                 "Monthly average concentration as fraction of Chlorophyll-a",
                 fontsize=16, pad=20)
    ax.set_ylabel("Year", fontsize=14)
    ax.set_xlabel("Month", fontsize=14)
    
    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.set_label("Fraction of Chlorophyll-a", rotation=270, labelpad=20, fontsize=12)
    
    ax.set_xticks(np.arange(-0.5, 12.5), minor=True)
    ax.set_yticks(np.arange(-0.5, len(years), 1), minor=True)
    ax.grid(which='minor', color='white', linestyle='-', linewidth=1.5)
    ax.tick_params(which='minor', size=0)
    
    plt.tight_layout()
    
    if save:
        fig.savefig(output_path + "heatmap.png", dpi=300, bbox_inches="tight")

if __name__ == '__main__':
    if not os.path.exists(csv_path):
        print("No CSV files found in the folder.")
    else:
        df=read_csv(csv_path)
        
        #generate x axis (dates)
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in df['date'].unique()]
        years=extractYears(dates)
        dates_dict=createDatesDict(dates,years)
                    
        allData={}
        for i in range(1,5):
            allData[i]={DataType.DIAT:{year: [] for year in years},DataType.DINO:{year: [] for year in years},DataType.GREEN:{year: [] for year in years},DataType.PRYM:{year: [] for year in years}}
        
        extract_data(df,allData,years)
        
        region=1
        plankton_type=DataType.DIAT
        heat_map(region,plankton_type,allData,dates_dict,save=True)
            
        
                    