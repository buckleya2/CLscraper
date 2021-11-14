import bs4
import datetime
import emoji
import numpy as np
import os
import pandas as pd
import re
import requests
import time

from CLscraper.helpers import *
from CLscraper.maps import *

def scrape_data(url_list: list)-> dict:
    """
    Function that takes in a list of URLs and pulls data from craigslist with a sleep timer from 2-10 seconds
    
    @param url_list: list of craigslist post URLs to scrape
    @returns: a dictionary with URL as key and BeautifulSoup object as the value
    """
    soup_dict={}
    scrape_count=0
    for url in url_list:
        req=requests.get(url)
        content=req.text
        soup=bs4.BeautifulSoup(content)
        soup_dict[url]=soup
        time.sleep(np.random.randint(2,10))
        scrape_count+=1
        if scrape_count % 10 == 0:
            print("%s listings completed / %s total" % (scrape_count, len(url_list)))
    return(soup_dict)

def extract_links(soup_list: list) -> dict:
    """
    Function that extracts individual craiglist posting URLs from a craiglist search URL
    
    @param soup_list: a list of BeautifulSoup objects scraped from craigslist search URLs
    @returns: a dict with the posting ID as the key and posting URL as value
    """
    url_dict={}
    links=[re.findall(r'http[s]?:.*apa.*html', str(soup)) for soup in soup_list]
    flat_links=list(set([item for sublist in links for item in sublist]))
    for link in flat_links:
        url_dict[link.split('/')[-1].split('.')[0]]=link
    return(url_dict)

def search_links(stem: str, database: list) -> dict:
    """
    Function that pulls all individual craigslist post URLs from a base craigslist housing search result
    
    @param stem: a base craiglist URL describing a rental search
    @param database: a list of all CL post ids currently in text database
    @returns:
    """
    # scrape first results page to determine max results
    CL_dict=scrape_data([stem])
    soup=CL_dict[stem]
    max_res=int(get_first(soup.findAll('span', {'class' : 'total'})))
    
    # if multiple pages, get all search result urls
    additional_urls=generate_search_urls(stem, max_res)
    all_urls=[stem] + additional_urls

    # scrape search pages, and extract all listing urls 
    CL_dict_add=scrape_data(all_urls)
    soup_list=list(CL_dict_add.values())
    listing_dict=extract_links(soup_list)
    new_urls=check_new(database, listing_dict)
    return(new_urls)

def count_title_emoji(soup: bs4.BeautifulSoup) -> int:
    """
    Function that counts the number of emojis in the post title
    
    @param soup: BeauftifulSoup object created from a craigslist posting
    @returns: the number of emojis in the posting title
    """
    emojitext=get_first(soup.findAll('title'))
    return(sum([x in emoji.EMOJI_DATA for x in emojitext]))

def parse_posting_info(soup: bs4.BeautifulSoup) -> tuple:
    """
    Function that extracts out post ID and posting time
    
    @param soup: BeauftifulSoup object created from a craigslist posting
    @returns: a tuple with posting ID, posting date, posting update date
    """
    post_info=soup.findAll('p', {'class' : 'postinginfo'})
    post_id, posted, updated=(None, None, None)
    for i in post_info:
        text=i.text
        post_id
        if 'post id' in text:
            post_id=text.split(":")[1].strip()
        elif 'posted' in text:
            posted=text.split(":")[1].strip().split(" ")[0]                   
        elif 'updated' in text:
            updated=text.split(":")[1].strip().split(" ")[0]
    return(post_id, posted, updated)

def get_coords(soup: bs4.BeautifulSoup)-> tuple:
    """
    Function that pulls latitude and longitude coordinates from post
    
    @params soup: BeautifulSoup object created from a craigslist posting
    @returns: a tuple of (latitude, longitude)
    """
    try: 
        map_info=soup.findAll('div', {'class' : 'viewposting'})[0]
        lat=map_info['data-latitude']
        long=map_info['data-longitude']
        return((lat,long))
    except:
        return((None, None))
    
def metrics_from_soup(soup: bs4.BeautifulSoup) -> list:
    """
    This function collects a number of metrics from the post soup object
    lat, long - latitude and longitude
    posting id, posted, updated - when post was created/updated
    price
    available - when is rental available
    size - number of beds and baths
    images - number of images attached to posting
    emoji - number of emojis in post title
    
    @param soup: BeautifulSoup object created from a craigslist posting
    @returns: a list of metrics 
    """
    price=get_first(soup.findAll('span', {'class' : 'price'}))
    available=get_first(soup.findAll('span', {'class' : 'housing_movein_now'}))
    size=get_first(soup.findAll('span', {'class' : 'shared-line-bubble'}))
    images=len(soup.findAll("a", {"class":"thumb"}))
    emoji=count_title_emoji(soup)
    
    posting_id, posted, updated=parse_posting_info(soup)
    lat, long=get_coords(soup)
    return([lat, long, posting_id, posted, updated, price, available, size, images, emoji])

def get_posting_text(soup: bs4.BeautifulSoup) -> str:
    """
    This function extracts the main post text
    
    @param soup: BeautifulSoup object created from a craigslist posting
    @returns: string of post body text
    """
    body_soup=get_first(soup.findAll('section', {'id' : 'postingbody'}))
    if body_soup == None:
        print("no text in posting")
        raise ValueError
    body=body_soup.replace('QR Code Link to This Post' , '').replace('\n' , '')
    return(body)

def property_management(body: str) -> str:
    """
    Function to look for specific property managment companies or web links in post body
    
    @param body: post text stripped from HTML
    @returns: property management name or a web address from the post
    """ 
    company=None
    companies=['tindel','invitation','pathlight','management group', 'lgi homes', 'windermere', 'green keys']
    for c in companies:
        if re.search(c, body.lower()):
            company=c
    if company is None and re.findall(r'(http|www)[s]?', body):
        company="".join([x for x in body.split(" ") if re.search(r'(http|www)[s]?', x.lower())])
    return(company)

def count_caps_words(body: str) -> int:
    """
    Function that counts the number of ALL CAPS WORDS
    
    @param body: text of craigslist posting
    @returns: the number of emojis in the posting title
    """
    caps_words = [len(re.sub('[a-z0-9]', '', x))/len(x) for x in body.split(" ") if len(x) > 0]
    return(sum(np.array(caps_words) == 1))

def metrics_from_text(body: str) -> list:
    """
    Function that returns a number of metrics from the post text
    scam - a T/F indicator for scam keywords
    prop - property managment company name (from list) or web link found in post
    angry - number of all caps words
    word_length - number of words in post
    
    @param body: post text stripped from HTML
    @returns: a list of metrics
    """
    scam=bool(re.search(r'(lease to own)|(real estate agent)|(purchase program)|(realtor)', body.lower()))
    prop=property_management(body)
    angry=count_caps_words(body)
    word_length=len(body.split(" "))
    return([scam, prop, angry, word_length])

def get_sqft(soup: bs4.BeautifulSoup, body: str) -> str:
    """
    Function that searches the post soup and post text for square footage
    
    @param soup: BeautifulSoup object created from a craigslist posting
    @param body: post text stripped from HTML
    @returns: square footage
    """
    sqft=None
    # first try to find sqft from a superscript tag
    if soup.findAll('sup'):
        for x in soup.findAll('sup'):
            if x.text == '2' and x.find_previous_sibling():
                    sqft=x.find_previous_sibling().text
    # if sqft can't be found in a tag, try to pull it from text, add caveat (estimated)        
    if sqft is None and re.search(r'ft', body):
        try:
            max_size=max([re.findall(r'\d+',x[0]) for x in re.findall( r'(( \w+){3}) ft', body)])[0]
            sqft=str(max_size) + "(estimated)"
        except:
            pass
    return(sqft)

def dog_friendliness(soup: bs4.BeautifulSoup, body: str) -> str:
    """
    Function to look for pet friendliness indicators in post soup or post body text
    
    @param soup: BeautifulSoup object created from a craigslist posting
    @param body: post text stripped from HTML
    @returns: doggo an indicator of dog friendliness, can be: yes, no, unknown, or a snippet of the post
    """ 
    doggo='unknown'
    # first look for tag indicating dog friendly
    if sum(['dog' in x.text for x in soup.findAll('span')]) > 0:
        doggo='yes'
    # next search for 'no dogs' in text
    elif re.search(r'no (pet|dog|animal)s?', body.lower()):
        doggo='no'
    # finally search the text for any mention of dogs and return the whole sentence
    elif re.search(r'(pet|dog|animal)s?', body.lower()):
        doggo=" ".join([x for x in body.split(".") if re.search(r'(pet|dog|animal)s?', x.lower())])     
    return(doggo)

def make_output(soup_metrics: list, dog: str, sqft: str, text_metrics: list, address: list, snippet: str, url: str) -> pd.DataFrame:
    """
    This function combines all metrics derived from the post body and text
    
    @param soup_metrics: output of metrics_from_soup()
    @param dog: output of dog_friendliness()
    @param sqft: output for get_sqft()
    @param text_metrics: output of metrics_from_text()
    @param address: ouput from parse_address()
    @param snippet: first 100 characters of post body
    @param url: posting URL
    @returns
    """
    lat, long, posting_id, posted, updated, price, available, size, images, emoji=soup_metrics
    scam, prop, angry, word_length=text_metrics
    postal_address, zipcode, neighborhood, locality=address
    
    results_dict={posting_id : 
     {'url' : url,
      'price' : price,
      'date_available' : available,
      'bed_bath' : size,
      'sqft' : sqft,
      'num_images' : images,
      'dog' : dog,
      'scam' : scam,
      'property_management' : prop,
      'angry_score' : angry,
      'emoji' : emoji,
      'word_length' : word_length,
      'address' : postal_address,
      'snippet' : snippet,
      'zipcode' : zipcode,
      'neighborhood' : neighborhood,
      'locality' : locality,
      'date_posted' : posted,
      'date_updated' : updated,
      'latitude' : lat,
      'longitude' : long
    }}
    
    df=pd.DataFrame.from_dict(results_dict, columns=list(results_dict[posting_id].keys()), orient='index')
    return(df)

def extract_soup(soup: bs4.BeautifulSoup, url: str, file_path: str, api_key: str) -> pd.DataFrame:
    """
    Main function to parse useful metrics and data out of soup
    
    @param soup: BeautifulSoup object created from a craigslist posting
    @param url: URL for craigslist post
    @param file_path: directory to write body txt files
    @returns: DataFrame with metrics
    """
    # pull metrics from soup
    soup_metrics=metrics_from_soup(soup)
    # pull text only from post body
    posttext=get_posting_text(soup)
    # write post text to file
    with open(os.path.join(file_path, soup_metrics[2] + '.txt'), "w") as file:
        file.write(posttext)
    # get first 100 characters of post body
    snippet=posttext[0:100]
    # pull metrics from text
    text_metrics=metrics_from_text(posttext)
    # pull dog/sqft metric (soup and text)
    dog=dog_friendliness(soup, posttext)
    sqft=get_sqft(soup, posttext)
    # reverse lookup lat, long coords to address
    address=reverse_lookup(api_key, soup_metrics[0], soup_metrics[1])
    # create output dataframe
    df=make_output(soup_metrics, dog, sqft, text_metrics, address, snippet, url)
    return(df)
