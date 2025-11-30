import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import numpy as np
from enum import Enum
import glob
import os
#%%
csv_path = r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/samples/11-29/mock_plankton_data.csv"
output_path= r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/samples/11-29/"
max_y_lim=0.7

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

def generate_trendline(plankton_type: PlanktonType,df: pd.DataFrame,save: bool):
    """Generate a multi-region trendline plot for a given plankton type.

    This function creates a 4-panel figure (one subplot per region) showing:
      - the minimum–maximum chlorophyll concentration range (shaded band),
      - the average concentration trendline,
      - gray intervals where no data exists for a region.
    """
    dates = np.sort(pd.to_datetime(df['date'].unique())) #unique ordered dates along the x-axis

    fig=plt.figure(figsize=(10,9))
    
    fig.supylabel("Chlorophyll-A Concentration",x=0.01)
    fig.suptitle(f" {NAMES[plankton_type]}")
    
    data=extract_data(df,plankton_type)
    for region_num in range(1,5):
        plt.subplot(4, 1, region_num)
        
        min_values=data[region_num-1]['min']
        max_values=data[region_num-1]['max']
        avg_values=data[region_num-1]['avg']
        
        nan_indices = np.isnan(avg_values)
        valid_indices = ~nan_indices
        
        #plot max min range
        plt.fill_between(dates[valid_indices], min_values[valid_indices], max_values[valid_indices], color='lightblue', alpha=0.75, label='Min-Max Range')

        #plot trendline
        plt.plot(dates[valid_indices], avg_values[valid_indices], label='Trendline', color='blue', marker='o', markersize=5, markerfacecolor='black')
        
        #plot gray bars for no data days
        for d in dates[nan_indices]:
            plt.axvspan(d - pd.Timedelta(days=3), d + pd.Timedelta(days=3),
                        color='gray', alpha=0.3,
                        label='No data' if region_num==1 else "")
        
        plt.ylim(0, max_y_lim)
        plt.ylabel("mg/m^3", fontsize=12)
        
        #only plot xtick marks on the bottom subplot
        if region_num != 4:
            plt.tick_params(axis='x', labelbottom=False)
            
        plt.title("Region " + str(region_num))
    
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(20)) #plot year-month for ~20 dates along the x-axis  
    plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m'))  

    plt.xticks(rotation=45)
    plt.tight_layout(rect=[0, 0.08, 1, 0.96])
    
    plt.figlegend(["Min-Max Range","Trendline","Cloudy/Insufficient Data"], loc='lower center', ncol=3, fontsize=10)
    plt.show()

    if save:
        fig.savefig(output_path+"sampletrendline.png",bbox_inches="tight")
    
##############
if __name__ == '__main__':    
    if not os.path.exists(csv_path):
        print("No CSV files found in the folder.")
    else:
        df=read_csv(csv_path)
                                
        plankton_type=PlanktonType.DIAT
        generate_trendline(plankton_type,df,save=True)
