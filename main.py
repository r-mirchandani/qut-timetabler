from urllib.request import urlopen
from bs4 import BeautifulSoup
from datetime import datetime
import random
from search import *
import functools
import operator
from tabulate import tabulate

class Timetable:
    def __str__(self):
        times = ['8:00', '8:30', '9:00', '9:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '1:00', '1:30', '2:00', '2:30',
                 '3:00', '3:30', '4:00', '4:30', '5:00', '5:30', '6:00', '6:30', '7:00', '7:30', '8:00', '8:30', '9:00', '9:30']
        rows = list()
        for i in range(len(times)):
            rows.append([times[i]])
            for j in range(len(self.days)):
                rows[i].append(self.days[j][800 + 50 * i])

        return tabulate(rows, ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'], tablefmt='grid')


    def __init__(self, state):
        self.days = state

    def __eq__(self, other):
        return self.days == other.days

    def __hash__(self):
        return functools.reduce(operator.xor, [hash(frozenset(day)) for day in self.days])

    def copy(self):
        newDays = list()
        for day in self.days:
            newDays.append(dict(day))
        return Timetable(newDays)

class TimetableProblem(Problem):

    def __init__(self, inital, domain):
        self.initial = inital
        self.domain = domain
        self.GAP_PENALTY = 5
        self.DAY_PENALTY = 100

    def actions(self, timetable):
        seen = set()
        state = timetable.days
        actions = list()
        for d, day in enumerate(state):
            for time, activity in day.items():
                if activity is not None:
                    if activity not in seen:
                        seen.add(activity)
                        for subject in self.domain:
                            if activity in subject:
                                others = [t for t in subject[activity] if (t[1] != time and t[0] != d)]
                                for t in others:
                                    if not conflicts(t, state):
                                        actions.append((activity, (d, time, t[2]), t))
                                break
        return actions

    def result(self, timetable, action):

        cp = timetable.copy()

        state = cp.days
        oldPos = action[1]
        newPos = action[2]

        for time in range(oldPos[1], oldPos[1] + oldPos[2], 50):
            state[oldPos[0]][time] = None

        for time in range(newPos[1], newPos[1] + newPos[2], 50):
            state[newPos[0]][time] = action[0]

        return cp

    def h(self, node):
        h = 0
        for day in node.state.days:
            classFound = False
            gap = 0
            for time, slot in day.items():
                if not classFound:
                    if slot is None:
                        continue
                    else:
                        classFound = True
                else:
                    if slot is None:
                        gap += self.GAP_PENALTY
                    elif gap != 0:
                        h += gap**2
                        gap = 0
            if classFound:
                h += self.DAY_PENALTY
        return h

    def goal_test(self, state):
        return False


def assign(val, assignment, name):
    length = val[2]
    segments = length / 50
    for i in range(int(segments)):
        assignment[val[0]][val[1] + i*50] = name

def unassign(val, assignment, preExisiting):
    for time in assignment[val[0]]:
        if time == preExisiting:
            time = None

def conflicts(val, assignment):
    length = val[2]
    segments = int(length / 50)
    for i in range(segments):
        if assignment[val[0]][val[1] + i * 50] is not None:
            return 1
    return 0

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
    random.seed(hash(time()))
    current = list()
    steps, max_steps = 0, 1000
    for i in range(5):
        current.append(dict())
        for j in range(800, 2200, 50):  # TODO: This was 2150 as max and I changed the end time from 9 to 10,
            current[i][j] = None        # TODO this would change to 2250 but I cannot see why it needs to go past 2200

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
                    if conflicts(assignmentTime, current):
                        preExisting = current[assignmentTime[0]][assignmentTime[1]]
                        assigned.remove(preExisting)
                        unassign(assignmentTime, current, preExisting)

                    # assign activity to timeslot and record that it has been assigned
                    assign(assignmentTime, current, activity)
                    assigned.append(activity)

    return current

def generateClasses(units, semester):
    unitActivities = list()
    for unit in units:
        unitActivities.append(getUnitTimes(unit, semester))
    return unitActivities

def findRows(url, unit):
    f = urlopen(url + unit)
    bsObj = BeautifulSoup(f.read(), "html.parser")
    return bsObj.find_all('tr')

def getUnitTimes(unit, semester):
    semesterCodes = ['3598', '293859', '3597', '293860']
    rows = findRows('https://qutvirtual3.qut.edu.au/qvpublic/ttab_unit_search_p.process_search?p_time_period_id='
                    + semesterCodes[semester - 1] + '&p_unit_cd=', unit)
    if len(rows) is 0:
        rows = findRows('https://qutvirtual3.qut.edu.au/qvpublic/ttab_unit_search_p.process_search?p_time_period_id='
                        + semesterCodes[semester + 1] + '&p_unit_cd=', unit)
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
    units = ['AMB240', 'AMB202', 'KCB205', 'KJB103']
    unitActivities = generateClasses(units, 2)

    # create default no conflict solution
    noConflict = createNoConflictSolution(unitActivities)
    print('\n')
    for days in noConflict:
        print(days)

    timetable = Timetable(noConflict)
    print('Calculating...')
    tp = TimetableProblem(timetable, unitActivities)
    bestNodes = best_first_graph_search(tp, lambda s: tp.h(s))
    i = 1
    for node in bestNodes:
        if node is not None:
            print('\n############################## SOLUTION ' + str(i) + ' ##############################\n')
            print(node.state)
            i += 1
        else:
            break
