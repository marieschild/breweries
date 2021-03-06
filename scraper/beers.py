#!/usr/bin/env python

"""Scrape beer styles from beeradvocate.com/beer/style/."""

# scraping
import requests
from lxml import html

# mongodb
from pymongo import MongoClient, DESCENDING

# functions


def get_html(link):
    """Load HTML page and parse it."""
    # load html page and parse it
    page = requests.get(link)
    tree = html.fromstring(page.content)
    return tree


def parse_beer_info(link):
    """Parse information of beer."""
    # constants to select range in table
    min_tr = 4
    max_tr = 54
    page = requests.get(link)
    tree = html.fromstring(page.content)

    brew_name, ids, beer_name = [], [], []

    for i in range(min_tr, max_tr):
        p = '//*[@id="ba-content"]/table/tr[' + str(i) + ']'

        brew_name.append(tree.xpath(p + '//text()')[1])
        beer_name.append(tree.xpath(p + '//text()')[0])
        ids.append(tree.xpath(p + '//a/@href')[0])

    brewery_id = [i.split('/')[3] for i in ids]
    beer_id = [i.split('/')[4] for i in ids]

    return(beer_id, beer_name, brewery_id, brew_name)


bstyles = list(zip([155, 159, 73, 175, 40],
               ['American Pale Lager', 'American Porter', 'American Brown Ale',
                'American Black Ale', 'Czech Pilsener']))

print('Extract all beers for styles')

link = 'https://www.beeradvocate.com/beer/style/'

# connect to mongodb client
client = MongoClient()
db = client.breweries

# loop over beer styles and get 50 beers with highest amount of reviews
for style in bstyles:
    print(style)
    link = 'https://www.beeradvocate.com/beer/style/%(style)d/?sort=revsD' % {
           'style': style[0]}

    beer_ids, beer_names, brew_ids, brew_names = [], [], [], []
    try:
        beer_ids, beer_names, brew_ids, brew_names = parse_beer_info(link)

        # get beer data in mongodb format
        beers = [{'beer_id': int(beer_id),
                  'brew_id': int(brew_id),
                  'style_id': style[0],
                  'beer_name': beer_name,
                  'brew_name': brew_name,
                  'style_name': style[1]}
                 for beer_id, brew_id, beer_name, brew_name
                 in zip(beer_ids, brew_ids, beer_names, brew_names)]

        # add beers to mongodb
        db.styles.insert(beers)
    except:
        print('Some Problem here.')  # probably less than 50 beers in style


# add beer_id and brew_id as compund index
client = MongoClient()
db = client.breweries

db.styles.create_index([('brew_id', DESCENDING),
                       ('beer_id', DESCENDING)])
