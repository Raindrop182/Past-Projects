from enum import Enum
import pandas as pd
import glob
from datetime import datetime
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import NullFormatter
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
    years=[]
    for date in dates:
        if date.year not in years:
            years.append(date.year)
            
    return years

def createDatesDict(dates,years):
    dates_dict={year: [] for year in years}
    for date in dates:
        dates_dict[date.year].append(date.replace(year=2000))
    return dates_dict

def extract_data(df: pd.DataFrame, allData,years):
    df['date'] = pd.to_datetime(df['date'])
    
    for regionNum in range(1,5,1):
        mask=(df['region']==regionNum)
        region_df=df.loc[mask] #selects only the data corresponding to the region
        
        for year in years:
             year_mask = region_df['date'].dt.year == year
             year_df = region_df.loc[year_mask]
             for plankton_type in DataType:
                 allData[regionNum][plankton_type][year].extend(year_df[plankton_type.value+"_avg"].tolist())
                 
def lineGraph10lines(region,plankton_type,allData,dates_dict,save):
    fig, ax = plt.subplots(figsize=(16, 6)) 
    fig.supylabel("Concentration as Fraction of Chlorophyll-A",x=0.06)
    ax.set_ylim(0,1)
    ax.set_title("Region "+f"{region}"+f" {NAMES[plankton_type]}")
        
    cmap = plt.get_cmap('tab10')
    for i,year in enumerate(dates_dict.keys()):
        color=cmap(i / len(years))
        ax.plot(dates_dict[year], allData[region][plankton_type][year], marker='o', linestyle='-', color=color,label=str(year))
    
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonthday=1))      # tick marks
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonthday=15))     # label positions
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
    ax.tick_params(which='minor', length=0)   # hide minor tick marks
    ax.tick_params(which='major', length=4)   # keep major tick marks

    # Rotate month names
    plt.setp(ax.get_xticklabels(which='minor'), rotation=45, ha='center')
    ax.xaxis.set_major_formatter(NullFormatter())
    
    ax.legend(title='Year', loc='upper right',bbox_to_anchor=(1.3, 1), ncol=2)  # ncol=2 if many years
    
    start_of_year = datetime(2000, 1, 1)
    end_of_year = datetime(2000, 12, 31)
    ax.set_xlim(start_of_year, end_of_year)
    
    fig.text(0.92,0.3,"The graphs represent an annual view of\naverage concentrations different\nspecies of plankton over a 10 year period\nin 4 distinct regions around Massachusetts.\nData is taken from NASA’s Landsat 8 Satellite, \nwhich passes over Massachusetts every 16 days. \nEach dot represents one day of collected data,\nbut some days are omitted because of \ncloud cover or no data collected. ", fontsize=12, ha="left",color="black")

    
    if save:
        fig.savefig(output_path+"plot.png",bbox_inches="tight")
        
def lineGraph5lines(region,plankton_type,allData,dates_dict,save):
    fig= plt.figure(figsize=(16, 6)) 
    fig.supylabel("Concentration as Fraction of Chlorophyll-A",x=0.5)
    fig.suptitle("Region "+f"{region}"+f" {NAMES[plankton_type]}")
    

    
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122,sharey=ax1)
        
    cmap = plt.get_cmap('tab10')
    
    left_years=list(dates_dict.keys())[:len(years) // 2]
    right_years=list(dates_dict.keys())[len(years) // 2:]

    
    for i,year in enumerate(left_years):
        color=cmap(i)
        ax1.plot(dates_dict[year], allData[region][plankton_type][year], marker='o', linestyle='-', color=color,label=str(year))
    
    for i,year in enumerate(right_years):
        color=cmap(5+i)
        ax2.plot(dates_dict[year], allData[region][plankton_type][year], marker='o', linestyle='-', color=color,label=str(year))
    
    for ax in [ax1,ax2]:
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonthday=1))      # tick marks
        ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonthday=15))     # label positions
        ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
        ax.tick_params(which='minor', length=0)   # hide minor tick marks
        ax.tick_params(which='major', length=4)   # keep major tick marks

        # Rotate month names
        plt.setp(ax.get_xticklabels(which='minor'), rotation=45, ha='center')
        ax.xaxis.set_major_formatter(NullFormatter())
            
        start_of_year = datetime(2000, 1, 1)
        end_of_year = datetime(2000, 12, 31)
        ax.set_xlim(start_of_year, end_of_year)
    
    ax1.legend(title='Year', loc='upper left',bbox_to_anchor=(-0.42, 1), ncol=2)  # ncol=2 if many years
    ax2.legend(title='Year', loc='upper right',bbox_to_anchor=(1.42, 1), ncol=2)  # ncol=2 if many years
    fig.text(0.92,0.3,"The graphs represent an annual view of\naverage concentrations different\nspecies of plankton over a 10 year period\nin 4 distinct regions around Massachusetts.\nData is taken from NASA’s Landsat 8 Satellite, \nwhich passes over Massachusetts every 16 days. \nEach dot represents one day of collected data,\nbut some days are omitted because of \ncloud cover or no data collected. ", fontsize=12, ha="left",color="black")

        
    if save:
        fig.savefig(output_path+"plot.png",bbox_inches="tight")
        
if __name__ == '__main__':
    if not os.path.exists(csv_path):
        print("No CSV files found in the folder.")
    else:
        df=read_csv(csv_path)
        
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in df['date'].unique()]
                
        years=extractYears(dates)
        dates_dict=createDatesDict(dates,years)
                    
        allData={}
        for i in range(1,5):
            allData[i]={DataType.DIAT:{year: [] for year in years},DataType.DINO:{year: [] for year in years},DataType.GREEN:{year: [] for year in years},DataType.PRYM:{year: [] for year in years}}
        
        extract_data(df,allData,years)
        
        region=1
        plankton_type=DataType.DIAT
        
        lineGraph10lines(region,plankton_type,allData,dates_dict,save=True)
        # lineGraph5lines(region,plankton_type,allData,dates_dict,save=True)
            
        