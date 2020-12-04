# alarm_clock

alarm_clock is a program used to run a smart alarm clock designed to keep one updated on the world during the time of COVID-19. It includes the ability to create alarms for any time and day, which will then read aloud the contents of the alarm, as well as providing notifications of weather, news, and the most recent COVID-19 updates each hour. This program was designed as the final project for ECM1400 at the University of Exeter.

## Prerequisites
Ensure you're running Python 3.7 or higher, that your internet connection is stable, as well as making sure to access config.json and update it with your personal API keys for [OpenWeather](https://openweathermap.org/) and [NewsAPI](https://newsapi.org/), and your city of choice in the UK.
## Installation

Ensure you download the following packages:
```bash
pip install pyttsx3
pip install Flask
pip install uk_covid19
python -m pip install requests
```

## Usage

While in your terminal:

```bash
python3 alarm_clock.py
```
![image](/static/images/alarm.png)

Enter a date, time, and label to create an alarm, and choose whether or not you'd like a weather or news brief with your alarm. You can dismiss an alarm or notification at any time by clicking the x. Notifications refresh every hour, with the COVID-19 data being updated by the government at midnight.

## License
Author: Jennifer Schofield\
Date: 4-12-2020\
Specification Creator: Dr. Matthew Collison\
[MIT](https://choosealicense.com/licenses/mit/) © Jennifer Schofield
