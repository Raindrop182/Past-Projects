import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from enum import Enum
import re
from datetime import datetime
import glob

folder_path = r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/"

class DataType(Enum):
    #the variable names in the CSV file
    DIAT = "diatoms_hirata"
    DINO = "dinoflagellates_hirata"
    GREEN = "greenalgae_hirata"
    PRYM = "prymnesiophytes_hirata"
    
COLORS={"other":(207/255, 255/255, 223/255),DataType.DIAT:(126/255, 33/255, 148/255),DataType.DINO:(255/255, 156/255, 17/255),DataType.GREEN:(0/255, 210/255, 0),DataType.PRYM:(0/255, 95/255, 185/255)}

##############
def get_dates(csv_paths: list[str]) -> list[datetime]:
    """Retrieve dates from file path names
    
    Args:
        csv_paths: list of strings of paths to csv files
    
    Returns:
        list of date objects
    """
    dates = []
    for csv_path in csv_paths:
        date=re.search(r'(\d{4}-\d{2}-\d{2})',csv_path) #expects file path containing {YYYY}-{MM}-{DD}.csv
        if not date:
            raise ValueError(csv_path+"does not contain expected pattern: YYYY-MM-DD.csv")
        date=datetime.strptime(date.group(0),"%Y-%m-%d") #turn string date into date object
        date=date.strftime('%Y-%m-%d')
        dates.append(date) 
    return dates

def read_csv(csv_path: str) -> pd.DataFrame:
    """Reads csv file as dataframe object
    """
    
    #search for the row that contains all the variable names
    with open(csv_path, 'r') as f:
        numLinesBeforeHeader=0  
        for line in f:
            if line.startswith('featureId'): 
                header_row=line
                break
            else:
                numLinesBeforeHeader+=1
        else:
            raise ValueError(f"Header row starting with 'featureId' not found in {csv_path}")
    
    #read in the csv file, starting with the row that contains all the variable names
    df = pd.read_csv(csv_path,sep=' ',skiprows=numLinesBeforeHeader,header=0,comment='#',on_bad_lines='skip')
    df.columns=[c.split(':')[0] for c in df.columns]
        
    return df

def sort_data(df: pd.DataFrame) -> dict:
    """Extracts data for each region and plankton type from dataframe
    
    Args:
        df: dataframe object
    
    Returns:
        dictionary with 4 keys (diatoms, dinoflagellates, green algae, pyrmnesiophytes)
        the value of each dict object is a list of 4 lists
        each of the 4 lists represents the data values from 1 region (the 1st list repesents region 1, 2nd list region 2, etc)
    """
    csv_data={}
    csv_data[DataType.DIAT]=[]
    csv_data[DataType.DINO]=[]
    csv_data[DataType.GREEN]=[]
    csv_data[DataType.PRYM]=[]
    
    region=df['region']
    for regionNum in range(1,5,1):
        mask=(region==regionNum)
        region_df=df.loc[mask,[dt.value for dt in DataType]] #selects only the data corresponding to the region
        
        csv_data[DataType.DIAT].append([i for i in region_df[DataType.DIAT.value] if i>0]) #i>0 ensures no bad data is selected
        csv_data[DataType.DINO].append([i for i in region_df[DataType.DINO.value] if i>0])
        csv_data[DataType.GREEN].append([i for i in region_df[DataType.GREEN.value] if i>0])
        csv_data[DataType.PRYM].append([i for i in region_df[DataType.PRYM.value] if i>0])
    
    return csv_data

def compress_data_to_avgs(csv_data: dict) -> dict:
    """calculates avg values in each region for each plankton type
    
    Args:
        csv_data: dictionary with 4 keys (corresponding to 4 plankton types)
        the value of each dict object is a list of 4 lists
        each of the 4 lists represents data values from a region
        
    Returns:
        dictionary with 4 keys
        the value of each dict object is a list of 4 lists
        each list contains 1 vlaue, the average value from that region
    """
    for plankton_type in csv_data.keys():
        for i in range (0,len(csv_data[plankton_type]),1):
            if len(csv_data[plankton_type][i])==0:
                avg_value=0
            else:
                avg_value=sum(csv_data[plankton_type][i])/len(csv_data[plankton_type][i])
            csv_data[plankton_type][i]=avg_value
    return csv_data

def reformat_data_for_bar_graph(all_data: list) -> dict:
    """Rearranges data to be used to make a bar graph
    Input is sorted by date -> plankton -> region
    Output is sorted by plankton -> region -> date
    """
    reformatted_data={}
    reformatted_data[DataType.DIAT]=[[],[],[],[]]
    reformatted_data[DataType.DINO]=[[],[],[],[]]
    reformatted_data[DataType.GREEN]=[[],[],[],[]]
    reformatted_data[DataType.PRYM]=[[],[],[],[]]
    
    for day_dict in all_data:
        for region in range(0,4,1):
            for plankton_type in day_dict.keys():
                reformatted_data[plankton_type][region].append(day_dict[plankton_type][region])
    
    return reformatted_data
    

def generate_bar_graph(data_from_all_dates,dates,save):
    """generates bar graph displaying plankton concentration in each region
    
    args: data_from_all_dates is a list with many dictionaries. each dictionary corresponds to a different date
    in each dictionary, each key correponds to a plankton type
    each key corresponds to a list of 4 lists
    each of the 4 lists contains the avg value from a region
    """
    fig=plt.figure(figsize=(10,12))
    fig.subplots_adjust(hspace=0.5)
    fig.suptitle("\n Phytoplankton Composition of Total Chlorophyll-a 2013 to 2020", fontsize=14, fontweight='bold')

    data=reformat_data_for_bar_graph(data_from_all_dates)
    
    fig.supylabel("Conentration as Fraction of Chlorophyll-A")
    
    #graphs the data for each region
    for region in range(1,5,1):
        ax=fig.add_subplot(4,1,region)
        ax.set_ylim(0,1)
        ax.set_title("Region "+f"{region}")
        bottom = np.zeros(len(data_from_all_dates))
        x_axis=np.arange(1,len(bottom)+1)
        
        #create x-axis with dates
        if region==4:
            ax.set_xticks(x_axis)
            ax.set_xticklabels(dates_sorted)
        else:
            ax.xaxis.set_visible(False)
        
        #graph the data for each plankton type
        for plankton_type in DataType:
            height=data[plankton_type][region-1]
            ax.bar(x_axis,height,bottom=bottom, color=COLORS[plankton_type], label=plankton_type.value, linewidth=0.3)
            for i in range(len(x_axis)):
                if height[i] > 0:
                    ax.text(x_axis[i], bottom[i] + height[i] / 2, f"{height[i]:.2f}", ha='center', va='center', fontsize=8)
            bottom+=height
        
        #Fills the remainder to 1
        ax.bar(x_axis,[min(1,1-i) for i in bottom],hatch = '/',bottom=bottom, color=COLORS["other"], label="other", linewidth=0.3)
        
    ax.legend(bbox_to_anchor=(1.3, 6),loc="upper right")

    if save:
        fig.savefig(folder_path+"myplot.png",bbox_inches="tight")
    
##############
if __name__ == '__main__':
    csv_paths = glob.glob(folder_path + "*.csv")  # Find all .csv files in the folder
    print("Found CSV files:", csv_paths)
    
    if csv_paths:  # Check if any CSVs were found
        dates = get_dates(csv_paths)
        
        dates_sorted, csv_paths_sorted = zip(*sorted(zip(dates, csv_paths))) #sort the csvs by date
        dates_sorted = list(dates_sorted)
        csv_paths_sorted = list(csv_paths_sorted)
        
        data_from_all_dates=[]
        for csv_path in csv_paths: #reads in every csv
            data=read_csv(csv_path)
            data=sort_data(data)
            data=compress_data_to_avgs(data)
            data_from_all_dates.append(data)
            
        generate_bar_graph(data_from_all_dates,dates_sorted,save=True)
    else:
        print("No CSV files found in the folder.")
    
