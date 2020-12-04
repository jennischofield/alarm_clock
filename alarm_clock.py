"""alarm_clock is a program used to run a smart alarm clock designed to
keep one updated on the world during the time of COVID-19.
It includes the ability to create alarms for any time and day,
which will then read aloud the contents of the alarm,
as well as providing notifications of weather, news,
and the most recent COVID-19 updates each hour.
This program was designed as the final project for ECM1400
at the University of Exeter"""
import time
import sched
import json
import logging
from datetime import date
from time import strftime
from flask import Flask
from flask import Markup
from flask import request, render_template, redirect
#pylint:disable = E0401
import requests
import pyttsx3
#pylint:disable = E0401
from uk_covid19 import Cov19API
s = sched.scheduler(time.time, time.sleep)
app = Flask(__name__)
engine = pyttsx3.init()
alarms = []
notifications = []
schednamelist = []
news_articles = []
dismissedlist = []
FORMAT = '%(levelname)s: %(asctime)s: %(message)s'
logging.basicConfig(filename = "alarmclock.log", level = logging.DEBUG, format = FORMAT)
cases_and_deaths = {"date": "date",
"areaName": "areaName",
"areaCode": "areaCode",
"newCasesByPublishDate": "newCasesByPublishDate",
"cumCasesByPublishDate": "cumCasesByPublishDate",
"newDeathsByDeathDate": "newDeathsByDeathDate",
"cumDeathsByDeathDate": "cumDeathsByDeathDate",
}
NOTIFTIMECOUNTER = 0

#helper functions
def format_string(inputstring:str)->str:
    """Correctly formats the time and day into legible string"""
    datetimelist = inputstring.split('T')
    real_alarm_time = datetimelist[-1]
    real_alarm_day = datetimelist[0]
    logging_string= "formatted " + inputstring +"to string"
    logging.info(logging_string)
    return "Set for " + real_alarm_time + " on " + real_alarm_day
def hhmm_to_seconds(inputtime:str):
    """Converts a time string in the from of Y-M-DTH:M to seconds"""
    timelist = inputtime.split('T')
    timenow = str(timelist[-1])
    minutelist = str(timenow).split(':')
    logging_string = "Converted " + inputtime + " to seconds"
    logging.info(logging_string)
    return int(minutelist[0])*3600 + int(minutelist[1])*60
def is_before(timecheck1:str, timecheck2:str):
    """Checks to see which string came before the other"""
    seconds1 = hhmm_to_seconds(timecheck1)
    seconds2 = hhmm_to_seconds(timecheck2)
    if seconds1 - seconds2 > 0:
        logging.info(timecheck1 + " is before " + timecheck2)
        return True
    logging.info(timecheck2 + " is before " + timecheck1)
    return False
def datedifference(time1:str, time2:str):
    """Helper function to get the number of days between two dates"""
    date1 = time1.split('T')
    date2= time2.split('T')
    datelist1= date1[0].split('-')
    year1 = int(datelist1[0])
    month1 = int(datelist1[1])
    day1 = int(datelist1[2])
    datelist2= date2[0].split('-')
    year2 = int(datelist2[0])
    month2 = int(datelist2[1])
    day2 = int(datelist2[2])
    properdate1 = date(year1, month1, day1)
    properdate2 = date(year2, month2, day2)
    difference = properdate1 - properdate2
    logging.info("Found difference of days")
    return difference.days
def insert_alarm_to_list(alarm1:dict):
    """Inserts an alarm chronologically to the alarms list"""
    counter = 0
    if len(alarms) == 0:
        alarms.append(alarm1)
    else:
        while True:
            if counter <= len(alarms):
                #pylint:disable = R1723
                if counter == len(alarms):
                    alarms.append(alarm1)
                    break
                elif is_before(alarms[counter].get('time'),alarm1.get('time')):
                    alarms.insert(counter, alarm1)
                    break
                else:
                    counter +=1
    logging.info("Inserted alarm to list")
def get_api_key(key_type:str)->str:
    """Gathers API data from the config.json file"""
    with open('config.json', 'r') as file:
        json_file = json.load(file)
    keys = json_file["API-keys"]
    logging.info("Got API key")
    return keys[key_type]
def get_json_info(key_type:str)->str:
    """Gathers non-API data from the config.json file"""
    with open("config.json", "r") as file:
        json_file = json.load(file)
    keys = json_file["other"]
    logging.info("Got JSON info")
    return keys[key_type]
def tts(announcement:str = "text 2 speech test"):
    """Takes in a string and uses the pyttsx3 module to speak it"""
    #pylint:disable = C0200
    for i in range(len(alarms)):
        if alarms[i]["title"] == announcement:
            del alarms[i]
            break
    try:
        engine.endLoop()
    #pylint:disable = W0702
    except:
        logging.error("end loop error pyttsx3. Program allowed to continue unaltered.")
    engine.say(announcement)
    engine.runAndWait()
    logging_string= "Said " + announcement
    logging.info(logging_string)
def get_headlines():
    """Scrapes the most recent news articles data and adds it to a global list"""
    base_url = "https://newsapi.org/v2/top-headlines?"
    api_key = get_api_key("news")
    country = "gb"
    complete_url = base_url + "country=" + country + "&apiKey=" + api_key
    # print response object
    response = requests.get(complete_url)
    json_response = response.json()
    news_dict = json_response
    articles = news_dict["articles"]
    for article in articles:
        news_articles.insert(0, {"title": article["title"],\
         "content": Markup('<a href="{}" target= "_blank">Full Article</a>'\
         .format(article["url"])),\
         "publishingTime":article["publishedAt"]})
    logging.info("Got headlines")
def get_weather()->dict:
    """Scrapes the most recent weather update data and concatenates it to a dictionary
    to be returned"""
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    api_key = get_api_key("weather")
    city_name = get_json_info("city")
    complete_url = base_url + "appid=" + api_key + "&q=" + city_name
    # print response object
    response = requests.get(complete_url)
    jsonresponse = response.json()
    mainresponse = jsonresponse["main"]
    current_temperature = round((mainresponse["temp"] - 273.15),2)
    current_temperature_f = round(((current_temperature) *(9/5) +32),2)
    current_feels_like = round((mainresponse["feels_like"] - 273.15), 2)
    current_feels_like_f = round(((current_feels_like) *(9/5) + 32), 2)
    weatherresponse = jsonresponse["weather"]
    weather_description = weatherresponse[0]["description"]
    weathertimenow = strftime("%Y-%m-%dT%H:%M", time.localtime())
    ret_string = "It is currently " + str(current_temperature)\
     + "˚C (" + str(current_temperature_f) + "˚F) and feels like "\
      + str(current_feels_like) + "˚C("+ str(current_feels_like_f)\
      +"˚F). The weather is currently " + str(weather_description) + ". "
    logging.info("Got weather")
    return {"title": "Weather Forecast", "content": ret_string, "publishingTime": weathertimenow }
def get_covid()->dict:
    """Scrapes the most recent covid update data and concatenates it to a dictionary
    to be returned"""
    area = "areaName=" + get_json_info("city")
    england_only = [area]
    api = Cov19API(filters=england_only, structure=cases_and_deaths,\
     latest_by = "newCasesByPublishDate")
    covid_response = api.get_json()
    json_response_covid = covid_response["data"]
    covidtimenow = strftime("%Y-%m-%dT", time.localtime()) + "00:00"
    covid_string = "There have been "
    if json_response_covid[0]["newCasesByPublishDate"] != 0:
        covid_string += str(json_response_covid[0]["newCasesByPublishDate"])\
         + " new cases, for a total of "\
          + str(json_response_covid[0]["cumCasesByPublishDate"]) +" cases.  "
    else:
        covid_string += " no new cases, for a total of "\
         + str(json_response_covid[0]["cumCasesByPublishDate"]) + " cases.  "
    if json_response_covid[0]["newDeathsByDeathDate"] is not None:
        covid_string += "There have been "\
         + str(json_response_covid[0]["newDeathsByDeathDate"])\
          + "new deaths, for a total of "\
           +str(json_response_covid[0]["cumDeathsByDeathDate"]) + " deaths.  "
    else:
        if json_response_covid[0]["cumDeathsByDeathDate"] is not None:
            covid_string += "There have been no new deaths, for a total of "\
             +str(json_response_covid[0]["cumDeathsByDeathDate"]) + "."
        else:
            covid_string += "There have been no deaths."
    logging.info("Got COVID-19 update")
    return {"title": "COVID-19 Update", "content": covid_string, "publishingTime": covidtimenow}
def alarm():
    """Adds an alarm from user input to a list of alarms, checks to see if the
    alarm was deleted, and schedules it into the text to speech function, as well
    as checking to see if they also requested weather or news"""
    possible_delete = request.args.get("alarm_item")
    if possible_delete is not None:
        #pylint:disable = C0200
        for i in range(len(alarms)):
            if alarms[i]["title"] == possible_delete:
                #pylint:disable = C0200
                for j in range(len(schednamelist)):
                    if schednamelist[j]["content"] == possible_delete:
                        s.cancel(schednamelist[j]["schedname"])
                        logging_string = alarms[i]["title"] + " was deleted"
                        logging.info(logging_string)
                        break
                del alarms[i]
                break
    s.run(blocking = False)
    alarm_time = request.args.get("alarm")
    alarm_content = request.args.get("two")
    nowtime = time.localtime()
    sched_content = alarm_content
    tstring = strftime("%Y-%m-%dT%H:%M", nowtime)
    if alarm_time:
        delay = (hhmm_to_seconds(str(alarm_time)) - hhmm_to_seconds(tstring))\
         + (datedifference(str(alarm_time), str(tstring)) * 86400)
        alarmstringfancy = format_string(alarm_time)
        if request.args.get("weather") is not None:
            weather = get_weather()
            sched_content += ". " + weather["content"]
            logging.info("Weather info added to alarm")
        if request.args.get("news") is not None:
            for i in range(3):
                sched_content += ". " + news_articles[i]["title"]
            logging.info("News articles added to alarm")
        covid_data = get_covid()
        sched_content += ". " + covid_data["content"]
        if delay == 0:
            tts(sched_content)
        else:
            insert_alarm_to_list({"title":alarm_content, "time": alarm_time,\
            "delay": delay, "content": alarmstringfancy})
            schedname = s.enter(int(delay), 1, tts, (sched_content, ))
            schednamelist.append({"schedname" :schedname, "content": alarm_content})
        logging.info("Alarm created")
    else:
        logging.warning("No alarm entered")
    return redirect("/index")
def notification():
    """Gets list of notifications and concatenates news, weather, and covid updates
    into a list and purges notifications older than a day, and clears the list of
    dismissed notifications at midnight"""
    possible_delete = request.args.get("notif")
    if possible_delete is not None:
        #pylint:disable = C0200
        for i in range(len(notifications)):
            if notifications[i]["title"] == possible_delete:
                dismissedlist.append(notifications[i])
                logging_string = notifications[i]["title"] + " deleted."
                logging.info(logging_string)
                del notifications[i]
                break
    get_headlines()
    for xcounter in news_articles:
        if xcounter not in notifications and xcounter not in dismissedlist:
            notifications.insert(0, xcounter)
    weatherupdate = get_weather()
    if weatherupdate not in notifications and weatherupdate not in dismissedlist:
        notifications.insert(0,weatherupdate)
    covid_update = get_covid()
    if covid_update not in notifications and covid_update not in dismissedlist:
        notifications.insert(0, covid_update)

    for counter in range(len(notifications)-1,-1,-1):
        timenow = strftime("%Y-%m-%dT%H:%M", time.localtime())
        if abs(hhmm_to_seconds(timenow) - \
        hhmm_to_seconds(notifications[counter]["publishingTime"])) >= 86400:
            logging_string = notifications[counter] + " expired."
            logging.info(logging_string)
            del notifications[counter]
    if strftime("%H:%M", time.localtime()) == "00:00":
        dismissedlist.clear()
        logging.info("Dismissed list cleared.")
    return redirect('/index')
@app.route('/')
def go_index():
    """Redirects the default page to /index"""
    logging.info("Redirected to /index")
    return redirect('/index')
@app.route('/index')
def index():
    """Renders and refreshes the webpage"""
    #required global to ensure accessing correct variable
    # pylint: disable=global-statement
    global NOTIFTIMECOUNTER
    alarm()
    if request.args.get("notif") is not None:
        notification()
    if NOTIFTIMECOUNTER == 0:
        notification()
        NOTIFTIMECOUNTER+=1
    elif NOTIFTIMECOUNTER == 60:
        logging.info("Notifications refreshed.")
        notification()
        NOTIFTIMECOUNTER =0
    else:
        NOTIFTIMECOUNTER+=1
    return render_template("template.html",
    title = "Alarm Clock", alarms = alarms, image = "clock.gif", notifications =
    notifications)


if __name__ == '__main__':
    app.run()
