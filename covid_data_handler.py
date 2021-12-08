"""<------------------------Covid-Dashboard Module------------------------>"""
#Importing libaries
from uk_covid19 import Cov19API
import json
import sched
import time
import datetime
import requests
from datetime import datetime
from flask import Flask
from newsapi import NewsApiClient
from flask import render_template
from flask import request
import covid_news_handling
from covid_news_handling import news_API_request, update_news
from time_conversion import hhmm_to_seconds
import logging

#Initialising a events logging file which resets when the program starts everything
logging.basicConfig(filename='events.log',level=logging.DEBUG, format="%(asctime)s %(message)s" , filemode='w')

with open('events.log', 'w'):
    pass

#Initialising Flask libary
app = Flask(__name__)

#Getting Location from conifg file
with open("config.json", "r") as file:
    temp2 = file.read()
    temp3 = json.loads(temp2)
    location_country = temp3["location_country"]

"""<------------------------Fubction to read file------------------------>"""

def parse_csv_data(csv_filename):
    #Opens file and reads every line and then returns it as a variable
    covid_csv_data = open(csv_filename , 'r').readlines()
    return(covid_csv_data)

"""<------------------------Function to calculate cases in last 7 days , current hospital cases and total deaths till now------------------------>"""

def process_covid_csv_data(covid_csv_data):
    #Adds the cases to a counter starting from the first day with data
    last7days_cases = 0
    for i in range(3,10):
        content_list_7days = covid_csv_data[i].split(",")
        last7days_cases += int(content_list_7days[6])
    #Reads the last amount of hospital cases
    content_list_hospital = covid_csv_data[1].split(",")
    current_hospital_cases = int(content_list_hospital[5])
    #Goes through the Deaths column until gets a value that is a digit
    count = 0
    while count != len(covid_csv_data):
        content_list_death = covid_csv_data[count].split(",")
        if content_list_death[4].isdigit():
            total_deaths = int(content_list_death[4])
            break
        else:
            count += 1            
    #Returns all values 
    return(last7days_cases, current_hospital_cases, total_deaths)

"""<------------------------Function to get data from API------------------------>"""

def covid_API_request( location ="Exeter", location_type="ltla"):
    #Creates a dictionary with  the location and location type
    local = ['areaType='+location_type,'areaName='+location]
    national = ['areaType=nation','areaName='+location_country]

    #Sets the data wanted to get from the API through a filter
    national_filt = {
                    "newCasesBySpecimenDate": "newCasesBySpecimenDate",
                    "cumDailyNsoDeathsByDeathDate":"cumDailyNsoDeathsByDeathDate",
                    "hospitalCases":"hospitalCases"
                    }
    local_filt = {
                 "newCasesBySpecimenDate": "newCasesBySpecimenDate"
                 }

    #Requests the data from the API and returns that data
    local_api = Cov19API(filters=local, structure=local_filt)
    local_data_API = local_api.get_json()['data']
    national_api = Cov19API(filters=national, structure=national_filt)
    national_data_API = national_api.get_json()['data']

    #Adds the last 7 days infection rates through a counter
    natInfectionSum=0
    locInfectionSum=0
    count=1

    while(count!=7):
        singleDayNat = national_data_API[count]
        singleDayLoc = local_data_API[count]
        natInfectionSum = natInfectionSum + singleDayNat.get('newCasesBySpecimenDate')
        locInfectionSum = locInfectionSum + singleDayLoc.get('newCasesBySpecimenDate')
        count=count+1

    #Gets the national hospital and death cases which are the newest ones in the API
    natHospCases = national_data_API[0].get('hospitalCases')
    numCheck = False
    i = 0
    while numCheck == False:
        if type(national_data_API[i].get('cumDailyNsoDeathsByDeathDate')) == int or float:
            natCumDeaths = national_data_API[i].get('cumDailyNsoDeathsByDeathDate')
            numCheck = True
        else:
            i = i + 1

    return "COVID-19 Infection Rates", location , locInfectionSum,location_country,natInfectionSum,natHospCases,natCumDeaths

"""<------------------------Schedule Module------------------------>"""

now = datetime.now()
current_time = now.strftime("%H:%M")
s = sched.scheduler(time.time, time.sleep)

def schedule_covid_updates(update_interval="11:25", update_name="covid" , func=covid_API_request):
    #Converts time into seconds
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
        
"""-------------------------------------Calling function of Flask-------------------------------------------------"""
#Functions to store data into files
def news_update(file_update):
    with open('temp_file.json', 'w') as convert_file:
        convert_file.write(json.dumps(file_update))
def sched_update(file_update):
    with open('temp_file_sched.json', 'w') as convert_file:
        convert_file.write(json.dumps(file_update))
        

#Sets initial files
newsTemp = news_API_request()
holder = [{"source": {"title":"First", "content":"Second"}}]
news_update(newsTemp)
sched_update(holder)

#Global flag to check if schedule has been created
global flag
flag = False
global flag_i
flag_i = 0


@app.route('/index')
def run_flask():
    #Gets Covid API data
    title, location ,locInfectionSum,location_country,natInfectionSum,natHospCases ,natCumDeaths = covid_API_request()
    #Opens news API data
    with open("temp_file.json", "r") as file:
        temp4 = file.read()
        news = json.loads(temp4)
        data = 0
        global flag  
        global update 
        global flag_i 
        #Gets setter schedule data from URL
        data = request.args.get("update")
        data_title = request.args.get("two")
        temp = 0
        #Gets deletion data from URL
        notif = request.args.get("notif")
        notif_sched = request.args.get("update_item")
        #If a widget is deleted it is checked in which position it is before being removed
        if notif:
            for i in range(len(news)-1):
                if news[i]['title'] == notif:
                    #The file is then reset to not include removed news
                    del news[i]
                    news_update(news)
        #If a widget is deleted it is checked in which position it is before being removed
        if notif_sched:
            with open('temp_file_sched.json', 'r') as file_sched2:
                temp_sched2 = file_sched2.read()
                update = json.loads(temp_sched2)
            print(notif_sched)
            for i in range(0,len(update)-1):
                if update[i]['title'] == notif_sched:
                    #The file is then reset to not include removed schedule event
                    del update[i]
                    sched_update(update)
        elif data != temp and data != None:
            #If URL has changed a schedule is made
            flag = True #It then remembers it in the global flag   
            repeat = request.args.get('repeat')
            covid_repeat = request.args.get('covid-data')
            news_repeat = request.args.get('news')
            #If both covid and news are to be updated a widget is made with both combined
            if covid_repeat and news_repeat:
                if repeat:
                    temp = schedule_covid_updates(update_interval=data, update_name=data_title, func=schedule_covid_updates)
                    temp = update_news(update_interval=data, update_name=data_title ,func=schedule_covid_updates)
                    temp_list = {"title":data_title , "content":data+" , Covid Update & News Update , Repeated"}
                if not repeat:
                    temp_list = {"title":data_title , "content":data+" , Covid Update & News Update"}
                temp_c = schedule_covid_updates(update_interval=data, update_name=data_title)
                temp_n = update_news(update_interval=data, update_name=data_title)
            #Else if not both are chosen
            elif not (covid_repeat and news_repeat):
                if covid_repeat:
                    if repeat:
            #If both covid and repeat are chosen it will call the scheduler function after the given time so it calls it again for ever
                        temp = schedule_covid_updates(update_interval=data, update_name=data_title, func=schedule_covid_updates)
                        temp_list = {"title":data_title , "content":data+" , Covid Update , Repeated"}
                    if not repeat:
                        temp_list = {"title":data_title , "content":data+" , Covid Update"}
                    temp = schedule_covid_updates(update_interval=data, update_name=data_title)
                if news_repeat:
                    if repeat:
            #If both news and repeat are chosen it will call the scheduler function after the given time so it calls it again for ever
                        temp = update_news(update_interval=data, update_name=data_title ,func=schedule_covid_updates)
                        temp_list = {"title":data_title , "content":data+" , News Update , Repeated"}
                    if not repeat:
                        temp_list = {"title":data_title , "content":data+" , News Update"}
                    temp = update_news(update_interval=data , update_name=data_title) 
                if repeat and not (covid_repeat or news_repeat):
                    temp = update_news(update_interval=data, update_name=data_title ,func=schedule_covid_updates)
                    temp_list = {"title":data_title , "content":data+" , Repeated"}
            if not (repeat or covid_repeat or news_repeat):
                temp = update_news(update_interval=data, update_name=data_title ,func=schedule_covid_updates)
                temp_list = {"title":data_title , "content":data}

            #The file is opened and read then appened to the list and then reset 
            with open('temp_file_sched.json', 'r') as file_sched:
                temp_sched = file_sched.read()
                temp_reload = json.loads(temp_sched)
                temp_reload.append(temp_list)
                if flag == True and flag_i == 0:
                    del temp_reload[0]
                    flag_i = 1
                sched_update(temp_reload)
            with open('temp_file_sched.json', 'r') as file_sched2:
                temp_sched2 = file_sched2.read()
                update = json.loads(temp_sched2)

        #The data is then rendered by sending it in Flask
        if (data != temp and data != None) or flag == True:
            return render_template("index.html", 
                                    title="COVID-19 Infection Rates", 
                                    location = location, 
                                    local_7day_infections = locInfectionSum,
                                    nation_location = location_country,
                                    national_7day_infections = natInfectionSum,
                                    news_articles = news,
                                    hospital_cases = "Hospital cases: " + str(natHospCases),
                                    deaths_total = "Total Deaths: " + str(natCumDeaths),
                                    updates = update,
                                    )   
        return render_template("index.html", 
                                title="COVID-19 Infection Rates", 
                                location = location, 
                                local_7day_infections = locInfectionSum,
                                nation_location = location_country,
                                national_7day_infections = natInfectionSum,
                                news_articles = news,
                                hospital_cases = "Hospital cases: " + str(natHospCases),
                                deaths_total = "Total Deaths: " + str(natCumDeaths),
                                )

#Flask app is then run
if __name__ == '__main__':
    app.run(debug=True)


"""<------------------------Test One------------------------>"""

#data = parse_csv_data('nation_21 -10-28.csv') 
#assert len(data) == 639
#print(data)

"""<------------------------Test Two------------------------>"""

#last7days_cases , current_hospital_cases , total_deaths = process_covid_csv_data(parse_csv_data('nation_21 -10-28.csv'))
#assert last7days_cases == 240_299
#assert current_hospital_cases == 7_019
#assert total_deaths == 141_544

"""<------------------------Test Three------------------------>"""

#covid_API_request()
#covid_API_request("England","nation")

"""<------------------------Test Four------------------------>"""

#schedule_covid_update()
