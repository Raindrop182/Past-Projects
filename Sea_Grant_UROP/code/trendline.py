import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
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

NAMES={DataType.DIAT:"Diatoms",DataType.DINO:"Dinoflagellates",DataType.GREEN:"Green Algae",DataType.PRYM:"Prymnesiophytes"}
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

def extract_data(df: pd.DataFrame,plankton_type):
    data=[]

    
    all_dates = df['date'].unique()
    n_dates = len(all_dates)
    date_to_idx = {date: i for i, date in enumerate(sorted(all_dates))}
    
    region=df['region']
    for region_num in range(1,5,1):
        region_dict={}
        
        mask=(region==region_num)
        region_df = df.loc[mask].copy()        
       
        full_avg  = np.full(n_dates, np.nan)
        full_q1  = np.full(n_dates, np.nan)
        full_q3  = np.full(n_dates, np.nan)
        
        indices = region_df['date'].map(date_to_idx).values
                    
        full_avg[indices]  = region_df[plankton_type.value  + "_avg"].values
        full_q1[indices]  = region_df[plankton_type.value  + "_min"].values
        full_q3[indices]  = region_df[plankton_type.value  + "_max"].values

        region_dict['avg']=np.array(full_avg)
        region_dict['q1']=np.array(full_q1)
        region_dict['q3']=np.array(full_q3)

        data.append(region_dict)
    return data

def generate_trendline(plankton_type,df,save):
    """
    """
    dates = pd.to_datetime(df['date'].unique())

    fig=plt.figure(figsize=(10,9))
    
    fig.supylabel("Concentration as Fraction of Chlorophyll-A",x=0.01)
    fig.suptitle(f" {NAMES[plankton_type]}")
    
    data=extract_data(df,plankton_type)
    for region_num in range(1,5):
        plt.subplot(4, 1, region_num)
        q1_values=data[region_num-1]['q1']
        q3_values=data[region_num-1]['q3']
        avg_values=data[region_num-1]['avg']
        
        nan_indices = np.isnan(avg_values)
        valid_indices = ~nan_indices
        
        print(q1_values[valid_indices])
        plt.fill_between(dates[valid_indices], q1_values[valid_indices], q3_values[valid_indices], color='lightblue', alpha=0.75, label='Min-Max Range')

        plt.plot(dates[valid_indices], avg_values[valid_indices], label='Trendline', color='blue', marker='o', markersize=5, markerfacecolor='black')
        
        for d in dates[nan_indices]:
            plt.axvspan(d - pd.Timedelta(days=3), d + pd.Timedelta(days=3),
                        color='gray', alpha=0.3,
                        label='No data' if region_num==1 else "")
        
        plt.ylim(0, 1)
        plt.ylabel("mg/m^3", fontsize=12)
        
        if region_num != 4:
            plt.tick_params(axis='x', labelbottom=False)
        plt.title("Region " + str(region_num))
            
    plt.gca().xaxis.set_major_locator(plt.MaxNLocator(20))   
    plt.gca().xaxis.set_major_formatter(DateFormatter('%Y-%m'))  

    plt.xticks(rotation=45)
    plt.tight_layout(rect=[0, 0.08, 1, 0.96])
    
    plt.figlegend(["Trendline", "Min-Max Range", "Cloudy/Insufficient Data"], loc='lower center', ncol=3, fontsize=10)
    plt.show()

    if save:
        fig.savefig(output_path+"myplot.png",bbox_inches="tight")
    
##############
if __name__ == '__main__':    
    if not os.path.exists(csv_path):
        print("No CSV files found in the folder.")
    else:
        df=read_csv(csv_path)
                                
        plankton_type=DataType.DIAT
        generate_trendline(plankton_type,df,save=True)
