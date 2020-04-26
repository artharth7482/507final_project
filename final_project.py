import requests
from bs4 import BeautifulSoup
import time
import json
import csv
import pandas
import sqlite3

def load_cache(cache_file_name): # called only once, when we run the program
    try:
        cache_file = open(cache_file_name,'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache, cache_file_name): # called whenever the cache is changed
    cache_file = open(cache_file_name, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache, cache_file_name):
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url, headers=headers)
        cache[url] = response.text
        save_cache(cache, cache_file_name)
        return cache[url]

headers = {
    'User-Agent': 'UMSI 507 Course Project',
    'From': 'hsliao@umich.edu',
    'Course-Info': 'https://www.si.umich.edu/programs/courses/507'
}


#### CRAWLING ATP PLAYERS DATA ####

PLAYER_BASEURL = 'https://www.atptour.com'
RANKING_DETAILED_URL = '/rankings/singles'
PLAYER_CACHE_FILE_NAME = 'player_cache.json'
PLAYER_CACHE_DICT = {}

# Load the cache, save in global variable
PLAYER_CACHE_DICT = load_cache(PLAYER_CACHE_FILE_NAME)

#class player:
NEWEST_DATE_PARENT_TAG = 'div'
NEWEST_DATE_PARENT_CLASS = 'dropdown-wrapper'
NEWEST_DATE_TAG = 'div'
NEWEST_DATE_CLASS = 'dropdown-label'
PLAYER_BODY_TAG = 'tbody'
PLAYER_PARENT_TAG = 'tr'
PLAYER_RANK_CLASS = 'rank-cell'
PLAYER_COUNTRY_CLASS = 'player-flag-code'
PLAYER_CELL_TAG = 'td'
PLAYER_CELL_CLASS = 'player-cell'
PLAYER_URL_TAG = 'a'
PLAYER_INFO_PARENT_TAG = 'div'
PLAYER_INFO_PARENT_CLASS = 'inner-wrap'
PLAYER_LASTNAME_CLASS = 'last-name'
PLAYER_FIRSTNAME_CLASS = 'first-name'
PLAYER_RANK_TAG = 'td'
PLAYER_AGE_TAG = 'div'
PLAYER_AGE_CLASS = 'table-big-value'
PLAYER_WEIGHT_TAG = 'span'
PLAYER_WEIGHT_CLASS = 'table-weight-lbs'
PLAYER_HEIGHT_TAG = 'span'
PLAYER_HEIGHT_CLASS = 'table-height-ft'
PLAYER_PLAYS_GRANDPARENT_TAG = 'tr' # the second one
PLAYER_PLAYS_PARENT_TAG = 'td' # the third one
PLAYER_PLAYS_TAG = 'div'
PLAYER_PLAYS_CLASS = 'table-value'
PLAYER_GEAR_PARENT_TAG = 'div'
PLAYER_GEAR_PARENT_CLASS = 'players-equipment-item'
PLAYER_GEAR_NAME_TAG = 'h3'
PLAYER_GEAR_IMAGE_TAG = 'img'

## Make the soup for the main page
atp_url = PLAYER_BASEURL + RANKING_DETAILED_URL
url_text = make_url_request_using_cache(atp_url, PLAYER_CACHE_DICT, PLAYER_CACHE_FILE_NAME)
soup = BeautifulSoup(url_text, 'html.parser')

# Get the newest date and create the partial url
newest_date = soup.find(NEWEST_DATE_PARENT_TAG,class_=NEWEST_DATE_PARENT_CLASS).find(NEWEST_DATE_TAG,class_=NEWEST_DATE_CLASS).text.strip()
date_url = '-'.join(newest_date.split('.'))

## For each ranking tier
ranking_pages_list = ['0-100', '101-200', '201-300','301-400', '401-500', '501-600', '601-700', '701-800', '801-900', '901-1000', '1001-1100', '1101-1200', '1201-1300', '1301-1400', '1401-1500', '1501-1600', '1501-5000']
player_dict = {}
for i in range(17):
    ## Make the soup for the all the ranking pages (1-100,101-200,.......,1501 and up)
    url = f'{PLAYER_BASEURL}{RANKING_DETAILED_URL}?rankDate={date_url}&rankRange={ranking_pages_list[i]}'
    page_url_text = make_url_request_using_cache(url, PLAYER_CACHE_DICT, PLAYER_CACHE_FILE_NAME)
    page_soup = BeautifulSoup(page_url_text, 'html.parser') 

    ## For each players listed
    page_body = page_soup.find(PLAYER_BODY_TAG)
    player_parent = page_body.find_all(PLAYER_PARENT_TAG)
    for j in player_parent:
        player_cell = j.find(PLAYER_CELL_TAG,class_=PLAYER_CELL_CLASS)
        player_suburl = player_cell.find(PLAYER_URL_TAG)['href']

        ## Make the soup for the player
        player_url = PLAYER_BASEURL + player_suburl
        player_url_text = make_url_request_using_cache(player_url, PLAYER_CACHE_DICT, PLAYER_CACHE_FILE_NAME)
        player_soup = BeautifulSoup(player_url_text, 'html.parser')

        ## extract wta player's name
        player_info_parent = player_soup.find_all(PLAYER_INFO_PARENT_TAG,class_=PLAYER_INFO_PARENT_CLASS)
        last_name = player_info_parent[0].find(PLAYER_INFO_PARENT_TAG, class_=PLAYER_LASTNAME_CLASS).text.strip()
        first_name = player_info_parent[0].find(PLAYER_INFO_PARENT_TAG, class_=PLAYER_FIRSTNAME_CLASS).text.strip()

        ## extract player's rank (use page_soup)
        rank = j.find(PLAYER_RANK_TAG, class_=PLAYER_RANK_CLASS).text.strip()

        ## extract player's country
        country = player_info_parent[0].find(PLAYER_INFO_PARENT_TAG, class_=PLAYER_COUNTRY_CLASS).text.strip()

        ## extract player's age
        age = player_info_parent[1].find(PLAYER_AGE_TAG,class_=PLAYER_AGE_CLASS).text.strip()

        ## extract player's weight
        try:
            weight = player_info_parent[1].find(PLAYER_WEIGHT_TAG,class_=PLAYER_WEIGHT_CLASS).text.strip()
        except AttributeError:
            weight = None        

        ## extract player's height
        try:
            height = player_info_parent[1].find(PLAYER_HEIGHT_TAG,class_=PLAYER_HEIGHT_CLASS).text.strip()
        except AttributeError:
            height = None

        ## extract player's plays
        try:
            plays_grandparent = player_info_parent[1].find_all(PLAYER_PLAYS_GRANDPARENT_TAG)[1]
            plays_parent = plays_grandparent.find_all(PLAYER_PLAYS_PARENT_TAG)[2]
            plays = plays_parent.find(PLAYER_PLAYS_TAG, class_=PLAYER_PLAYS_CLASS).text.strip()
        except AttributeError:
            plays = None

        ## extract player's gear names and images
        gear_dict = {}
        gear_image_dict = {}
        try:
            player_gear_parent = player_soup.find_all(PLAYER_GEAR_PARENT_TAG,class_=PLAYER_GEAR_PARENT_CLASS)
            #gear name
            for i in range(3):
                try:
                    gear_name = player_gear_parent[i].find(PLAYER_GEAR_NAME_TAG)
                    gear_dict[i] = gear_name.text.strip()
                except IndexError:
                    gear_dict[i] = None
            #gear image
                try:
                    gear_image = player_gear_parent.find(PLAYER_GEAR_IMAGE_TAG)
                    gear_image_dict[i] = PLAYER_BASEURL + gear_image['src']
                except IndexError:
                    gear_image_dict[i] = None
        except AttributeError:
            for i in range(3):
                gear_dict[i] = None
                gear_image_dict[i] = None

    ## put all the data into the dictionary
        player_dict[rank] = [last_name, first_name, rank, country, age, height, weight, plays, gear_dict[0], gear_image_dict[0], gear_dict[1], gear_image_dict[1], gear_dict[2], gear_image_dict[2]]


#### Load matches data ####
file_contents = open('df_atp.csv', 'r')
csv_reader = csv.reader(file_contents)
next(csv_reader)

#create database
conn = sqlite3.connect('atp.sqlite')
cur = conn.cursor()

drop_players_sql = 'DROP TABLE IF EXISTS "Players"'
drop_matches_sql = 'DROP TABLE IF EXISTS "Matches"'


create_players_sql = '''
    CREATE TABLE IF NOT EXISTS 'Players' (
        'Id' INTEGER PRIMARY KEY AUTOINCREMENT, 
        'LastName' TEXT NOT NULL,
        'FirstName' TEXT NOT NULL, 
        'Rank' INTEGER NOT NULL,
        'Country' TEXT NOT NULL,
        'Age' INTEGER,
        'Height' TEXT,
        'Weight' TEXT, 
        'Plays' TEXT, 
        'Gear1' TEXT, 
        'GearImage1' TEXT,
        'Gear2' TEXT,
        'GearImage2' TEXT,
        'Gear3' TEXT,
        'GearImage3' TEXT
    )
'''

create_matches_sql = '''
    CREATE TABLE IF NOT EXISTS 'Matches'(
        'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
        'ATP' INTEGER NOT NULL,
        'Tournament' TEXT NOT NULL,
        'Location' TEXT NOT NULL,
        'Surface' TEXT NOT NULL,
        'Date' INTEGER NOT NULL,
        'Round' TEXT NOT NULL,
        'BestOf' INTEGER NOT NULL,
        'Winner' TEXT NOT NULL,
        'Loser' TEXT NOT NULL
    )
'''
cur.execute(drop_players_sql)
cur.execute(drop_matches_sql)
cur.execute(create_players_sql)
cur.execute(create_matches_sql)
conn.commit()

insert_players = '''
    INSERT INTO Players
    VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
'''

insert_matches = '''
    INSERT INTO Matches
    VALUES (NULL,?,?,?,?,?,?,?,?,?)
'''

for player in player_dict:
    cur.execute(insert_players, player_dict[player])

for row in csv_reader:
    cur.execute(insert_matches,[
        row[0],
        row[1],
        row[2],
        row[3],
        row[4],
        row[5],
        row[6],
        row[7],
        row[8]
    ])

conn.commit()
conn.close()
