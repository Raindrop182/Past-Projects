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
    """
    Extract unique years from a list of datetime-like objects.
    """
    years=[]
    for date in dates:
        if date.year not in years:
            years.append(date.year)
            
    return years

def extract_data(df: pd.DataFrame, allData,years):
    """
    Populate a nested data structure with plankton data grouped by region, 
    year, and plankton type.
    """
    for regionNum in range(1,5,1):
        mask=(df['region']==regionNum)
        region_df=df.loc[mask] #selects only the data corresponding to the region
        
        for year in years:
             year_mask = region_df['date'].dt.year == year
             year_df = region_df.loc[year_mask] #selects only data corresponding to the year
             
             for plankton_type in PlanktonType:
                 allData[regionNum][plankton_type][year].extend(year_df[plankton_type.value+"_avg"].tolist())
                 
def get_x_values(year: list,region_df: pd.DataFrame):
    """
    Extract and normalize date values for a specific year within a region's 
    DataFrame.
    """
    year_mask = region_df['date'].dt.year == year
    year_df = region_df.loc[year_mask]
    normalized_dates = year_df['date'].apply(lambda d: d.replace(year=2000))
    return normalized_dates

def format_month_axis(ax):
    """Format X-axis for monthly datetime plotting."""
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonthday=1)) #sets tick mark at start of month
    ax.tick_params(which='major', length=4)
    ax.xaxis.set_major_formatter(NullFormatter()) #set no labels at the start of the month

    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonthday=15)) #sets month label at middle of month
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
    ax.tick_params(which='minor', length=0) #no tick marks in the middle of the month
    
    #rotate month labels so they fit
    plt.setp(ax.get_xticklabels(which='minor'), rotation=45, ha='center')
    
def lineGraphAllLines(region: int, plankton_type: PlanktonType,allData: dict,years:list,save:bool):
    """
    Plot a multi-year line graph of concentration of chlorophyll-a for a 
    specific region and plankton type.

    This function creates a single line plot where each line corresponds to 
    one year of data. Dates are normalized to the year 2000 so all years 
    can be visually compared on the same seasonal cycle.
    """
    fig, ax = plt.subplots(figsize=(16, 6)) 
    fig.supylabel("Chlorophyll-A Concentration (mg per m^3)",x=0.06)
    ax.set_ylim(0,1)
    ax.set_title("Region "+f"{region}"+f" {NAMES[plankton_type]}")
    
    mask=(df['region']==region)
    region_df=df.loc[mask] #selects only the data corresponding to the region
    
    cmap = plt.get_cmap('tab20')
    for i,year in enumerate(years):
        color=cmap(i / len(years))
        
        x_values=get_x_values(year,region_df)
        
        ax.plot(x_values, allData[region][plankton_type][year], marker='o', linestyle='-', color=color,label=str(year))
    
    format_month_axis(ax)
    
    ax.legend(title='Year', loc='upper right',bbox_to_anchor=(1.3, 1), ncol=2)  # ncol=2 if many years
    
    start_of_year = datetime(2000, 1, 1)
    end_of_year = datetime(2000, 12, 31)
    ax.set_xlim(start_of_year, end_of_year)
    
    if save:
        fig.savefig(output_path+"samplelinegraph-all.png",bbox_inches="tight")
        
def lineGraphHalfLines(region,plankton_type,allData,years,save):
    fig= plt.figure(figsize=(16, 6)) 
    fig.supylabel("Chlorophyll-A Concentration (mg per m^3)",x=0.5)
    fig.suptitle("Region "+f"{region}"+f" {NAMES[plankton_type]}")
    
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122,sharey=ax1)
        
    cmap = plt.get_cmap('tab20')
    
    left_years=years[:len(years) // 2]
    right_years=years[len(years) // 2:]
    
    mask=(df['region']==region)
    region_df=df.loc[mask] #selects only the data corresponding to the region

    for i,year in enumerate(left_years):
        x_values=get_x_values(year,region_df)
        color=cmap(i)
        ax1.plot(x_values, allData[region][plankton_type][year], marker='o', linestyle='-', color=color,label=str(year))
    
    for i,year in enumerate(right_years):
        x_values=get_x_values(year,region_df)
        color=cmap(5+i)
        ax2.plot(x_values, allData[region][plankton_type][year], marker='o', linestyle='-', color=color,label=str(year))
    
    for ax in [ax1,ax2]:
        format_month_axis(ax)
            
        start_of_year = datetime(2000, 1, 1)
        end_of_year = datetime(2000, 12, 31)
        ax.set_xlim(start_of_year, end_of_year)
        ax.set_ylim(0,1)
    
    ax1.legend(title='Year', loc='upper left',bbox_to_anchor=(-0.42, 1), ncol=2)  # ncol=2 if many years
    ax2.legend(title='Year', loc='upper right',bbox_to_anchor=(1.42, 1), ncol=2)  # ncol=2 if many years
        
    if save:
        fig.savefig(output_path+"samplelinegraph-half.png",bbox_inches="tight")
        
if __name__ == '__main__':
    if not os.path.exists(csv_path):
        print("No CSV files found in the folder.")
    else:
        df=read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'])

        years=extractYears(df['date'])
                    
        allData={}
        for i in range(1,5):
            allData[i]={
                PlanktonType.DIAT:{year: [] for year in years},
                PlanktonType.DINO:{year: [] for year in years},
                PlanktonType.GREEN:{year: [] for year in years},
                PlanktonType.PRYM:{year: [] for year in years}
            }
        
        extract_data(df,allData,years)
        
        region=1
        plankton_type=PlanktonType.DIAT
        lineGraphAllLines(region,plankton_type,allData,years,save=True)
        lineGraphHalfLines(region,plankton_type,allData,years,save=True)
        