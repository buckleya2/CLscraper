import argparse
import logging

from CLscraper.helpers import *
from CLscraper.lib import *
from CLscraper.maps import *
from CLscraper.searches import SEARCH_STEMS

def main():
    # parse command line
    parser=argparse.ArgumentParser(description='CLscraper')
    parser.add_argument('base_path', type=str, nargs=1, help='base output path for files')
    parser.add_argument('api', type=str, nargs=1, help='path to file with Google maps API key')
    arguments=parser.parse_args()
    base_path=arguments.base_path[0]
    api=arguments.api[0]

    # import craigslist search stem URLs from searches.py
    portland_stem=SEARCH_STEMS['portland_house']
    seattle_stem=SEARCH_STEMS['seattle_house']
    
    # first check if requires directories are present, if not, create
    log_path, database_path, file_path=create_paths(base_path)
    # set up logging
    curr_time=datetime.datetime.today().strftime("%d%m%Y_%H:%M")
    logging.basicConfig(filename=os.path.join(log_path, curr_time + '.log.txt'), format='%(message)s    %(asctime)s',
                   level=logging.INFO, filemode='w')
    print(os.path.join(log_path, curr_time + '.log.txt'))
    # check for database file, if not present, create empty database list
    database_file=os.path.join(database_path, 'CL_database.main.txt')
    if not os.path.exists(database_file):
        database=[]
    else:
        database=check_database(database_file)
    
    logging.info('Database currently contains %s listings' % (len(database)))
    # get urls from all posts that match our critera, then subset to those that aren't in our database
    portland_recent_urls=search_links(portland_stem, database)
    seattle_recent_urls=search_links(seattle_stem, database)
    
    logging.info("scraping %s links" % (len(set(portland_recent_urls + seattle_recent_urls))))

    # scrape data for these urls 
    CL_dict=scrape_data(portland_recent_urls + seattle_recent_urls)
    
    # parse soup
    outlist=[]
    fails=0
    for key, value in CL_dict.items():
        try:
            outlist.append(extract_soup(value, key, file_path))
        except:
            logging.info("Listing ID %s failed" % (key))
            fails+=1
        
    # make dataframe, combine with current database
    out=pd.concat(outlist).reset_index()
    try:
        FIN=pd.concat([DB, out])
        FIN.to_csv(database_file, sep='\t', index=False)
    except:
        logging.info('database outputs non-conformable, writing new data to %s' % (database_file.replace('main', str(date.today()))))
        out.to_csv(database_file.replace('main', str(date.today())), sep='\t', index=False)  
    logging.info("%s listings added to database, %s listings failed" % (len(out), fails))
    return()
