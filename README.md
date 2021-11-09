# CLscraper

CLscraper is my personal project, meant for educational purposes only.

CLscraper is a command line tool that can search through housing listings on craigslist and pull out key metrics of interest

## Installation Instructions

First install miniconda http://docs.conda.io/en/latest/miniconda.html

Requirements can be installed using
```pip3 install -r requirements.txt```

CLscraper can be installed using
```python setup.py install```

## Usage

Clscraper requires 3 main inputs:
- a base craigslist housing search result stem
  - example: ```https://portland.craigslist.org/search/apa?bundleDuplicates=1&hasPic=1&housing_type=6&maxSqft=2200&max_price=4000&min_bathrooms=2&min_bedrooms=2'```
- a directory to store output files
- an API key for Google maps API
  - access detailed here: https://developers.google.com/maps/documentation/geocoding/start


By default, CLscraper will use all craigslist search result stems located in the searches.py file

Example command line usage

```CLscraper /PATH/TO/OUTPUT /PATH/TO/API_FILE```

## Outputs

