from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime
import random

class TimetableProblem():
    def __init__(self, vars, domain, constraints):
        # vars = [days: {times}]
        self.vars = vars
        self.domain = domain # tuples of required classes to map
        self.constraints = constraints

    def assign(self, val, assignment):
        assignment[val[1]][val[2]] = val[0]

    def unassign(self, val, assignment):
        domain.append(val)
        assignment[val[1]][val[2]] = None

    def conflicts(val, assignment):
        c = 0
        length = val[3]
        segments = length / 30
        for i in range(1, segments+1):
            if assignment[val[1]][val[2]+i] != 0:
                c += 1
        return c

    def conflicted_vars(self, assignment):
        return [slot for slots in day for days in vars if self.conflicts(slot, assignment) > 0]

    def goal_test(self):
        if not domain:
            return True

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

def min_conflicts_value(csp, val, current):
    return argmin_random_tie(csp.domains, lambda val: csp.conflicts(val, current))

def convertDateStrToInt(dateStr):
    dt = datetime.strptime(dateStr, '%I:%M%p')
    return dt.hour * 100

def getUnitTimes(unit):

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
        if activityName in activities:
            activities[activityName].append(timeTuple)
        else:
            activities[activityName] = [timeTuple]

    print(activities)
    return activities

# main loop
if __name__ == '__main__':

    # init
    unit = 'EGB348'
    activities = getUnitTimes(unit)
    current = list()
    steps, max_steps = 0, 1000
    for i in range(5):
        current.append(dict())
        for j in range(800, 2150, 50):
            current[i][j] = 0
            print(i, j)

    csp = TimetableProblem(current, domain, constraints)
    while csp.conflicted_vars(current) and steps < max_steps:
        # assign classes
        pass
