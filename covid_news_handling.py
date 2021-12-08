"""<------------------------Covid-Dashboard Module------------------------>"""
import requests
import json
import sched
import schedule 
import time
import datetime
from datetime import datetime
from newsapi import NewsApiClient
from flask import Blueprint
from newsapi import NewsApiClient
from time_conversion import hhmm_to_seconds
import logging

#Initialising a events logging file
logging.basicConfig(filename='events.log',level=logging.DEBUG, format="%(asctime)s %(message)s")

#Gets News API key and amount of news shown from config file
with open("config.json", "r") as file:
    temp2 = file.read()
    temp3 = json.loads(temp2)
    key = temp3["key"]
    news_num = temp3['news_num']
    news_search = temp3['news_search']

"""<------------------------News Module------------------------>"""


def news_API_request(covid_terms=news_search):
    #Set the news list so it can be appended
    news = [{}]
    #Get the top headlines from the API
    newsapi = NewsApiClient(api_key= str(key))
    top_headlines = newsapi.get_top_headlines(q = covid_terms)
    #Appends the said number of articles on a list which is then returned
    for i in range(0,news_num):
        news.append(top_headlines["articles"][i])
    del news[0] #Gets rid of the empty list 
    return news


"""<------------------------Update News Module------------------------>"""

now = datetime.now()
current_time = now.strftime("%H:%M")
s = sched.scheduler(time.time, time.sleep)

def update_news(update_interval="11:25", update_name="covid", func=news_API_request):
    wait = hhmm_to_seconds(current_time)
    update_interval_test = hhmm_to_seconds(update_interval)
    logging.info("schedule set for :", update_interval, " at " , current_time)
    #Makes sure only one schedule is added each time the function is called
    order = 0
    while order == 0:
        if isinstance(update_interval_test, int) and isinstance(wait, int):
            delay = update_interval_test - wait
            order = order + 1
            s.enter(int(delay), 1, func, ())
            s.run(blocking=False)
            return s.queue
        else:
            print("NONE", update_interval_test , " , " , wait)
            break