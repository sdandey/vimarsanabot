import json
import pprint
import urllib.request

import re
from threading import Thread

from bs4 import BeautifulSoup
import facebook
from pymongo import MongoClient

wikiCitiUrl = 'https://en.wikipedia.org/wiki/List_of_cities_in_India_by_population'
accesstoken = 'EAAXg2lcZCvBUBAHYq8SvI5eixorhcOxAslO2i0FUBQJp3mLuj9pFv9vh4QJeulIrmCfndmTwkwzdVvXClsz3ZBtBOcjrkwVZAnPyTbFoX0OSygHdVTva240AO2W7ZBCH1ZAZAhdWYjnBZBHXHBMZAHbAFI4DbzblUtowb25fxVG75AZDZD'
#name of the app vimarsana for santoshdandey user
fb_fields_to_retrieve='name,place,attending_count,cover,description,owner,parent_group,ticket_uri,start_time,end_time,updated_time,interested_count,timezone,type'
fb_appid='1654603254840341'
fb_secret='147879469d33521da94c3c6df27dc3aa'
mongo_host= 'vps110824.vps.ovh.ca'
#mongo_host = 'localhost'
fb_access_tokens = list()
mongo_port= 27017
fb_counter = 0
fb_access_tokens_index=0
fb_current_access_token=''
fb_api_max_hits_error_message='It looks like you were misusing this feature by going too fast. You’ve been blocked from using it'

class SaveEvents(Thread):
   def __init__(self, queue):
       Thread.__init__(self)
       self.queue = queue

   def run(self):
       while True:
           # Get the work from the queue and expand the tuple
           data, city = self.queue.get()
           insert_record_in_database(data, city)
           self.queue.task_done()

class RetrieveEvents(Thread):
    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Get the work from the queue and expand the tuple
            city = self.queue.get()
            extract_events(city)
            self.queue.task_done()

def get_wiki_url_for_each_country():
    city_extract_url ={}
    city_extract_url['usa'] = 'https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population'
    city_extract_url['uk'] = 'https://en.wikipedia.org/wiki/List_of_English_districts_by_population'
    city_extract_url['canada'] = 'https://en.wikipedia.org/wiki/List_of_the_100_largest_municipalities_in_Canada_by_population'
    city_extract_url['australia'] =  'https://en.wikipedia.org/wiki/List_of_cities_in_Australia_by_population'
    city_extract_url['india'] = 'https://en.wikipedia.org/wiki/List_of_cities_in_India_by_population'

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



def extract_events(city, fb_access_tokens:list):
    try:
        graph = facebook.GraphAPI(access_token=retrieve_fb_token(fb_access_tokens, False), version=2.7)
        events = graph.request('/search?q='+city+'&type=event&limit=10000&fields=' + fb_fields_to_retrieve)
    except facebook.GraphAPIError as exception:
        print('my catched exception:' + exception.message)
        #if(fb_api_max_hits_error_message == exception.message):
        retrieve_fb_token(fb_access_tokens,True)
        return extract_events(city, fb_access_tokens)
    return events['data']

def long_live_fb_access_token():
    graph = facebook.GraphAPI(access_token=accesstoken, version=2.7)
    graph.extend_access_token(fb_appid,fb_secret)

def delete_all_records_in_mongodb():
    client = MongoClient(mongo_host,mongo_port)
    db=client['vimarsana']
    result = db.fb_events.delete_many({})
    print('number of records deleted from fb_events:' + str(result))

def extract_event_for_city():
    #Long Lived Access Token that's there for 60 days
    fbApi = "https://graph.facebook.com/v2.10/search?q=hyderabad%20events&type=event&limit=500&access_token=" + accesstoken
    data = json.load(urllib.request.urlopen(fbApi))
    with open('data.txt', 'w') as outfile:
        json.dump(data, outfile)


def retrieve_fb_token(fb_access_tokens:list, is_retrieve_new_token:bool):
    global fb_counter
    global fb_access_tokens_index
    global fb_current_access_token
    fb_counter += 1

    if(is_retrieve_new_token):
        fb_access_tokens_index += 1
        fb_current_access_token = fb_access_tokens[fb_access_tokens_index]
        print('new token' + fb_current_access_token)
        return fb_current_access_token

    if not fb_current_access_token:
        fb_current_access_token = fb_access_tokens[0]
    else:
        return fb_current_access_token


def insert_record_in_database(data, city):
    client = MongoClient(mongo_host, mongo_port)
    db = client['vimarsana']
    fb_events=db.fb_events
    result=fb_events.insert_many(data)
    print('inserted ' + str(len(result.inserted_ids)) + ' events in the database for city ' + city)


def extract_event_information(cities:list,access_tokens:list):
    total_events = 0
    for city in cities:
        regex = re.compile('[^a-zA-Z]')
        events = extract_events(regex.sub('',city), access_tokens)
        print('grabbed ' + str(len(events)) + ' events for city ' + city)
        if (len(events) > 0):
            insert_record_in_database(events, city)
        total_events = total_events + len(events)
    print("total events from different cities:" + str(total_events))

def get_fb_access_tokens_from_db():
    client = MongoClient(mongo_host, mongo_port)
    db = client['vimarsana']
    fb_access_tokens = db.fb_access_tokens.find()
    accesstokens = list()
    for document in fb_access_tokens:
        accesstokens.append(document['access_token'])
    return accesstokens

def filter_data(data:list):
    data = list(set(data))
    regex = re.compile('[^a-zA-Z\s]')
    data = map(lambda city: regex.sub('', city), data)
    data = list(filter(None, data))
    print('cities count before filter ' + str(len(data)))
    return data

def main():
    delete_all_records_in_mongodb()
    wikiurls = get_wiki_url_for_each_country()

    access_tokens = get_fb_access_tokens_from_db()
    list(map(lambda x: print(x), access_tokens))
    for country in wikiurls.keys():
        print('extracting event information for country' + country)
        cities = extract_cities_information_from_wiki(wikiurls[country])
        extract_event_information(filter_data(cities),access_tokens)


if __name__ == '__main__':
    main()



#print('saving all events into a json file')

#with open('events.json', 'w') as outfile:
#    json.dump(json.dumps(total_events),outfile)




