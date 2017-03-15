from django.shortcuts import render, redirect
from django.http import HttpResponse
from django import forms
import sqlite3
import os
from .operator import *
from django.template import RequestContext
import django_excel as excel


DATA_DIR = "/home/student/cs122-win-17-xinyih/courses-regi/mysite/courses"
DATABASE_FILENAME = os.path.join(DATA_DIR, 'redpocket.db')
conn = sqlite3.connect(DATABASE_FILENAME)
c = conn.cursor()
query_major = "SELECT DISTINCT track_name FROM major_requirements"
results_major = c.execute(query_major, [])
output_major = results_major.fetchall()

def build_drop_down(options):
  '''
  Build a list of tuples
  '''
  new_options = []
  for option in options:
    x = option[0]
    if x is not None:
      new_options.append((x, x))
  return new_options

MAJORS = build_drop_down(output_major)


def build_checkbox_list(options):
  '''
  Build a list from a list of one tuple
  '''
  new_options = set()
  for option in options[0]:
      if option is not None and len(option)!=0:
        new_options.add(option)
  return list(new_options)

def build_list(options):
  '''
  Build a list from a list of tuples
  '''
  new_options = set()
  for option in options:
    if option[0] is not None:
      new_options.add(option[0])
  return list(new_options)


def choose_major(request):
  '''
  Choose a major from all the major programs
  '''
  conn = sqlite3.connect(DATABASE_FILENAME)
  c = conn.cursor()
  query = "DELETE FROM user_inputs"
  result = c.execute(query, [])
  conn.commit()

  context = {"choices": MAJORS}
  return render(request, "major.html", context)


def choose_majortaken(request):
  '''
  Choose courses for a major that a user has taken 
  '''
  conn = sqlite3.connect(DATABASE_FILENAME)
  c = conn.cursor()

  selected_major = request.GET['major_choice']
  start_quarter = request.GET['start_quarter']

  query_quarter = "INSERT INTO user_inputs (start_quarter) VALUES (?)"
  result_quarter = c.execute(query_quarter, [start_quarter])
  conn.commit()
  # select prescribed courses
  query_total = "SELECT course_code FROM program_elective WHERE program_name = (SELECT program_name FROM major_requirements WHERE track_name= ?)"
  result_total = c.execute(query_total, [selected_major])
  output_total = result_total.fetchall()
  TOTAL = build_list(output_total)

  query_pre = "SELECT Requirement0, Requirement1, Requirement2, Requirement3, Requirement4, Requirement5, Requirement6, Requirement7, Requirement8, Requirement9 FROM major_requirements_only WHERE track_name=?"
  results_pre = c.execute(query_pre, [selected_major])
  output_pre = results_pre.fetchall()
  PRESCRIBED = build_checkbox_list(output_pre)

  ELECTIVE = [x for x in TOTAL if x not in PRESCRIBED]

  l1 = len(PRESCRIBED)
  x = "(?), " * l1
  x = x[:-2]
  query_1 = "INSERT INTO user_inputs (major_pre_courses) VALUES " + x 
  result = c.execute(query_1, PRESCRIBED)
  conn.commit()
  # insert elective courses for the major into database
  l2 = len(ELECTIVE)
  y = "(?), " * l2
  y = y[:-2]
  query_2 = "INSERT INTO user_inputs (major_elec_courses) VALUES " + y 
  result = c.execute(query_2, ELECTIVE)
  conn.commit()

  context = {"PRESCRIBED": PRESCRIBED, "ELECTIVE": ELECTIVE}
  return render(request, "major_courses_taken.html", context)


def choose_majortotake(request):
  '''
  Choose courses for a major that a user wants to take
  '''
  selected_pre_courses = request.GET.getlist("pre_course")
  selected_elec_courses = request.GET.getlist("elec_course")
  other_taken_courses = []
  for i in range(5):
    other_taken_courses.append(request.GET["major_other_"+str(i)])

  rest_pre_courses = set()
  rest_elec_courses = set()

  conn = sqlite3.connect(DATABASE_FILENAME)
  c = conn.cursor()
  # insert courses the user has taken into database
  l1 = len(selected_pre_courses)
  if l1 != 0:
    x = "(?), " * l1
    x = x[:-2]
    query_1 = "INSERT INTO user_inputs (courses_taken) VALUES " + x 
    result = c.execute(query_1, selected_pre_courses)
    conn.commit()

  l2 = len(selected_elec_courses)
  if l2 != 0:
    y = "(?), " * l2
    y = y[:-2]
    query_2 = "INSERT INTO user_inputs (courses_taken) VALUES " + y
    result = c.execute(query_2, selected_elec_courses)
    conn.commit()

  l3 = len(other_taken_courses)
  if l3 != 0:
    z = "(?), " * l3
    z = z[:-2]
    query_3 = "INSERT INTO user_inputs (courses_taken) VALUES " + z
    result = c.execute(query_3, other_taken_courses)
    conn.commit()
  
  query = "SELECT major_pre_courses FROM user_inputs"
  results = c.execute(query, [])
  output_pre = results.fetchall()
  
  for obj in output_pre:
    if obj[0] is not None and obj[0] != "None":
      if obj[0] not in selected_pre_courses:
        rest_pre_courses.add(obj[0])

  query = "SELECT major_elec_courses FROM user_inputs"
  results = c.execute(query, [])
  output_elec = results.fetchall()

  for obj in output_elec:
    if obj[0] is not None and obj[0] != "None":
      if obj[0] not in selected_elec_courses:
        rest_elec_courses.add(obj[0])

  context = {"rest_pre_courses": list(rest_pre_courses), "rest_elec_courses": list(rest_elec_courses)}
  return render(request, "major_courses_to_take.html", context)

query_minor = "SELECT DISTINCT track_name FROM minor_requirements"
results_minor = c.execute(query_minor, [])
output_minor = results_minor.fetchall()
MINORS = build_drop_down(output_minor)

class MinorProgramForm(forms.Form):
  minor_program = forms.ChoiceField(label='Minor Programs', choices=MINORS, required=True)

def choose_minor(request):
  '''
  Choose a minor from all minor programs 
  '''
  conn = sqlite3.connect(DATABASE_FILENAME)
  c = conn.cursor()
  selected_pre_courses = request.GET.getlist("pre_course")
  selected_elec_courses = request.GET.getlist("elec_course")
  other_to_take_courses = []
  for i in range(5):
    other_to_take_courses.append(request.GET["major_other_"+str(i)])
  rest_pre_courses = set()
  rest_elec_courses = set()

  l1 = len(selected_pre_courses)
  if l1 != 0:
    x = "(?), " * l1
    x = x[:-2]
    query_1 = "INSERT INTO user_inputs (courses_to_take) VALUES " + x 
    result = c.execute(query_1, selected_pre_courses)
    conn.commit()

  l2 = len(selected_elec_courses)
  if l2 != 0:
    y = "(?), " * l2
    y = y[:-2]
    query_2 = "INSERT INTO user_inputs (courses_to_take) VALUES " + y
    result = c.execute(query_2, selected_elec_courses)
    conn.commit()

  l3 = len(other_to_take_courses)
  if l3 != 0:
    z = "(?), " * l3
    z = z[:-2]
    query_3 = "INSERT INTO user_inputs (courses_to_take) VALUES " + z
    result = c.execute(query_3, other_to_take_courses)
    conn.commit()

  context = {'choices': MINORS}
  return render(request, "minor.html", context)

def choose_minortaken(request):
  '''
  Choose courses for a minor that a user has taken 
  '''
  selected_minor = request.GET['minor_choice']
  if selected_minor is None:
    PRESCRIBED = False
    ELECTIVE = False
  else:
    conn = sqlite3.connect(DATABASE_FILENAME)
    c = conn.cursor()
  
    query_total = "SELECT course_code FROM program_elective WHERE program_name = (SELECT program_name FROM minor_requirements WHERE track_name= ?)"
    result_total = c.execute(query_total, [selected_minor])
    output_total = result_total.fetchall()
    TOTAL = build_list(output_total)

    query_pre = "SELECT Requirement0, Requirement1, Requirement2, Requirement3, Requirement4, Requirement5, Requirement6, Requirement7, Requirement8 FROM minor_requirements_only WHERE track_name=?"
    results_pre = c.execute(query_pre, [selected_minor])
    output_pre = results_pre.fetchall()
    PRESCRIBED = build_checkbox_list(output_pre)
    print(PRESCRIBED)

    ELECTIVE = [x for x in TOTAL if x not in PRESCRIBED]

    l1 = len(PRESCRIBED)
    if l1 != 0 and PRESCRIBED[0]!="check electives":
      x = "(?), " * l1
      x = x[:-2]
      query_1 = "INSERT INTO user_inputs (minor_pre_courses) VALUES " + x 
      result = c.execute(query_1, PRESCRIBED)
      conn.commit()
    else:
      PRESCRIBED = False
  
    l2 = len(ELECTIVE)
    if l2 != 0 and ELECTIVE[0]!="check electives":
      y = "(?), " * l2
      y = y[:-2]
      query_2 = "INSERT INTO user_inputs (minor_elec_courses) VALUES " + y 
      result = c.execute(query_2, ELECTIVE)
      conn.commit()
    else:
      ELECTIVE = False
  
    context = {"PRESCRIBED": PRESCRIBED, "ELECTIVE": ELECTIVE}
    return render(request, "minor_courses_taken.html", context)


def choose_minortotake(request):
  '''
  Choose courses for a minor that a user wants to take
  '''
  selected_pre_courses = request.GET.getlist("pre_course")
  selected_elec_courses = request.GET.getlist("elec_course")
  other_taken_courses = []
  for i in range(5):
    other_taken_courses.append(request.GET["minor_other_"+str(i)])

  rest_pre_courses = set()
  rest_elec_courses = set()

  conn = sqlite3.connect(DATABASE_FILENAME)
  c = conn.cursor()
  l1 = len(selected_pre_courses)
  if l1 != 0:
    x = "(?), " * l1
    x = x[:-2]
    query_1 = "INSERT INTO user_inputs (courses_taken) VALUES " + x 
    result = c.execute(query_1, selected_pre_courses)
    conn.commit()

  l2 = len(selected_elec_courses)
  if l2 != 0:
    y = "(?), " * l2
    y = y[:-2]
    query_2 = "INSERT INTO user_inputs (courses_taken) VALUES " + y
    result = c.execute(query_2, selected_elec_courses)
    conn.commit()

  l3 = len(other_taken_courses)
  if l3 != 0:
    z = "(?), " * l3
    z = z[:-2]
    query_3 = "INSERT INTO user_inputs (courses_taken) VALUES " + z
    result = c.execute(query_3, other_taken_courses)
    conn.commit()

  query = "SELECT minor_pre_courses FROM user_inputs"
  results = c.execute(query, [])
  output_pre = results.fetchall()
  
  for obj in output_pre:
    if obj[0] is not None and obj[0] != "None":
      if obj[0] not in selected_pre_courses:
        rest_pre_courses.add(obj[0])

  query = "SELECT minor_elec_courses FROM user_inputs"
  results = c.execute(query, [])
  output_elec = results.fetchall()

  for obj in output_elec:
    if obj[0] is not None and obj[0] != "None":
      if obj[0] not in selected_elec_courses:
        rest_elec_courses.add(obj[0])

  context = {"rest_pre_courses": list(rest_pre_courses), "rest_elec_courses": list(rest_elec_courses)}
  return render(request, "minor_courses_to_take.html", context)


def schedules(request):
  '''
  Create a course schedule 
  '''
  conn = sqlite3.connect(DATABASE_FILENAME)
  c = conn.cursor()
  selected_pre_courses = request.GET.getlist("pre_course")
  selected_elec_courses = request.GET.getlist("elec_course")
  other_to_take_courses = []
  for i in range(5):
    if request.GET.get("minor_other_"+str(i)) is not None:
      other_to_take_courses.append(request.GET.get("minor_other_"+str(i)))
  rest_pre_courses = set()
  rest_elec_courses = set()

  l1 = len(selected_pre_courses)
  if l1 != 0:
    x = "(?), " * l1
    x = x[:-2]
    query_1 = "INSERT INTO user_inputs (courses_to_take) VALUES " + x 
    result = c.execute(query_1, selected_pre_courses)
    conn.commit()

  l2 = len(selected_elec_courses)
  if l2 != 0:
    y = "(?), " * l2
    y = y[:-2]
    query_2 = "INSERT INTO user_inputs (courses_to_take) VALUES " + y
    result = c.execute(query_2, selected_elec_courses)
    conn.commit()
  
  l3 = len(other_to_take_courses)
  if l3 != 0:
    z = "(?), " * l3
    z = z[:-2]
    query_3 = "INSERT INTO user_inputs (courses_to_take) VALUES " + z
    result = c.execute(query_3, other_to_take_courses)
    conn.commit()

  
  query = "SELECT courses_taken FROM user_inputs"
  result = c.execute(query, [])
  output_taken = result.fetchall()
  courses_taken = set()
  for obj in output_taken:
    if obj[0] is not None:
      courses_taken.add(obj[0])

  query = "SELECT courses_to_take FROM user_inputs"
  result = c.execute(query, [])
  output_to_take = result.fetchall()
  courses_to_take = set()
  for obj in output_to_take:
    if obj[0] is not None:
      courses_to_take.add(obj[0])
  
  start_quarter = []
  query = "SELECT start_quarter FROM user_inputs"
  result = c.execute(query, [])
  output = result.fetchall()
  for obj in output:
    if type(obj[0]) is str and obj[0] != '':
      start_quarter.append(obj[0])
      break

  schedule = create_schedule(list(courses_to_take), list(courses_taken), start_quarter[0])
  context = {"schedule": schedule}
  return render(request, "schedules.html", context)