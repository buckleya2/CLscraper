import argparse
import logging

from CLscraper.helpers import *
from CLscraper.lib import *
from CLscraper.maps import *
from CLscraper.email import *
from CLscraper.searches import SEARCH_STEMS

def main():
    # parse command line
    parser=argparse.ArgumentParser(description='CLscraper')
    parser.add_argument('base_path', type=str, nargs=1, help='base output path for files')
    parser.add_argument('api', type=str, nargs=1, help='path to file with Google maps API key')
    parser.add_argument('mailto', type=str, nargs=1, help='email address to send alters to')
    parser.add_argument('gmail_creds', type=str, nargs=1, help='path to Gmail token json file')
    arguments=parser.parse_args()
    base_path=arguments.base_path[0]
    api=arguments.api[0]
    mailto=arguments.mailto[0]
    gmail_creds=arguments.gmail_creds[0]

    # set api key as global variable
    with open(api, 'r') as file:
        api_key=file.read().rstrip()

    # import craigslist search stem URLs from searches.py
    portland_stem=SEARCH_STEMS['portland_house']
    seattle_stem=SEARCH_STEMS['seattle_house']
    
    # first check if requires directories are present, if not, create
    log_path, database_path, file_path=create_paths(base_path)
    # set up logging
    curr_time=datetime.datetime.today().strftime("%d%m%Y_%H:%M")
    logging.basicConfig(filename=os.path.join(log_path, curr_time + '.log.txt'), format='%(message)s    %(asctime)s',
                   level=logging.INFO, filemode='w')

    # check for database file, if not present, create empty database list
    database_file=os.path.join(database_path, 'CL_database.main.txt')
    if not os.path.exists(database_file):
        database=[]
        DB=None
    else:
        DB, database=check_database(database_file)
    
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
            outlist.append(extract_soup(value, key, file_path, api_key))
        except:
            logging.info("Listing ID %s failed" % (key))
            fails+=1
        
    # make dataframe, combine with current database
    out=pd.concat(outlist).reset_index()
    # filter spam and send email alert
    clean=filter_spam(out)
    print("%s non-spam postings" % (len(clean))) 
    email_dict=make_email_dict(clean, CL_dict, api_key)
    print(len(email_dict))
    message=create_email('me', mailto, 'Housing Email Alert', email_dict)
    send_message(gmail_creds, message)
    try:
        FIN=pd.concat([DB, out])
        FIN.to_csv(database_file, sep='\t', index=False)
    except:
        logging.info('database outputs non-conformable, writing new data to %s' % (database_file.replace('main', str(datetime.date.today()))))
        out.to_csv(database_file.replace('main', str(datetime.date.today())), sep='\t', index=False)  
    logging.info("%s listings added to database, %s listings failed" % (len(out), fails))
    return()
