from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime

def convertDateStrToInt(dateStr):
    dt = datetime.strptime(dateStr, '%I:%M%p')
    return dt.hour * 100

unit = 'EGB342'

f = urlopen('https://qutvirtual3.qut.edu.au/qvpublic/ttab_unit_search_p.process_search?p_time_period_id=293859&p_unit_cd=' + unit)
bsObj = BeautifulSoup(f.read(), "html.parser")
rows = bsObj.find_all('tr')
rows = rows[1:]
activities = dict()
dayConversion = {'MON' : 0, 'TUE' : 1, 'WED' : 2, 'THU' : 3, 'FRI' : 4}

for row in rows:
    columns = row.find_all('td')

    activityName = columns[1].string
    dayStr = columns[2].string
    dateStrings = columns[3].string.split(' - ')

    startTime = convertDateStrToInt(dateStrings[0])

    duration = int((convertDateStrToInt(dateStrings[1]) - startTime) * 0.6)

    timeTuple = (dayConversion[dayStr], startTime, duration)
    print(activities)
    if activityName in activities:
        activities[activityName].append(timeTuple)
    else:
        activities[activityName] = [timeTuple]

print(activities)