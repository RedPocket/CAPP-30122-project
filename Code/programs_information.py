
#Red Pocket Final Project
#Yuqing Zhang, Yiqing Zhu, Xinyi Hong

'''
-----------------------------------------------------------
This document is to grab required classes, electives and descriptions for each
major and minor programs listed in
http://collegecatalog.uchicago.edu/thecollege/programsofstudy/
'''
import re
import bs4
import queue
import json
import sys
import urllib.parse
import requests
import pandas as pd

print_header_lst = ['GENERAL EDUCATION','MAJOR: TRACK I','MAJOR: TRACK II']
taboo_descriptions = ['MAJOR','GENERAL EDUCATION','One of the following sequences:',
                      'One of the following:','and','*','or','OR','Area A:', 'Area B:', 'Area C:',
                      'Both of the following:','Standard Core Sequence', 
                      'or Honors Core Sequence',
                      'Three approved electives (see Elective Courses below)',
                      'Computer Science', 'Statistics', 'Mathematics','Four electives',
                      'Students may take one of the following:','Total Units',
                      'Tutorial:']
def get_request(url):
    '''
    Open a connection to the specified URL and if successful
    read the data.

    Inputs:
        url: must be an absolute URL
    
    Outputs: 
        request object or None
    '''
    
    if is_absolute_url(url):
        
        try:
            r = requests.get(url)
            print(r)
            if r.status_code == 404 or r.status_code == 403:
                r = None
        except:
            # fail on any kind of error
            r = None
    else:
        r = None

    return r


def read_request(request):
    '''
    Return data from request object.  Returns result or "" if the read
    fails..
    '''

    try:
        return request.text.encode('iso-8859-1')
    except:
        print("read failed: " + request.url)
        return ""

def get_request_url(request):
    '''
    Extract true URL from the request
    '''
    return request.url


def is_absolute_url(url):
    '''
    Is url an absolute URL?
    '''
    if url == "":
        return False
    return urllib.parse.urlparse(url).netloc != ""


    

def convert_if_relative_url(current_url, new_url):
    '''
    Attempt to determine whether new_url is a relative URL and if so,
    use current_url to determine the path and create a new absolute
    URL.  Will add the protocol, if that is all that is missing.

    Inputs:
        current_url: absolute URL
        new_url: 

    Outputs:
        new absolute URL or None, if cannot determine that
        new_url is a relative URL.

    Examples:
        convert_if_relative_url("http://cs.uchicago.edu", "pa/pa1.html") yields 
            'http://cs.uchicago.edu/pa/pa.html'

        convert_if_relative_url("http://cs.uchicago.edu", "foo.edu/pa.html") yields
            'http://foo.edu/pa.html'
    '''
    if new_url == "" or not is_absolute_url(current_url):
        return None

    if is_absolute_url(new_url):
        return new_url

    parsed_url = urllib.parse.urlparse(new_url)
    path_parts = parsed_url.path.split("/")

    if len(path_parts) == 0:
        return None

    ext = path_parts[0][-4:]
    if ext in [".edu", ".org", ".com", ".net"]:
        return "http://" + new_url
    elif new_url[:3] == "www":
        return "http://" + new_path
    else:
        return urllib.parse.urljoin(current_url, new_url)
    
def extract_program_url(start_url):
    '''
    Take the catalog main page
    Return a dictionary with key: program name, value: its main page url
    '''
    program_urls = {}
    request = get_request(start_url)
    if request is None:
        return {}
    else:
        html = request.text
        soup = bs4.BeautifulSoup(html, "lxml")
        links = soup.findChild('ul', class_="nav levelthree")
        links = str(links)
        match1 = re.findall('<a href="(.*)">', links)
        match2 = re.findall('">(.*)</a></li>', links)
        for i in range(len(match1)):
            if match1[i] != [] and match2[i] != []:
                url = convert_if_relative_url(start_url, match1[i])
                if url != None:
                    program_urls[match2[i]] = url
    return program_urls

start_url = 'http://collegecatalog.uchicago.edu/thecollege/programsofstudy/'
program_urls = extract_program_url(start_url)

def get_requirements(program,df_major_requirements,df_minor_requirements,
                     program_url,minor):
'''
This function is to get required courses, electives and descriptions for one program

Inputs:
    program: program name
    df_major_requirements: an empty DataFrame for major programs
    df_minor_requirements: an empty DataFrame for minor programs
    program_url: program website
    minor: a boolean 

Return:
    major_dicts: a dictionary if not minor 
    minor_dicts: a dictionary if minor
'''
    request=get_request(program_url)

    if request is None:
        return []

    r = requests.get(program_url)
    text=request.text
    soup = bs4.BeautifulSoup(text,'lxml')
    table_lst = soup.find_all('table',class_='sc_courselist') #how to extract stuff only under summary of requirement the header?
    h4header_lst = soup.findAll('h4')
    strong_lst = soup.findAll('strong')
    h5header_lst = soup.findAll('h5')
    or_lst = soup.findAll('td',class_="codecol orclass")
    found_summary = False
    found_minor = False
    major_dicts = []
    minor_dicts = []

    for h4header in h4header_lst:
            
        h4header_lower = h4header.text.lower()

        if 'summary of' in h4header_lower and 'minor' not in h4header_lower and minor== False:
            
            found_summary = True

            major_dicts.append(find_table(program,df_major_requirements,
                                          df_minor_requirements,h4header_lst,
                                          h4header_lst,strong_lst,h5header_lst,
                                          table_lst,or_lst,h4header,minor=False))

        elif 'minor' in h4header_lower and minor:
            found_minor = True
            minor_dicts.append(find_table(program,df_major_requirements,df_minor_requirements,h4header_lst,h4header_lst,strong_lst,h5header_lst,table_lst,or_lst,h4header,minor=True))
    
    if not found_summary:

        h3header_lst =soup.findAll('h3')

        for h3header in h3header_lst:
            if 'summary of' in h3header.text.lower() and minor==False:

                major_dicts.append(find_table(program,df_major_requirements,
                                              df_minor_requirements,h4header_lst,
                                              h4header_lst,strong_lst,h5header_lst,
                                              table_lst,or_lst,h3header,minor=False))
                
            elif 'minor' in h3header.text.lower() and not found_minor and minor:

                minor_dicts.append(find_table(program,df_major_requirements,
                                   df_minor_requirements,h4header_lst,h4header_lst,
                                   strong_lst,h5header_lst,table_lst,or_lst,
                                   h3header,minor=True))

    if major_dicts != []:

        return major_dicts

    if minor_dicts != []:

        return minor_dicts
 


def find_table(program,df_major_requirements,df_minor_requirements,header_lst,
               h4header_lst,strong_lst,h5header_lst,table_lst,or_lst,header,minor):
'''
This function is to find the table under the 'summary of ...' header
and extract required classes, electives and descriptions information out of it.

Returns: 
    minor_requirements: a dictionary containing minor program information
    major_requirements: a dictionary containing major program information
'''
    minor_requirements = {}
    major_requirements = {}
    next_tag = header.findNext()
    strongheader = ''
    h5header = ''
    h4header = ''
    header_id = ''
    while next_tag not in header_lst:
        if next_tag in h4header_lst:
            h4header = next_tag.text

        elif next_tag in strong_lst:
            strongheader = next_tag.text

        elif next_tag in h5header_lst and next_tag.text == 'Program with Equal Emphasis on Two Literatures':
            h5header = next_tag.text
            header_id = 'summary of requirements for'+h5header

        elif next_tag in h5header_lst and next_tag.text == 'Program with Greater Emphasis on One Literature':
            
            h5header = next_tag.text
            header_id = 'summary of requirements for'+h5header

        elif next_tag in table_lst:
            electives_lst = []
            one_table_requirement_lst = []
            one_table_descriptions_lst = []
            one_table_electives_lst = []
            
            headers = next_tag.find_all('span', class_="courselistcomment") #how to extract stuff only under one header?

            if minor:

                minor_header_id = header.text
                header_id_group = re.findall('(summary of requirements for the 
                                             '|summary of requirements for |summary of requirements: |
                                             'summary of requirements|summary of)*(.+)', 
                                             minor_header_id.lower())
                
                minor_header_id = header_id_group[0][1]
                minor_requirements[minor_header_id]={}
                minor_requirements[minor_header_id]['track'] = header.text
                minor_requirements[minor_header_id]['program_name'] = program

            else:
                if strongheader != '':
                    header_id = strongheader
              
                elif header != '':
                    header_id = header.text
                    if header_id == 'Summary of Requirements':
                        header_id += ' for '
                        header_id += program
                header_id_group = re.findall('(summary of requirements for the |
                                             'summary of requirements for |
                                             'summary of requirements: |
                                             'summary of requirements|summary of)(.+)', 
                                             header_id.lower())
                if True:
                    header_id = header_id_group[0][1]
                    if header_id == '\xa0':
                        header_id = 'Comparative Human Development'
                    if header_id == 'standard major\xa0\xa0\xa0\xa0\xa0\xa0\xa0':
                        header_id = 'Philosophy'
                    if header_id == '** GENERAL EDUCATION':
                        header_id = 'Computer Science GENERAL EDUCATION'
                    if header_id == 'students meeting the writing requirement with a long paper':
                        header_id = 'Political Science: Students Meeting the Writing Requirement with a Long Paper'
                    if header_id == 'students meeting the writing requirement with a ba thesis\xa0':
                        header_id = 'Political Science: Students Meeting the Writing Requirement with a BA Thesis'
                    if header_id == ' major requirements:\xa0track a':
                        header_id = 'Biological Sciences:track A'
                    if header_id == ' major requirements: track b':
                        header_id = 'Biological Sciences:track B'
                    if header_id == ' major requirements:\xa0track c':
                        header_id = 'Biological Sciences:track C'
                    
            
                if headers != []:
                    descriptions = next_tag.find_all('span',class_ = 'courselistcomment')
                    for description in descriptions:
                        if description.text in print_header_lst:
                            header_id = header_id+' '+description.text
                            major_requirements[header_id] = {}
                            major_requirements[header_id]['track'] = header_id
                            major_requirements[header_id]['program_name'] = program
                        else:
                            major_requirements[header_id] = {}
                            major_requirements[header_id]['track'] = header_id
                            major_requirements[header_id]['program_name'] = program
                            one_table_descriptions_lst.append(description.text.splitlines())
                else:
                    
                    major_requirements[header_id] = {}
                    major_requirements[header_id]['track'] = header_id
                    major_requirements[header_id]['program_name'] = program


            electives = next_tag.find_all('div',style='margin-left: 20px;')

            for elective in electives:
                e = re.findall('([A-Z]+)\xa0([\d]+\-*[\d]*\-*[\d]*)',elective.text)
                if e != []:
                    electives_lst.append(e)

            if electives_lst != []:
                for course in electives_lst:
                    elective_code_final = course[0][0]+" "+course[0][1]
                    one_table_electives_lst.append(elective_code_final)

                    if elective_code_final == 'LATN 21100':
                        one_table_electives_lst.append('LATN 21200')
                        one_table_electives_lst.append('LATN 21300')
                    if elective_code_final == 'GREK 10100':
                        one_table_electives_lst.append('GREK 10200')
                        one_table_electives_lst.append('GREK 10300')
                    if elective_code_final == 'SOSC 24302':
                        one_table_electives_lst.append('SOSC 24302-24402')
                    if elective_code_final == 'CHEM 10100':
                        one_table_electives_lst[-1]='CHEM 10100-10200'

            requirements = next_tag.text#.splitlines()
            courses = re.findall('([A-Z]+)\xa0([\d]+\-*[\d]*\-*[\d]*)',requirements)

            for course in courses:
                course_code_final = course[0]+" "+course[1]
                if course_code_final == 'CHEM 10100':
                    course_code_final = 'CHEM 10100-10200'
                elif course_code_final == 'PHYS 12200':
                    course_code_final = 'PHYS 12200-12300'
                elif course_code_final == 'SOSC 24302':
                    course_code_final = 'SOSC 24302-24402'
                one_table_requirement_lst.append(course_code_final)

            classes = next_tag.find_all('td', class_="codecol")
            choose_from_one = []
            for i in range(1,len(classes)):
                if classes[i-1] not in or_lst and classes[i] in or_lst:
                    main_class_name = re.findall('([A-Z]+)\xa0([\d]+\-*[\d]*\-*[\d]*)',classes[i-1].text)
                    main_class_realname = main_class_name[0][0]+' '+main_class_name[0][1]
                    or_class_name = re.findall('([A-Z]+)\xa0([\d]+\-*[\d]*\-*[\d]*)',classes[i].text)
                    or_class_realname = or_class_name[0][0]+' '+or_class_name[0][1]
                    choose_from_one.append(main_class_realname)
                    choose_from_one.append(or_class_realname)
                    if i==len(classes)-1:
                        one_table_electives_lst.append(main_class_realname)
                        one_table_electives_lst.append(or_class_realname)

                elif classes[i-1] in or_lst and classes[i] in or_lst:
                    or2_class_name = re.findall('([A-Z]+)\xa0([\d]+\-*[\d]*\-*[\d]*)',classes[i].text)
                    or2_class_realname = or2_class_name[0][0]+' '+or2_class_name[0][1]
                    one_table_electives_lst.append(or2_class_realname)

            if header.text == 'minor program in computer science':
                minor_requirements[minor_header_id] = {}
                minor_requirements[minor_header_id]['program_name'] = program
                minor_requirements[minor_header_id]['elective1'] = []
                minor_requirements[minor_header_id]['elective1'] = one_table_electives_lst[:3]
                minor_requirements[minor_header_id]['elective2'] = []
                minor_requirements[minor_header_id]['elective2'] = one_table_electives_lst[3:6]
                minor_requirements[minor_header_id]['elective3'] = []
                minor_requirements[minor_header_id]['elective3'] = one_table_electives_lst[6:]
            
            elif header != 'A. Civilization Requirement':
                    if minor:
                        if one_table_electives_lst == []:
                            one_table_electives_lst = ['No electives']

                        minor_requirements[minor_header_id]['elective'] = []
                        str_electives = ','.join(one_table_electives_lst)
                        minor_requirements[minor_header_id]['elective'] = str_electives
                    
                    else:
                        if one_table_electives_lst == []:
                            one_table_electives_lst = ['No electives']
                        major_requirements[header_id]['elective'] = []
                        str_electives = ','.join(one_table_electives_lst)
                        major_requirements[header_id]['elective'] = str_electives
            
            major_lst = [x for x in one_table_requirement_lst if x not in one_table_electives_lst]
            
            if minor:
                minor_requirements[minor_header_id]['must_take'] = []
                if major_lst == []:
                    major_lst = ['check electives']
                str_requirements = ','.join(major_lst)
                minor_requirements[minor_header_id]['must_take'] = str_requirements
                minor_requirements[minor_header_id]['must_take'] = str_requirements

            else:
                major_requirements[header_id]['must_take'] = []
                if major_lst == []:
                    major_lst = ['check electives']
                str_requirements = ','.join(major_lst)
                major_requirements[header_id]['must_take'] = str_requirements

            if [x[0] for x in one_table_descriptions_lst if x[0] not in taboo_descriptions]!=[]:
                
                if minor:
                    minor_requirements[minor_header_id]['descriptions']=[]
                    minor_requirements[minor_header_id]['descriptions']=[x[0] for x in one_table_descriptions_lst if x[0] not in taboo_descriptions]
                
                else:
                    major_requirements[header_id]['descriptions']=[]
                    major_requirements[header_id]['descriptions']=[x[0] for x in one_table_descriptions_lst if x[0] not in taboo_descriptions]
        
        elif next_tag == None:
            break


        next_tag = next_tag.findNext()

    if minor:
        return minor_requirements

    return major_requirements


'''
Now it's time to build the dataframe for major and minor programs,
then convert them to csv files
'''
df_major_requirements = pd.DataFrame()
df_minor_requirements = pd.DataFrame()
for program, program_url in program_urls.items():

    minor_requirements = get_requirements(program,df_major_requirements,df_minor_requirements,program_url,minor=True)
    major_requirements = get_requirements(program,df_major_requirements,df_minor_requirements,program_url,minor=False)
    
    if minor_requirements1!=None:
        for minor_requirement in minor_requirements:
            df_minors = pd.DataFrame.from_dict(minor_requirement, orient = 'index')
            df_minor_requirements = pd.concat([df_minor_requirements, df_minors])
    
    if major_requirements2!=None:
        for major_requirement in major_requirements:
            df_majors = pd.DataFrame.from_dict(major_requirement, orient = 'index')
            df_major_requirements = pd.concat([df_major_requirements, df_majors])

df_major_requirements=df_major_requirements.drop(df_major_requirements[df_major_requirements.program_name == 'Comparative Race and Ethnic Studies'].index)
df_major_requirements=df_major_requirements.drop(df_major_requirements[df_major_requirements.program_name == 'Computational Neuroscience'].index)
df_major_requirements=df_major_requirements.drop(df_major_requirements[df_major_requirements.program_name == 'Creative Writing'].index)
df_major_requirements=df_major_requirements.drop(df_major_requirements[df_major_requirements.track.str.contains('GENERAL EDUCATION')].index)

df_minor_requirements=df_minor_requirements.drop(df_minor_requirements[df_minor_requirements.program_name == 'Creative Writing'].index)

df_major_requirements=df_major_requirements.rename(index={'**':'Computer Science'})
df_major_requirements=df_major_requirements.rename(index={'majors':'Visual Arts'})
df_major_requirements=df_major_requirements.rename(index={'studio track majors':'Visual Arts studio track majors'})
df_major_requirements=df_major_requirements.rename(index={'language and literature variant':'Classical Studies: language and literature variant'})
df_major_requirements=df_major_requirements.rename(index={'language intensive variant':'Classical Studies: language intensive variant'})
df_major_requirements=df_major_requirements.rename(index={'language intensive variant':'Classical Studies: language intensive variant'})
df_major_requirements=df_major_requirements.rename(index={'greek and roman cultures variant':'Classical Studies: greek and roman cultures variant'})
df_major_requirements=df_major_requirements.rename(index={'intensive track':'Philosophy: intensive track'})
df_major_requirements=df_major_requirements.rename(index={'french':'Romance Languages and Literatures: french'})
df_major_requirements=df_major_requirements.rename(index={'italian':'Romance Languages and Literatures: italian'})
df_major_requirements=df_major_requirements.rename(index={'spanish':'Romance Languages and Literatures: spanish'})

df_minor_requirements=df_minor_requirements.rename(index={'sample program for the minor':'Astronomy and Astrophysics'})
df_minor_requirements=df_minor_requirements.rename(index={'d. requirements for the major and the minor':'Comparative Race and Ethnic Studies'})
df_minor_requirements=df_minor_requirements.rename(index={'samples follow of two groups of courses that would comprise a minor:':'Philosophy'})
df_minor_requirements=df_minor_requirements.rename(index={'language track sample minor':'Near Eastern Languages and Civilizations:language track sample minor'})
df_minor_requirements=df_minor_requirements.rename(index={'culture track sample minor':'Near Eastern Languages and Civilizations:culture track sample minor'})
df_minor_requirements=df_minor_requirements.rename(index={'electives approved for the minor in statistics1':'Statistics'})


df_major_requirements.drop('minor in south asian languages and civilizations',inplace=True)
df_minor_requirements.drop('Creative Writing',inplace=True)
df_major = pd.DataFrame(df_major_requirements.must_take.apply(lambda x:pd.Series(x.split(','))))
df_minor = pd.DataFrame(df_minor_requirements.must_take.apply(lambda x:pd.Series(x.split(','))))

df_major.rename(columns={0:'Requirement 1',1:'Requirement 2',2:'Requirement 3',
                   3:'Requirement 4',4:'Requirement 5',5:'Requirement 6',
                   6:'Requirement 7',7:'Requirement 8',8:'Requirement 9',
                   9:'Requirement 10',10:'Requirement 11',11:'Requirement 12'},inplace= True)
df_minor.rename(columns={0:'Requirement 1',1:'Requirement 2',2:'Requirement 3',
                   3:'Requirement 4',4:'Requirement 5',5:'Requirement 6',
                   6:'Requirement 7',7:'Requirement 8',8:'Requirement 9'},inplace= True)

split_minor = df_minor_requirements['elective'].str.split(',').apply(pd.Series, 1).stack()
split_minor.index = split_minor.index.droplevel(-1)
split_minor.name = 'elective'
del df_minor_requirements['elective']
df_minor_requirements = df_minor_requirements.join(split_minor)

split_major = df_major_requirements['elective'].str.split(',').apply(pd.Series, 1).stack()
split_major.index = split_major.index.droplevel(-1)
split_major.name = 'elective'
del df_major_requirements['elective']
df_major_requirements = df_major_requirements.join(split_major)

df_minor_requirements.to_csv('minors_info.csv', sep = ',', encoding = 'utf-8')
df_major_requirements.to_csv('majors_info.csv', sep = ',', encoding = 'utf-8')
df_major.to_csv('requirements_info.csv', sep = ',', encoding = 'utf-8')
df_minor.to_csv('minor_requirements_info.csv', sep = ',', encoding = 'utf-8')
df_major_requirements.loc[df_major_requirements['program_name'] == 'Biological Sciences']


