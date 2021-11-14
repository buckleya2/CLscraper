import numpy as np
import os
import pandas as pd
import re
import shutil

def exist_or_make(path: str) -> None:
    """
    Function that checks for existance of required directories and creates them if they don't exist
    
    @param path: path to a directory required by script
    @returns: creates directories, returns nothing 
    """
    if not os.path.isdir(path):
        os.makedirs(path)
        
def create_paths(base_path: str) -> list:
    """
    Function that takes in a base path and outputs directories for data and log files
    
    @param base_path: base output path for files
    @returns a list with: log_path, database_path, and file_path
    """
    log_path=os.path.join(base_path, 'logs')
    database_path=os.path.join(base_path, 'database')
    file_path=os.path.join(base_path, 'post_text')
    out=[log_path, database_path, file_path]
    [exist_or_make(x) for x in out]
    return(out)

def check_database(database_path: str) -> tuple:
    """
    Function that checks status of current database file, and backs up current database file
    
    @param database_path: file path of database file
    @returns: tuple of pd.DataFrame, list of all craigslist post ID in database, errors out if database file provided is < 2 lines long
    """
    with open(database_path,"r") as f:
        count = len(f.readlines())
    if count < 2:
        return('Compare main database file to backup before proceeding')
    else:
        backup=database_path.replace('/database','/database/backup')
        shutil.copy(database_path, backup)
        # read in current database
        DB=pd.read_csv(database_path, sep='\t')
        database=DB['index'].tolist()
        return(DB, database)

def get_first(values: list):
    """
    Function that takes in a list and returns the first value (and the .text attribute if it exists), otherwise returns nothing
    
    @param values: list that contains 0-many results
    @returns: the first item of the list or None
    """
    out=None
    if len(values) > 0:
        out=values[0]
        if out.text:
            out=out.text.strip()
    return(out)

def generate_search_urls(stem: str, max_res: int) -> list:
    """
    Function that generates a list of craigslist URLs for each page of the search defined in stem 
    
    @param stem: a base craiglist URL describing a rental search
    @param max_res: the total number of search results (determined by search_links())
    @returns: a list of URLs for each page of a craiglist search
    """
    ## generate urls to grab all results
    search_limit=120
    url_list=[]
    if max_res > search_limit:
        for i in range(1, int(np.floor(max_res/120))+1):
            num=search_limit * i
            link=stem + '&s=' + str(num)
            url_list.append(link)
    return(url_list)

def filter_spam(df):
    """
    Function that takes in the craigslist database pd.DataFrame and subsets to likely real postings
    
    @param df: pd.DataFrame output by make_output()
    @returns: pd.DataFrame with spam listings removed
    """
    spam_bool=((df.num_images > 2) & (df.scam == False) & \
               (df.emoji < 2) & (~df.property_management.astype(str).str.contains('www|http')) & \
               (pd.notnull(df.latitude)) & (df.dog != 'no'))
    clean=df[spam_bool]
    return(clean)
