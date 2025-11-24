import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from enum import Enum
import glob
import os
#%%
csv_path = r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/fakedata10years_interesting.csv"
output_path= r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/"

class DataType(Enum):
    #the variable names in the CSV file
    DIAT = "diatoms_hirata"
    DINO = "dinoflagellates_hirata"
    GREEN = "greenalgae_hirata"
    PRYM = "prymnesiophytes_hirata"
    
COLORS={"other":(207/255, 255/255, 223/255),DataType.DIAT:(126/255, 33/255, 148/255),DataType.DINO:(255/255, 156/255, 17/255),DataType.GREEN:(0/255, 210/255, 0),DataType.PRYM:(0/255, 95/255, 185/255)}

##############
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

def extract_data(df: pd.DataFrame):
    allData={}
    allData[DataType.DIAT]=[]
    allData[DataType.DINO]=[]
    allData[DataType.GREEN]=[]
    allData[DataType.PRYM]=[]
    
    all_dates = df['date'].unique()
    n_dates = len(all_dates)
    date_to_idx = {date: i for i, date in enumerate(sorted(all_dates))} #maps each date to an index
    
    region=df['region']
    for region_num in range(1,5,1):
        mask=(region==region_num)
        region_df = df.loc[mask].copy()        
       
        full_diat  = np.full(n_dates, -1.0)
        full_dino  = np.full(n_dates, -1.0)
        full_green = np.full(n_dates, -1.0)
        full_prym  = np.full(n_dates, -1.0)
        
        indices = region_df['date'].map(date_to_idx).values
                    
        full_diat[indices]  = region_df[DataType.DIAT.value  + "_avg"].values 
        full_dino[indices]  = region_df[DataType.DINO.value  + "_avg"].values
        full_green[indices] = region_df[DataType.GREEN.value + "_avg"].values
        full_prym[indices] = region_df[DataType.PRYM.value + "_avg"].values
        
        allData[DataType.DIAT].append(full_diat) 
        allData[DataType.DINO].append(full_dino)
        allData[DataType.GREEN].append(full_green)
        allData[DataType.PRYM].append(full_prym)
    return allData

def generate_bar_graph(data,dates,save):
    """generates bar graph displaying plankton concentration in each region
    """
    fig=plt.figure(figsize=(50,12))
    fig.subplots_adjust(hspace=0.5)
    fig.suptitle("\n Phytoplankton Composition of Total Chlorophyll-a 2013 to 2020", fontsize=14, fontweight='bold')
    
    fig.supylabel("Concentration as Fraction of Chlorophyll-A",x=0.1)
    #graphs the data for each region
    for region in range(1,5,1):
        ax=fig.add_subplot(4,1,region)
        ax.set_ylim(0,1)
        ax.set_title("Region "+f"{region}")
        bottom = np.zeros(len(df['date'].unique()))
        x_axis=np.arange(1,len(bottom)+1)
        
        #create x-axis with dates
        if region==4:
            ax.set_xticks(x_axis)
            ax.set_xticklabels(dates,rotation=90)
        else:
            ax.xaxis.set_visible(False)
        
        #graph the data for each plankton type
        for plankton_type in DataType:
            height=np.array(data[plankton_type][region-1])
            
            valid = height >= 0                            
            missing = height < 0
            
            ax.bar(x_axis[valid],height[valid],bottom=bottom[valid], color=COLORS[plankton_type], label=plankton_type.value, linewidth=0.3)
            for i in np.where(valid)[0]:
                if height[i] > 0:
                    r, g, b = COLORS[plankton_type][:3]
                    ax.text(x_axis[i], bottom[i] + height[i] / 2, f"{height[i]:.2f}", ha='center', va='center', fontsize=8, color="white" if (0.299*r + 0.587*g + 0.114*b) < 0.4 else "black")
            bottom[valid]+=height[valid]
        

        
        #Fills the remainder to 1
        ax.bar(x_axis,[min(1,1-i) for i in bottom],hatch = '/',bottom=bottom, color=COLORS["other"], label="other", linewidth=0.3)
        
        ax.bar(x_axis[missing], 1.0, color='gray', alpha=0.7,label="No data")


    ax.legend(bbox_to_anchor=(1.1, 6),loc="upper right")

    if save:
        fig.savefig(output_path+"myplot.png",bbox_inches="tight")
    
##############
if __name__ == '__main__':    
    if not os.path.exists(csv_path):
        print("No CSV files found in the folder.")
    else:
        df=read_csv(csv_path)
        
        dates = df['date'].unique()
        
        data=extract_data(df)
        
        generate_bar_graph(data,dates,save=True)
    
#%%
