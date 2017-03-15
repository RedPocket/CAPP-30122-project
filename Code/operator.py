import sqlite3
import os
import openpyxl
from openpyxl import load_workbook

DATA_DIR = "/home/student/cs122-win-17-xinyih/courses-regi/mysite/courses"
DATABASE_FILENAME = os.path.join(DATA_DIR, 'redpocket.db')

def find_prerequisites(course_code):
    '''
    Find prerequisites of a course
    '''
    conn = sqlite3.connect(DATABASE_FILENAME)
    c = conn.cursor()
    compulsory = set()
   
    query_compulsory = "SELECT prerequisite_course_code FROM prerequisites WHERE course_code=? and Compulsory='True'"
    result_compulsory = c.execute(query_compulsory, [course_code])
    output_compulsory = result_compulsory.fetchall()
    if output_compulsory != []:
        for obj in output_compulsory:
            if obj[0] is not None:
                compulsory.add(obj[0])

    return list(compulsory)


def find_terms_offered(course_code):
    '''
    Find terms-offered for a course
    '''
    conn = sqlite3.connect(DATABASE_FILENAME)
    c = conn.cursor()
    query = "SELECT term1, term2, term3, term4 FROM terms_offered WHERE course_code = ?"
    result = c.execute(query, [course_code])
    output = result.fetchall()

    terms = set()
    if len(output) != 0:
        for obj in output[0]:
            if obj is not None and obj != '\r':
                terms.add(obj)

    return list(terms)


def find_paths(acourse, courses_taken, courses_to_take):
    '''
    Create a list of sequence of courses 
    in terms of prerequisites
    '''
    paths = []
    compulsory_list = find_prerequisites(acourse)

    if compulsory_list is []:
        paths = [[acourse]]
    if compulsory_list is not []:
        subpath = set()
        for obj in compulsory_list:
            if obj is not None:
                if obj not in courses_taken and obj not in courses_to_take:
                    subpath.add(obj)
        if len(subpath) != 0:
            paths.append(list(subpath)+[acourse])
        else:
            paths = [[acourse]]
    return paths


def find_priorities(start_quarter, seasons):
    '''
    Find an order of seasons by which we 
    try putting a course into schedule
    '''
    priorities = [None]*3
    if start_quarter == "Winter":
        if "Winter" in seasons:
            priorities[0] = "Winter"
            if "Spring" in seasons:
                priorities[1] = "Spring"
                if "Autumn" in seasons:
                    priorities[2] = "Autumn"
            elif "Autumn" in seasons:
                priorities[1] = "Autumn"
        elif "Spring" in seasons:
            priorities[0] = "Spring"
            if "Autumn" in seasons:
                priorities[1] = "Autumn"
        else:
            priorities[0] = "Autumn"

    elif start_quarter == "Spring":
        if "Spring" in seasons:
            priorities[0] = "Spring"
            if "Autumn" in seasons:
                priorities[1] = "Autumn"
                if "Winter" in seasons:
                    priorities[2] = "Winter"
            elif "Winter" in seasons:
                priorities[1] = "Winter"
        elif "Autumn" in seasons:
            priorities[0] = "Spring"
            if "Winter" in seasons:
                priorities[1] = "Winter"
        else:
            priorities[0] = "Winter"
    else:
        if "Autumn" in seasons:
            priorities[0] = "Autumn"
            if "Winter" in seasons:
                priorities[1] = "Winter"
                if "Spring" in seasons:
                    priorities[2] = "Spring"
            elif "Spring" in seasons:
                priorities[1] = "Spring"
        elif "Winter" in seasons:
            priorities[0] = "Winter"
            if "Spring" in seasons:
                priorities[1] = "Spring"
        else:
            priorities[0] = "Spring"

    return priorities


def one_priority(schedules, course, priorities, start_season, start_year, seasons):
    '''
    Put into schedule the course that only has one term-offered
    '''
    M = priorities[0]
    v1 = seasons[start_season]
    v2 = seasons[M]
    d = v2 - v1
    if d >= 0:
        year = int(start_year)
    else:
        year = int(start_year) + 1

    key = M + ' ' + str(year)
    while key in schedules and len(schedules[key]) >= 4:
        year += 1
        key = M + ' ' + str(year)

    if key not in schedules:
        schedules[key] = [course]
        return key
    elif course not in schedules[key]:
        schedules[key] += [course]
        return key


def two_priorities(schedules, course, priorities, start_season, start_year, seasons):
    '''
    Put into schedule the course that only has two terms-offered
    '''
    M = priorities[0]
    v1 = seasons[start_season]
    v2 = seasons[M]
    d = v2 - v1
    if d >= 0:
        year_1 = int(start_year)
    else:
        year_1 = int(start_year) + 1
    N = priorities[1]
    v2 = seasons[M]
    d = v2 - v1
    if d >= 0:
        year_2 = int(start_year)
    else:
        year_2 = int(start_year) + 1

    key_1 = M + ' ' + str(year_1)
    key_2 = N + ' ' + str(year_2)

    while key_1 in schedules and key_2 in schedules and\
          len(schedules[key_1]) >=4 and len(schedules[key_2]) >=4:
        year_1 += 1
        year_2 += 1
        key_1 = M + ' ' + str(year_1)
        key_2 = N + ' ' + str(year_2)

    if key_1 not in schedules:
        schedules[key_1] = [course]
        return key_1
    elif len(schedules[key_1]) < 4:
        if course not in schedules[key_1]:
            schedules[key_1] += [course]
        return key_1
    elif key_2 not in schedules:
        schedules[key_2] = [course]
        return key_2
    elif len(schedules[key_2]) < 4:
        if course not in schedules[key_2]:
            schedules[key_2] += [course]
        return key_2


def three_priorities(schedules, course, priorities, start_season, start_year, seasons):
    '''
    Put into schedule the course that has three terms-offered
    '''
    M = priorities[0]
    v1 = seasons[start_season]
    v2 = seasons[M]
    d = v2 - v1
    if d >= 0:
        year_1 = int(start_year)
    else:
        year_1 = int(start_year) + 1
    N = priorities[1]
    v2 = seasons[M]
    d = v2 - v1
    if d >= 0:
        year_2 = int(start_year)
    else:
        year_2 = int(start_year) + 1
    S = priorities[2]
    v2 = seasons[S]
    d = v2 - v1
    if d >= 0:
        year_3 = int(start_year)
    else:
        year_3 = int(start_year) + 1

    key_1 = M + ' ' + str(year_1)
    key_2 = N + ' ' + str(year_2)
    key_3 = S + ' ' + str(year_3)

    while key_1 in schedules and key_2 in schedules and key_3 in schedules and\
          len(schedules[key_1]) >=4 and len(schedules[key_2]) >=4 and len(schedules[key_3]) >= 4:
        year_1 += 1
        year_2 += 1
        year_3 += 1
        key_1 = M + ' ' + str(year_1)
        key_2 = N + ' ' + str(year_2)
        key_3 = S + ' ' + str(year_3)

    if key_1 not in schedules:
        schedules[key_1] = [course]
        return key_1
    elif len(schedules[key_1]) < 4:
        if course not in schedules[key_1]:
            schedules[key_1] += [course]
        return key_1
    else:
        if key_2 not in schedules:
            schedules[key_2] = [course]
            return key_2
        elif len(schedules[key_2]) < 4:
            if course not in schedules[key_2]:
                schedules[key_2] += [course]
            return key_2
        else:
            if key_3 not in schedules:
                schedules[key_3] = [course]
                return key_3
            elif len(schedules[key_3]) < 4:
                if course not in schedules[key_3]:
                    schedules[key_3] += [course]
                return key_3


def arrange_courses(path, start_quarter, schedule):
    '''
    Arrange the courses by terms
    '''
    copy_start_quarter = start_quarter
    seasons_dict = {"Winter": 0,
                    "Spring": 1,
                    "Autumn": 2}
    for p in path:
        start_year = start_quarter[-2:]
        start_season = start_quarter[:(-3)]
        for q in p:
            if q != '':
                seasons = find_terms_offered(q)
                if len(seasons) != 0:
                    priorities = find_priorities(start_quarter, seasons)
                    num_priorities = 0
                    for i in priorities:
                        if i != None:
                            num_priorities += 1
                    if num_priorities == 1:
                        start_quarter = one_priority(schedule, q, priorities, start_season, start_year, seasons_dict)
                    if num_priorities == 2:
                        start_quarter = two_priorities(schedule, q, priorities, start_season, start_year, seasons_dict)
                    if num_priorities == 3:
                        start_quarter = three_priorities(schedule, q, priorities, start_season, start_year, seasons_dict)
        start_quarter = copy_start_quarter
    return schedule


def sort_schedule_by_key(schedule, start_season,start_year):
    '''
    Sort the schedule by terms
    '''
    new_schedule = []
    key_and_weight = {}
    weights = []

    if start_season == "Winter":
        seasons_dict = {"Winter": 0,
                        "Spring": 1,
                        "Autumn": 2}
    if start_season == "Spring":
        seasons_dict = {"Spring": 0, 
                        "Autumn": 1,
                        "Winter": 3}
    if start_season == "Autumn":
        seasons_dict = {"Autumn": 0,
                        "Winter": 1,
                        "Spring": 2}

    for key, value in schedule.items():
        weight_of_key = seasons_dict[key[:(-3)]] + (int(key[(-2):])-start_year)*3
        key_and_weight[str(weight_of_key)] = key
        weights.append(weight_of_key)

    new_weights = sorted(weights)

    for i in range(len(new_weights)):
        key = key_and_weight[str(new_weights[i])]
        value = ", ".join(schedule[key])
        new_schedule.append((key,value))

    return new_schedule


def create_schedule(courses_to_take, courses_taken, start_quarter):
    '''
    Create one schedule
    '''
    start_year = int(start_quarter[-2:])
    start_season = start_quarter[:(-3)]
    
    schedule_1 = {}
    l = len(courses_to_take)
    path_zero = [[]] * l
    path_one = [[]] * l

    have_second_schedule = False
    for m in range(l):
        if courses_to_take[m] is not None:
            paths = find_paths(courses_to_take[m], courses_taken, courses_to_take)
            path_zero[m] = paths[0]
            if len(paths) == 1:
                path_one[m] = paths[0]
            else:
                have_second_schedule = True
                path_one[m] = paths[1]
    
    schedule_1 = arrange_courses(path_zero, start_quarter, schedule_1)
    ordered_schedule = sort_schedule_by_key(schedule_1, start_season, start_year)
    
    return ordered_schedule























