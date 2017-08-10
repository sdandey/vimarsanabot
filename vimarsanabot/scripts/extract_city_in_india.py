import re
from bs4 import BeautifulSoup
import urllib.request
import csv

from pymongo import MongoClient

url = 'https://en.wikipedia.org/wiki/List_of_cities_in_Australia_by_population'
mongo_host= 'vps110824.vps.ovh.ca'
#mongo_host = 'localhost'
fb_access_tokens = list()
mongo_port= 27017

def get_wiki_url_for_each_country():
    city_extract_url ={}
    city_extract_url['india'] = 'https://en.wikipedia.org/wiki/List_of_cities_in_India_by_population'
    city_extract_url['usa'] = 'https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population'
    city_extract_url['canada'] = 'https://en.wikipedia.org/wiki/List_of_the_100_largest_municipalities_in_Canada_by_population'
    city_extract_url['uk'] = 'https://en.wikipedia.org/wiki/List_of_English_districts_by_population'
    city_extract_url['australia'] =  'https://en.wikipedia.org/wiki/List_of_cities_in_Australia_by_population'
    return city_extract_url


def extract_cities_information_from_wiki(url):
    page = urllib.request.urlopen(url)
    soup = BeautifulSoup(page.read(), "lxml")
    # cities_list = soup.find("table",{"class":"wikitable"})
    cities_list = soup.findAll("table")
    rows = list()
    for cities in cities_list:
        if cities.findParent("table") is None:
            for row in cities.findAll("tr"):
                cols = row.findAll('td')
                cols = [ele.text.strip() for ele in cols]
                rows.append([ele for ele in cols if ele])
    cities = list()
    for row in rows:
        if (len(row) >= 4):
            cities.append(row[1])
    return cities

def insert_record_in_database(country:str, cities:list):
    client = MongoClient(mongo_host, mongo_port)
    db = client['vimarsana']
    location_details=db.location_details
    result=location_details.insert_one({'country':country,'cities':cities})

def delete_all_records_in_mongodb():
    client = MongoClient(mongo_host,mongo_port)
    db=client['vimarsana']
    result = db.location_details.delete_many({})
    print('number of records deleted from fb_events:' + str(result))

def main():
    delete_all_records_in_mongodb()
    wikiurls = get_wiki_url_for_each_country()
    for country in wikiurls.keys():
        print('extracting event information for country' + country)
        cities = extract_cities_information_from_wiki(wikiurls[country])
        cities = list(set(cities))
        print('cities count before filter ' + str(len(cities)))
        cities = list(set(cities))
        print('cities count after filter ' + str(len(cities)))

        regex = re.compile('[^a-zA-Z\s]')
        cities = map(lambda city:regex.sub('',city),cities)
        cities = list(filter(None, cities))
        print('cities count before filter ' + str(len(cities)))
        print(cities)
        insert_record_in_database(country,cities)


if __name__ == '__main__':
    main()