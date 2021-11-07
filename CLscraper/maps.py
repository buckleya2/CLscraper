import requests

def parse_address(json) -> list:
    """
    Function that parses the Gogle maps API json output 
    
    @param json: Google's reverse lookup json object
    @returns: a list with address, zipcode, neighborhood, and locality (Google defined)
    """
    result=json['results'][0]
    address=result['formatted_address']
    zipcode, neighborhood, locality=(None, None, None)
    for entry in result['address_components']:
        if 'postal_code' in entry['types']:
            zipcode=entry['long_name']
        elif 'neighborhood' in entry['types']:
            neighborhood=entry['long_name']
        elif 'locality' in entry['types']:
            locality = entry['long_name']
    return([address, zipcode, neighborhood, locality])

def reverse_lookup(key: str, lat: str, long: str) -> list:
    """
    Function that uses Google's reverse lookup API to turn latitude and longitude into a street address

    @param lat: latitude
    @param long: longitude
    @returns: Google's reverse lookup json object
    """
    # Google's reverse lookup API
    url='https://maps.googleapis.com/maps/api/geocode/json?latlng='
    r=requests.get(url + lat + ',' + long + "&key=" + key)
    json=r.json()
    # parse output
    address=parse_address(json)
    return(address)

def check_new(database: list, url_dict: dict) -> list:
    """
    Function that filters list of all URLs to only new URLs
    
    @param database: a list of all CL post ids currently in text database
    @param url_dict: a dict of URLs to be checked against URLs already scraped, generated by extract_links()
    @returns: filtered list of only new URLs
    """
    # for ids not in database, return url
    new=[url_dict[key] for key, value in url_dict.items() if int(key) not in database]
    return(new)
