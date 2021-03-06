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


    def __init__(self, state, unplacedUnits):
        self.days = state
        self.unplacedUnits = unplacedUnits

    def __eq__(self, other):
        return self.days == other.days

    def __hash__(self):
        return functools.reduce(operator.xor, [hash(frozenset(day)) for day in self.days])

    def copy(self):
        newDays = list()
        for day in self.days:
            newDays.append(dict(day))
        return Timetable(newDays, list(self.unplacedUnits))

class TimetableProblem(Problem):

    def __init__(self, initial, domain, constraints):
        self.initial = initial
        self.domain = domain
        self.constraints = constraints

        self.GAP_PENALTY = constraints['gapsWeight']
        self.DAY_PENALTY = 100
        self.NODAY_PENALTY = constraints['noDayWeight'] * 60

        self.EARLY_PENALTY = 60 * constraints['startWeight']
        self.LATE_PENALTY = 60 * constraints['endWeight']

    def actions(self, timetable):
        seen = set()
        state = timetable.days
        actions = list()

        for activity in timetable.unplacedUnits:
            for subject in self.domain:
                if activity in subject:
                    for time in subject[activity]:
                        if not conflicts(time, state):
                            actions.append((activity, None, time))
                            break

        if len(actions) is 0:
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
        if oldPos is not None:
            for time in range(oldPos[1], oldPos[1] + oldPos[2], 50):
                state[oldPos[0]][time] = None
        else:
            cp.unplacedUnits.remove(action[0])

        for time in range(newPos[1], newPos[1] + newPos[2], 50):
            state[newPos[0]][time] = action[0]

        return cp

    def h(self, node):
        def day2int(days):
            ints = list()
            map = {'Monday':0, 'Tuesday':1, 'Wednesday':2, 'Thursday':3, 'Friday':4}
            for day in days:
                ints.append(map[day])
            return ints

        h = 0
        noDays = None
        startTime = int(self.constraints['startTime'])
        endTime = int(self.constraints['endTime'])
        isLate = False
        if self.constraints['noDays'][0] != '':
            noDays = day2int(self.constraints['noDays'])
        for d, day in enumerate(node.state.days):
            classFound = False
            gap = 0
            for time, slot in day.items():
                if not classFound:
                    if slot is None:
                        continue
                    elif not (self.constraints['watchOnline'] and 'LEC' in slot.split('-')[1]):
                        if int(time) < startTime:
                            h += self.EARLY_PENALTY
                        classFound = True
                else:
                    if slot is None:
                        gap += self.GAP_PENALTY
                    elif gap != 0:
                        if int(time) >= endTime and not isLate:
                            h += self.LATE_PENALTY
                            isLate = True
                        h += gap**2
                        gap = 0
            if classFound:
                if noDays and d in noDays:
                    h += self.NODAY_PENALTY
            else:
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

def createEmptyDays():
    current = list()
    for i in range(5):
        current.append(dict())
        for j in range(800, 2200, 50):
            current[i][j] = None
    return current

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

    return activities

# main loop
if __name__ == '__main__':


    # init
    #units = ['CAB403', 'CAB401', 'CAB240', 'EGH404']

    # determine timetable constraints
    constraints = dict()
    print('Hi! Thanks for using the QUT Auto-Timetabler. Please answer the following questions to help us optimise your timetable to suit your needs.\n')
    units = input('What units are you studying this semester? ').split(',')
    constraints['startTime'] = input('What time would you like your days to preferably start? (HHMM) ')
    constraints['startWeight'] = int(input('On a scale of 0-5, how strongly would you prefer this? '))
    constraints['endTime'] = input('What time would you like your days to preferably end? (HHMM) ')
    constraints['endWeight'] = int(input('On a scale of 0-5, how strongly would you prefer this? '))
    daysRaw = input('Are there any days you would strongly prefer not to be at uni? ' )
    if daysRaw != '':
        constraints['noDays'] = daysRaw.split(',')
        constraints['noDayWeight'] = int(input('On a scale of 0-5, how strongly would you prefer this? '))
    else:
        constraints['noDays'] = ['']
        constraints['noDayWeight'] = 0
    constraints['gapsWeight'] = int(input('On a scale of 0-5, how much do you dislike gaps in your timetable? '))
    watchOnlineRaw = input('Are you open to watching lectures online? (Y/N)').capitalize()
    constraints['watchOnline'] = watchOnlineRaw == 'Y' or watchOnlineRaw == 'YES'

    unitActivities = generateClasses(units, 2)

    # create default no conflict solution
    emptyDays = createEmptyDays()

    activityList = list()
    for unitActivity in unitActivities:
        for key in unitActivity.keys():
            activityList.append(key)

    timetable = Timetable(emptyDays, activityList) # add unplaced units
    print('Getting your optimal timetables...')
    tp = TimetableProblem(timetable, unitActivities, constraints)
    bestNodes = best_first_graph_search(tp, lambda s: tp.h(s))
    i = 1
    for node in bestNodes:
        if node is not None:
            print('\n############################## SOLUTION ' + str(i) + ' ##############################\n')
            print(node.state)
            # print(tp.h(node))
            for unit in node.state.unplacedUnits:
                print('Could not assign the unit: ' + unit)
            i += 1
        else:
            break
