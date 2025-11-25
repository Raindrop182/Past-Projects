from enum import Enum
import pandas as pd
import glob
import re
import os

#%%
folder_path = r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/fakedata/"
output_path= r"C:/Users/raine/Data/School/MIT/Freshman Year/UROP/CSV/lyze/"

class DataType(Enum):
    #the variable names in the CSV file
    DIAT = "diatoms_hirata"
    DINO = "dinoflagellates_hirata"
    GREEN = "greenalgae_hirata"
    PRYM = "prymnesiophytes_hirata"
    
def get_dates(csv_paths: list[str]) -> list[str]:
    """Retrieve dates from file path names
    
    Args:
        csv_paths: list of strings of paths to csv files
    
    Returns:
        list of strings of dates
    """
    dates = []
    for csv_path in csv_paths:
        date=re.search(r'(\d{4}-\d{2}-\d{2})',csv_path) #expects file path containing {YYYY}-{MM}-{DD}.csv
        if not date:
            raise ValueError(csv_path+"does not contain expected pattern: YYYY-MM-DD.csv")
        dates.append(date.group(0)) 
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

def avgValue(data: list) -> int:
    """returns avg value of a list
    """
    if len(data)==0:
        avg_value=0
    else:
        avg_value=sum(data)/len(data)
    return avg_value

def extract_data(df: pd.DataFrame, data: list[dict], date):
    """
    """
    for region_num in range(1,5,1):
        mask=(df['region']==region_num)
        region_df=df.loc[mask,[dt.value for dt in DataType]] #selects only the data corresponding to the region
        
        plankton_data={}
        for plankton_type in DataType:
            plankton_data[plankton_type.value+"_avg"]=avgValue([i for i in region_df[plankton_type.value] if i>0])
            plankton_data[plankton_type.value+"_max"]=max([i for i in region_df[plankton_type.value] if i>0])
            plankton_data[plankton_type.value+"_min"]=min([i for i in region_df[plankton_type.value] if i>0])

        row = {
            'date': date,
            **plankton_data,
            'region': float(region_num)
        }
        data.append(row)
    
def write_csv_file(data, path):
    """Write CSV data to file"""
    if not data:
        return

    df = pd.DataFrame(data)
    
    variables=[]
    for plankton_type in DataType:
        variables.append(plankton_type.value+"_avg")
        variables.append(plankton_type.value+"_max")
        variables.append(plankton_type.value+"_min")

    column_order = ['date'] + variables + ['region']
    df = df[column_order]

    header_row = "date " + " ".join([f"{var}:float" for var in variables])+ " region:float"

    with open(path, 'w') as f:
        f.write(f"{header_row}\n")
        df.to_csv(f, sep=' ', index=False, header=False, float_format='%.8f')

if __name__ == '__main__':
    csv_paths = glob.glob(folder_path + "*.csv")  # Find all .csv files in the folder
    print("Found CSV files:", csv_paths)
    
    if csv_paths:  # Check if any CSVs were found
        dates = get_dates(csv_paths)
        
        dates_sorted, csv_paths_sorted = zip(*sorted(zip(dates, csv_paths))) #sort the csvs by date
        dates_sorted = list(dates_sorted)
        csv_paths_sorted = list(csv_paths_sorted)
        
        data=[]
        for i,csv_path in enumerate(csv_paths):
            extract_data(read_csv(csv_path),data,dates[i])
        
        # csv_filename = f"{dates_sorted[0]}-to-{dates_sorted[-1]}.csv"
        csv_filename=f"alldata.csv"
        csv_save_path = os.path.join(output_path, csv_filename)
        write_csv_file(data,csv_save_path)
   
        
    else:
        print("No CSV files found in the folder.")