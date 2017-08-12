from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime
import random

GAP_PENALTY = 5
DAY_PENALTY = 100

class TimetableProblem():
    def __init__(self, vars, domain):
        # vars = [days: {times}]
        self.vars = vars
        self.domain = domain # tuples of required classes to map

    def assign(self, val, assignment, name):
        length = val[2]
        segments = length / 30
        for i in range(int(segments)):
            assignment[val[0]][val[1] + i*50] = name

    def unassign(self, val, assignment):
        assignment[0][val[1]] = 0

    def conflicts(self, val, assignment):
        c = 0
        length = val[2]
        segments = length / 30
        for i in range(1, int(segments)+1):
            if assignment[0][val[1] + i * 50] != 0:
                c += 1
        return c

    def h(self, current):
        h = 0
        classFound = False
        for day in current:
            gap = 0
            for time, slot in day:
                if not classFound:
                    if slot is None:
                        continue
                    else:
                        classFound = True
                else:
                    if slot is None:
                        gap += GAP_PENALTY
                    elif gap != 0:
                        h += gap**2
                        gap = 0
                if classFound:
                    h += DAY_PENALTY




def argmin_random_tie(seq, fn):
    """Return an element with lowest fn(seq[i]) score; break ties at random.
    Thus, for all s,f: argmin_random_tie(s, f) in argmin_list(s, f)"""
    best_score = fn(seq[0])
    n = 0
    for x in seq:
        x_score = fn(x)
        if x_score < best_score:
            best, best_score = x, x_score
            n = 1
        elif x_score == best_score:
            n += 1
            if random.randrange(n) == 0:
                best = x
    return best

def min_conflicts_value(csp, domain, current):
    return argmin_random_tie(domain, lambda val: csp.conflicts(val, current))

def convertDateStrToInt(dateStr):
    dt = datetime.strptime(dateStr, '%I:%M%p')
    return dt.hour * 100 + dt.minute

def getUnitTimes(unit):

    def numTimes(list):
        return len(list)

    f = urlopen('https://qutvirtual3.qut.edu.au/qvpublic/ttab_unit_search_p.process_search?p_time_period_id=293859&p_unit_cd=' + unit)
    bsObj = BeautifulSoup(f.read(), "html.parser")
    rows = bsObj.find_all('tr')
    rows = rows[1:]
    activities = dict()
    dayConversion = {'MON' : 0, 'TUE' : 1, 'WED' : 2, 'THU' : 3, 'FRI' : 4}

    for row in rows:
        columns = row.find_all('td')

        activityName = unit + '-' + columns[1].string
        dayStr = columns[2].string
        dateStrings = columns[3].string.split(' - ')

        startTime = convertDateStrToInt(dateStrings[0])

        duration = int((convertDateStrToInt(dateStrings[1]) - startTime) * 0.6)

        timeTuple = (dayConversion[dayStr], startTime, duration)
        if activityName in activities:
            activities[activityName].append(timeTuple)
        else:
            activities[activityName] = [timeTuple]

    print(activities)
    return activities

# main loop
if __name__ == '__main__':

    # init
    units = ['EGH404', 'CAB403', 'CAB401', 'EGB342']
    unitActivities = list()
    for i in range(len(units)):
        unitActivities.append(getUnitTimes(units[i]))

    current = list()
    steps, max_steps = 0, 1000
    for i in range(5):
        current.append(dict())
        for j in range(800, 2150, 50):
            current[i][j] = None

    maxDays = 3

    csp = TimetableProblem(current, unitActivities)

    assigned = list()
    required = list()
    for unit in unitActivities:
        for activity in unit:
            required.append((activity, unit[activity][0][2]))

    while len(assigned) != len(required):
        for activities in unitActivities:
            for activity, times in activities.items():
                if activity not in assigned:
                    hConstrainedTimes = 0
                    assignmentTime = min_conflicts_value(csp, times, current)

                    # replacement if minimum conflict requires removing activity from a occupied time slot
                    # the removed activity must be marked so that it can be re-evaluated for a new conflict free time
                    if current[assignmentTime[0]][assignmentTime[1]] != 0:
                        preExisting = current[assignmentTime[0]][assignmentTime[1]]
                        assigned.remove(preExisting)
                        csp.unassign(assignmentTime, current)

                    # assign activity to timeslot and record that it has been assigned
                    csp.assign(assignmentTime, current, activity)
                    assigned.append(activity)

    print(csp.score(current, required))
    for day in current:
        print(day)