from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime
import random
from search import *

class TimetableProblem(Problem):

    GAP_PENALTY = 5
    DAY_PENALTY = 100

    def __init__(self, inital, domain):
        self.initial = inital
        self.domain = domain

    def actions(self, state):
        actions = list()
        for d, day in enumerate(state):
            for time, activity in day.items():
                if activity is not None:
                    for subject in self.domain:
                        if activity in subject:
                            others = [t for t in subject[activity] if (t[1] != time and t[0] != d)]
                            for t in others:
                                actions.append((activity, t))

    def result(self, state, action):
        oldPos = action[1]
        newPos = action[2]

        for time in range(oldPos[1], oldPos[1] + oldPos[2], 50):
            state[oldPos[0]][time] = None

        for time in range(newPos[1], newPos[1] + newPos[2], 50):
            state[newPos[0]][time] = action[0]

    def h(self, state):
        h = 0
        classFound = False
        for day in state:
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



def assign(val, assignment, name):
    length = val[2]
    segments = length / 50
    for i in range(int(segments)):
        assignment[val[0]][val[1] + i*50] = name

def unassign(val, assignment):
    assignment[0][val[1]] = 0

def conflicts(val, assignment):
    c = 0
    length = val[2]
    segments = length / 50
    for i in range(1, int(segments)+1):
        if assignment[0][val[1] + i * 50] != 0:
            c += 1
    return c

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

def min_conflicts_value(domain, current):
    return argmin_random_tie(domain, lambda val: conflicts(val, current))

def convertDateStrToInt(dateStr):
    dt = datetime.strptime(dateStr, '%I:%M%p')
    return dt.hour * 100 + int(dt.minute * 5/3.0)

def createNoConflictSolution(unitActivities):
    current = list()
    steps, max_steps = 0, 1000
    for i in range(5):
        current.append(dict())
        for j in range(800, 2150, 50):
            current[i][j] = None

    assigned = list()
    required = list()
    for unit in unitActivities:
        for activity in unit:
            required.append((activity, unit[activity][0][2]))

    while len(assigned) != len(required):
        for activities in unitActivities:
            for activity, times in activities.items():
                if activity not in assigned:
                    # pick a class to assign based on minimum conflicts
                    assignmentTime = min_conflicts_value(times, current)

                    # replacement if minimum conflict requires removing activity from a occupied time slot
                    # the removed activity must be marked so that it can be re-evaluated for a new conflict free time
                    if current[assignmentTime[0]][assignmentTime[1]] is not None:
                        preExisting = current[assignmentTime[0]][assignmentTime[1]]
                        assigned.remove(preExisting)
                        unassign(assignmentTime, current)

                    # assign activity to timeslot and record that it has been assigned
                    assign(assignmentTime, current, activity)
                    assigned.append(activity)

    return current

def generateClasses(units):
    unitActivities = list()
    for i in range(len(units)):
        unitActivities.append(getUnitTimes(units[i]))
    return unitActivities

def getUnitTimes(unit):

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

        duration = (convertDateStrToInt(dateStrings[1]) - startTime)

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
    unitActivities = generateClasses(units)

    # create default no conflict solution
    noConflict = createNoConflictSolution(unitActivities)
    print('\n')
    for days in noConflict:
        print(days)