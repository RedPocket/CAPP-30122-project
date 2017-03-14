import sqlite3
import os

DATA_DIR = "/home/student/cs122-win-17-xinyih/courses-regi/mysite/courses"
DATABASE_FILENAME = os.path.join(DATA_DIR, 'redpocket.db')

def find_prerequisites(course_code):
    conn = sqlite3.connect(DATABASE_FILENAME)
    c = conn.cursor()
    query_or = "SELECT prerequisite_course_code FROM prerequisites WHERE course_code = ? and Compulsory = 'False'"
    result_or = c.execute(query_or, [course_code])
    output_or = result_or.fetchall()
    and_list = set()
    or_list = set()
    
    if output_or != []:
        for obj in output_or:
            if obj[0] is not None:
                or_list.add(obj[0])

    query_and = "SELECT prerequisite_course_code FROM prerequisites WHERE course_code=? and Compulsory='True'"
    result_and = c.execute(query_and, [course_code])
    output_and = result_and.fetchall()
    if output_and != []:
        for obj in output_and:
            if obj[0] is not None:
                and_list.add(obj[0])

    return (list(and_list), list(or_list))


def find_terms_offered(course_code):
    conn = sqlite3.connect(DATABASE_FILENAME)
    c = conn.cursor()
    query = "SELECT term1, term2, term3, term4 FROM terms_offered WHERE course_code = ?"
    result = c.execute(query, [course_code])
    output = result.fetchall()

    terms = set()
    for obj in output[0]:
        if obj is not None and obj != '\r':
            terms.add(obj)

    return list(terms)


def find_paths(acourse, courses_taken, courses_to_take):
    paths = []
    before_acourse = []
    and_list, or_list = find_prerequisites(acourse)

    if  and_list == [] and or_list == []:
        paths = [[acourse]]
    elif or_list != []:
        for obj in or_list:
            paths.append([obj, acourse])
    elif and_list != []:
        new_path = and_list + [acourse]
        paths.append(new_path)

    return paths


def find_priorities(start_quarter, seasons):
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


def one_priority(schedules, course, priorities, start_season, start_year):
    M = priorities[0]
    v1 = seasons_dict[start_season]
    v2 = seasons_dict[M]
    d = v2 - v1
    if d >= 0:
        year = int(start_year)
    else:
        year = int(start_year) + 1

    key = M + str(year)
    while key in schedules and len(schedules[key]) >= 4:
        year += 1
    
    key = M + str(year)
    if key not in schedules[key]:
        schedules[key] = [course]
        return key
    elif course not in schedules[key]:
        schedules[key] += [course]
        return key


def two_priorities(schedules, course, priorities, start_season, start_year):
    M = priorities[0]
    v1 = seasons_dict[start_season]
    v2 = seasons_dict[M]
    d = v2 - v1
    if d >= 0:
        year_1 = int(start_year)
    else:
        year_1 = int(start_year) + 1
    N = priorities[1]
    v2 = seasons_dict[M]
    d = v2 - v1
    if d >= 0:
        year_2 = int(start_year)
    else:
        year_2 = int(start_year) + 1

    key_1 = M + str(year_1)
    key_2 = N + str(year_2)

    while key_1 in schedules and key_2 in schedules and\
          len(schedules[key_1]) >=4 and len(schedules[key_2]) >=4:
        year_1 += 1
        year_2 += 1

    key_1 = M + str(year_1)
    key_2 = N + str(year_2)

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
            schedules[key_2] += [courses]
        return key_2


def three_properties(schedules, course, priorities, start_season, start_year):
    M = priorities[0]
    v1 = seasons_dict[start_season]
    v2 = seasons_dict[M]
    d = v2 - v1
    if d >= 0:
        year_1 = int(start_year)
    else:
        year_1 = int(start_year) + 1
    N = priorities[1]
    v2 = seasons_dict[M]
    d = v2 - v1
    if d >= 0:
        year_2 = int(start_year)
    else:
        year_2 = int(start_year) + 1
    S = priorities[2]
    v2 = seasons_dict[S]
    d = v2 - v1
    if d >= 0:
        year_3 = int(start_year)
    else:
        year_3 = int(start_year) + 1

    key_1 = M + str(year_1)
    key_2 = N + str(year_2)
    key_3 = S + str(year_3)

    while key_1 in schedules and key_2 in schedules and key_3 in schedules and\
          len(schedules[key_1]) >=4 and len(schedules[key_2]) >=4 and len(schedules[key_3]) >= 4:
        year_1 += 1
        year_2 += 1
        year_3 += 1

    key_1 = M + str(year_1)
    key_2 = N + str(year_2)
    key_3 = S + str(year_3)

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
                schedules[key_2] += [courses]
            return key_2
        else:
            if key_3 not in schedules:
                schedules[key_3] = [course]
                return key_3
            elif len(schedules[key_3]) < 4:
                if course not in schedules[key_3]:
                    schedules[key_3] += [courses]
                return key_3


def arrange_courses(path, start_quarter, schedule):
    for p in path:
        start_year = start_quarter[-2:]
        start_season = start_quarter[:(-3)]
        for q in p:
            priorities = find_priorities[q]
            num_priorities = 0
            for i in priorities:
                if i != None:
                    num_priorities += 1
            if num_priorities == 1:
                start_quarter = one_priority(schedule, q, priorities, start_season, start_year)
            if num_priorities == 2:
                start_quarter = two_priorities(schedule, q, priorities, start_season, start_year)
            if num_priorities == 3:
                start_quarter = three_priorities(schedule, q, priorities, start_season, start_year)
    return schedule



def create_schedule(courses_to_take, courses_taken, start_quarter):


    start_year = int(start_quarter[-2:])
    start_season = start_quarter[:(-3)]
    seasons_dict = {"Winter": 0,
                    "Spring": 1,
                    "Autumn": 2}
    
    schedule_1 = {}
    schedule_2 = {}
    l = len(courses_to_take)
    path_zero = [[]] * l
    path_one = [[]] * l

    have_second_schedule = False
    for m in range(l):
        paths = find_paths(course, courses_taken, courses_to_take)
        path_zero[m] = paths[0]
        if len(paths) == 1:
            path_one[m] = paths[0]
        else:
            have_second_schedule = True
            path_one[m] = paths[1]
    
    schedule_1 = arrange_courses(path_zero, start_quarter, schedule_1)
    
    if have_second_schedule:
        schedule_2 = arrange_courses(path_one, start_quarter, schedule_2)
        return (schedule_1, schedule_2)
    else:
        return schedule_1






















