import re
import bs4
import urllib.parse
import requests
import pandas as pd
import numpy as np
from  itertools import chain


def get_request(url):
    '''
    Open a connection to the specified URL and if successful
    read the data.

    Inputs:
        url: an absolute URL
    
    Outputs: 
        request object or None

    Examples:
        get_request("http://www.cs.uchicago.edu")
    '''
    
    if is_absolute_url(url):
        
        try:
            r = requests.get(url)
            
            if r.status_code == 404 or r.status_code == 403:
                r = None
        except:
            # fail on any kind of error
            r = None
    else:
        r = None

    return r


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
        return "http://" + new_url
    else:
        return urllib.parse.urljoin(current_url, new_url)
    
                
def extract_program_url(start_url):
    '''
    Take the catalog main page
    Return a dictionary with key: program name, value: corresponding program url
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
    
    
'''
Find course info on a single program page
Example: find all courses in 'Anthropology' program from 
    'http://collegecatalog.uchicago.edu/thecollege/anthropology/'
'''
WORDS_IGNORE = set(['also',  'an',  'and',  'are', 'as',  'at',  'be', 'been',
                    'but',  'by',  'course',  'for',  'from',  'how', 'i',
                    'ii',  'iii',  'in',  'include',  'is',  'not',  'of',
                    'on',  'or',  's',  'sequence',  'so',  'social',  'students',
                    'such',  'that',  'the',  'their',  'this',  'through',  'to',
                    'topics',  'units', 'we', 'were', 'which', 'will', 'with', 'yet',
                    'instructor', 'note', 'offer', 'offered', 'spring', 'summer',
                    'autumn', 'winter', 'terms', 'tbd', 'a', 'b', 'c', 'd', 'e', 
                    'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r',
                    's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'do', 'does', 'feel',
                    'into', 'it', 'have', 'its', 'many', 'most', 'make', 'made', 'take',
                    'seem', 'these', 'they', 'if', 'has', 'did', 'some', 'our'])


def build_index_for_a_program(program_url):
    '''
    Find information(build a index) for a program from a single url
    '''

    request = get_request(program_url)
    
    index = {}
    
    if request is None:
        return {}
    else:
        text = request.text
        soup = bs4.BeautifulSoup(text, 'lxml')
        div_tags = soup.find_all("div", "courseblock main")
        
        if div_tags != []:
            for div_tag in div_tags:
                sequences = find_sequence(div_tag)
                
                # no subsequence
                if sequences == []: 
                    index = scrape_course_info(div_tag, index, words_from_sequence = set())
                
                # has subsequence
                else:
                    # extract words from sequence header
                    words_from_sequence_title = extract_words(div_tag, "courseblocktitle") 
                    words_from_sequence_desc = extract_words(div_tag, "courseblockdesc")
                    words_from_sequence_detail = extract_words(div_tag, "courseblockdetail")
                        
                    words_from_sequence = words_from_sequence_title | words_from_sequence_desc | words_from_sequence_detail
                    words_from_sequence = words_from_sequence - WORDS_IGNORE
                    
                    for sequence in sequences:
                        index = scrape_course_info(sequence, index, words_from_sequence)
    
    return index


def extract_words(tag, attr):
    finding = tag.find_all("p", attr)
    if finding != []:
        text = finding[0].text
        words = re.findall("[a-zA-Z][a-zA-Z0-9]*", text)
        words = set(word.lower() for word in words)
    else:
        words = set()
    return words
    

def scrape_course_info(tag, index, words_from_sequence):
    '''
    Given one course, aka, one courseblock main
    Find course_code, course_unit, course_title from courseblocktitle
    Find instructor, terms_offered, equivalent_courses, prerequisites, notes from courseblockdetail
    Find words in courseblocktitle, courseblockdesc, courseblockdetail
    '''
    # Initialize something from courseblockdesc and courseblockdetail in case they are missing from the website
    instructors = ""
    terms_offered = ""
    equivalent_courses = ""
    prerequisites = ""
    notes = ""
    words_from_detail = set()

    # There should be info in courseblocktitle, or it's a empty or useless tag
    finding1 = tag.find_all("p", "courseblocktitle")
    if finding1 != []:
        text1 = finding1[0].text
        # Find course_code, course_title, course_unit
        info1 = re.findall("([A-Z]{4}).*(\d{5})\.\s+(.+)\.\s+(\d+)\sUnits\.", text1)
        if info1 == []:
            return index
        course_code = info1[0][0] + " " + info1[0][1]
        course_title = info1[0][2]
        course_unit = info1[0][3]
        # Find words in courseblocktitle
        words_from_title = re.findall("[a-zA-Z][a-zA-Z0-9]*", text1)
        words_from_title = set(word.lower() for word in words_from_title)
    else:
        return index
    
    # Find words in courseblockdesc
    words_from_desc = extract_words(tag, "courseblockdesc")
    if words_from_desc == set():
        # Some courses put description in class "p1"
        words_from_desc = extract_words(tag, "p1")
    
    finding3 = tag.find_all("p", "courseblockdetail")
    if finding3 != []:
        text3 = finding3[0].text
        # Find instructor, terms_offered, equivalent_courses, prerequisites, notes
        instructors_info = re.findall("Instructor\(s\)\:\s*(.+?)\s*($|Terms|\<br\/\>|Note|Equivalent|Prerequisite)", text3)
        if instructors_info != []:
            instructors = instructors_info[0][0]
        
        terms_offered_info = re.findall("Terms Offered\:\s*(.+?)($|\.|\s*Instructor|\s*\<br\/\>|\s*Note|\s*Equivalent|\s*Prerequisite)", text3)
        if terms_offered_info != []:
            terms_offered = terms_offered_info[0][0]
        
        equivalent_courses_info = re.findall("Equivalent Course\(s\)\:\s*(.+?)\s*($|Terms Offered|Instructor|\<br\/\>|Note|Prerequisite)", text3)
        if equivalent_courses_info != []:
            equivalent_courses = equivalent_courses_info[0][0]
        
        prerequisites_info = re.findall("Prerequisite\(s\)\:\s*(.+?)\s*($|Terms Offered|Instructor|\<br\/\>|Note|Equivalent)", text3)
        if prerequisites_info != []:
            prerequisites = prerequisites_info[0][0]
    
        notes_info = re.findall("Note\(s\)\:\s*(.+?)\s*($|Terms Offered|Instructor|\<br\/\>|Note|Equivalent|Prerequisite)", text3)
        if notes_info != []:
            notes = notes_info[0][0]
        
        # Find words in courseblockdetail
        words_from_detail = re.findall("[a-zA-Z][a-zA-Z0-9]*", text3)
        words_from_detail = set(word.lower() for word in words_from_detail)
    
    # Combine all the words
    words = words_from_title | words_from_desc | words_from_detail | words_from_sequence
    words = words - WORDS_IGNORE
        
    if course_code not in index:
        index[course_code] = {}
        index[course_code]['course_code'] = course_code
        index[course_code]['course_title'] = course_title
        index[course_code]['course_unit'] = course_unit
        index[course_code]['instructors'] = instructors
        index[course_code]['terms_offered'] = terms_offered
        index[course_code]['equivalent_courses'] = equivalent_courses
        index[course_code]['prerequisites'] = prerequisites
        index[course_code]['notes'] = notes
        index[course_code]['words'] = words
    
    return index


def is_subsequence(tag):
    '''
    Does the tag represent a subsequence?
    '''
    return isinstance(tag, bs4.element.Tag) and 'class' in tag.attrs \
        and tag['class'] == ['courseblock', 'subsequence']

    
def is_whitespace(tag):
    '''
    Does the tag represent whitespace?
    '''
    return isinstance(tag, bs4.element.NavigableString) and (tag.strip() == "")


def find_sequence(tag):
    '''
    If tag is the header for a sequence, then
    find the tags for the courses in the sequence.
    '''
    rv = []
    sib_tag = tag.next_sibling
    while is_subsequence(sib_tag) or is_whitespace(tag):
        if not is_whitespace(tag):
            rv.append(sib_tag)
        sib_tag = sib_tag.next_sibling
    return rv  

    
start_url = 'http://collegecatalog.uchicago.edu/thecollege/programsofstudy/'
program_urls = extract_program_url(start_url)


information = {}
for program, program_url in program_urls.items():
    information[program] = build_index_for_a_program(program_url)
    
words_ANTH_23091 = re.findall("[a-zA-Z][a-zA-Z0-9]*", "“Progress,” and its derived concept of “development” have \
puzzled Latin Americans throughout their modern history: they were an ambitious goal and a challenge for intellectual\
and political elites, a reality and an elusive dream for ordinary Latin Americans, and the cause of new challenges and\
problems wherever they actually or presumably took place. For historians, progress and development used to represent\
the very sense of universal history, a narrative that sneaked into visions of “Western modernity” and “globalization.”\
But later on, they became a myth to debunk rather than an object of reflection. What has “progress” meant particularly\
for Latin Americans? What is, for instance, the meaning of “progress” in the Brazilian flag? How did those notions\
shape the one of “development” since WWII? In political terms, what ideas of “progress” and “development” animated\
oligarchic, liberal, populist, military, revolutionary, and democratic projects across the region? Because both\
concepts involve planning and envisioning the outcome of present actions, the history of progress and development is\
also, in a certain way, a history of the future.  The goal of this seminar is to help students situate a problem of\
their choice and trace its history in terms of the political debates that pursued the goal of progress and development\
in that specific realm.")
words_ANTH_23091 = set(word.lower() for word in words_ANTH_23091)

information['Anthropology']['ANTH 23091']['words'] = words_ANTH_23091 | information['Anthropology']['ANTH 23091']['words']
information['Anthropology']['ANTH 23091']['words'] = information['Anthropology']['ANTH 23091']['words'] - WORDS_IGNORE

words_ANTH_24105 = re.findall("[a-zA-Z][a-zA-Z0-9]*", "Where is the Middle East, how do we go about studying it and\
why does it matter? This course explores the emergence of the ‘Middle East’ as an object of inquiry; a place with a\
people and a culture set in opposition to the ‘West.’ It asks how these categories are constituted, by whom, and with\
what consequence. How do they define the contours of political community, the possibilities for empathy and\
understanding or the limits of rights and moral obligation? The historical and contemporary texts assigned draw\
attention to the layered and shifting meanings of these categories, and in turn to the geopolitical and\
epistemological worlds that give rise to them. By putting these texts into conversation with each other the course\
engages a number of key issues that have occupied social theorists: the relationship between power and knowledge, the\
politics of representation, and the nature of social theory more generally.")

words_ANTH_24105 = set(word.lower() for word in words_ANTH_24105)

information['Anthropology']['ANTH 24105']['words'] = words_ANTH_24105 | information['Anthropology']['ANTH 24105']['words']
information['Anthropology']['ANTH 24105']['words'] = information['Anthropology']['ANTH 24105']['words'] - WORDS_IGNORE

words_MENG_23310 = re.findall("[a-zA-Z][a-zA-Z0-9]*", "This course aims to provide students with a knowledge of\
state-of-the-art experimental measurement techniques and laboratory instrumentation for applications in broad\
scientific research environments, as well as industrial and general engineering practice. Topics include atomic-scale\
structural and imaging methods, electronic transport in low dimensional matter, magnetic and optical characterization\
of materials. Basic concepts in electronic measurement such as lock-in amplifiers, spectrum and network analysis,\
noise reduction techniques, cryogenics, thermometry, vacuum technology, as well as statistical analysis and fitting\
of data will also be discussed.")

words_MENG_23310 = set(word.lower() for word in words_MENG_23310)

information['Molecular Engineering']['MENG 23310']['words'] = words_MENG_23310 | information['Molecular Engineering']['MENG 23310']['words']
information['Molecular Engineering']['MENG 23310']['words'] = information['Molecular Engineering']['MENG 23310']['words'] - WORDS_IGNORE

words_MENG_23320 = re.findall("[a-zA-Z][a-zA-Z0-9]*", "The course will introduce the use of optics in engineering\
We will cover the basics of wave optics, ray optics and topics such as interference, polarization and diffraction.\
We will apply them to lens systems, estimates of resolution and aberrations; the interaction of light with solids\
including non-linear optical behavior, dispersion, and the propagation of light through multilayers.  Applications\
of optics in areas such as optical communications, photonics and imaging will be introduced.")

words_MENG_23320 = set(word.lower() for word in words_MENG_23320)

information['Molecular Engineering']['MENG 23320']['words'] = words_MENG_23320 | information['Molecular Engineering']['MENG 23320']['words']
information['Molecular Engineering']['MENG 23320']['words'] = information['Molecular Engineering']['MENG 23320']['words'] - WORDS_IGNORE

words_MENG_23700 = re.findall("[a-zA-Z][a-zA-Z0-9]*", "This course provides an introduction to the fundamentals of\
quantum information to students who have not had training in quantum computing or quantum information theory. Some\
knowledge of quantum mechanics is expected, including bra-ket notation and the time-dependent form of Schrodinger’s\
equation.  Students will learn how to carry out calculations and gain a fundamental grasp of topics that will include\
some or all of: Entanglement, teleportation, quantum algorithms, cryptography, and error correction.")

words_MENG_23700 = set(word.lower() for word in words_MENG_23700)

information['Molecular Engineering']['MENG 23700']['words'] = words_MENG_23700 | information['Molecular Engineering']['MENG 23700']['words']
information['Molecular Engineering']['MENG 23700']['words'] = information['Molecular Engineering']['MENG 23700']['words'] - WORDS_IGNORE

words_MENG_24310 = re.findall("[a-zA-Z][a-zA-Z0-9]*", "Cellular engineering is a field that studies cell and molecule\
structure-function relationships. It is the development and application of engineering approaches and technologies to\
biological molecules and cells. This course is intended to be a bridge between engineers and biologists, to\
quantitatively study cells and molecules and develop future clinical applications.  Topics include “Fundamental Cell\
&amp; Molecular Biology”, “Immunology and Biochemistry, Receptors, ligands and their interactions”, \
“Nanotechnology/biomechanics”, “Enzyme kinetics”, “Molecular probes”, “Cellular and molecular imaging”, “Single-cell\
genomics and proteomics”, “Genetic and protein engineering”, and “Drug delivery &amp; gene delivery”.")

words_MENG_24310 = set(word.lower() for word in words_MENG_24310)

information['Molecular Engineering']['MENG 24310']['words'] = words_MENG_24310 | information['Molecular Engineering']['MENG 24310']['words']
information['Molecular Engineering']['MENG 24310']['words'] = information['Molecular Engineering']['MENG 24310']['words'] - WORDS_IGNORE

information['Philosophy']['PHIL 21506']['instructors'] = 'D. Finkelstein'
information['Philosophy']['PHIL 21506']['terms_offered'] = 'Spring'
information['Philosophy']['PHIL 21506']['notes'] = 'Students should register via discussion section.'

words_HIST_15702 = re.findall("[a-zA-Z][a-zA-Z0-9]*", "This course looks at the earliest attestation of East Semitic\
as a language: Akkadian which was first written in the 3rd millennium BC in Mesopotamia (modern Iraq).  Akkadians were\
in close contact with Sumerians, the other important language of Mesopotamia, and adapted their script (cuneiform)\
to write a Semitic language. This class critically examines the connection between script, language, peoples and\
ethnos. Furthermore, this course explores the political expansion of Akkadian in connection with the development of\
an early “empire” and the emergence of historical, legal and literary traditions in Akkadian and its influence for\
the Ancient Near East and beyond. Texts covered included historical inscriptions, the Law Code of Hammu-râpi, Flood\
Stories and divination texts (omina). Visits to the Oriental Institute Museum will complement the exploration of the\
Akkadian culture. Texts in English.")

words_HIST_15702 = set(word.lower() for word in words_HIST_15702)

information['History']['HIST 15702']['words'] = words_HIST_15702 | information['History']['HIST 15702']['words']
information['History']['HIST 15702']['words'] = information['History']['HIST 15702']['words'] - WORDS_IGNORE


words_HIST_15703 = re.findall("[a-zA-Z][a-zA-Z0-9]*", "This course explores the historical evidence for several\
Semitic peoples who dwelled in Syria and Northern Iraq in the third to first millennia BCE (Eblaites, Amorites,\
Ugariteans, Assyrians). These peoples' languages belong either to the larger group of Northwest Semitic, that\
comprises languages such as Aramaic and Canaanite (including Biblical Hebrew), or to the northern dialects of East\
Semitic. The shared characteristic of these people is to have recorded their cultural legacy on clay tablets, using\
Mesopotamian cuneiform or an alphabetic script adapted from it, noting either their own language or several aspects\
of their history, culture and religion through a borrowed language (Akkadian). The class will focus on major cultural\
traditions that have echoes in younger records that came to be influential for the modern Middle East and for the\
Western world – especially the Hebrew Bible, but also some traditions of Pre-Islamic Arabia. This includes a close\
examination and discussion of representative ancient sources, as well as readings in modern scholarship. Ancient\
sources include literary, historical, and legal documents. Texts in English.")

words_HIST_15703 = set(word.lower() for word in words_HIST_15703)

information['History']['HIST 15703']['words'] = words_HIST_15703 | information['History']['HIST 15703']['words']
information['History']['HIST 15703']['words'] = information['History']['HIST 15703']['words'] - WORDS_IGNORE


words_HIST_15704 = re.findall("[a-zA-Z][a-zA-Z0-9]*", "This course explores the histories and literatures of\
Aramaic- and Arabic-writing Jewish, Christian, and Muslim communities in the first millennium CE. Beginning with the\
reception of Ancient Mesopotamian culture in late antiquity, the class will focus on the development of Syriac\
Christian, Rabbinic, and early Muslim sacred literatures in relation to the social, political, and economic contexts\
of the Roman and Iranian empires and inter-imperial Arabia. It will then turn to the literary and intellectual revival\
of the early Islamic caliphates, in which representatives of all three religions participated. Among the works to be\
read in translation are the Acts of Thomas, the Babylonian Talmud, the Qur’ān, and early Arabic poetry.")

words_HIST_15704 = set(word.lower() for word in words_HIST_15704)

information['History']['HIST 15704']['words'] = words_HIST_15704 | information['History']['HIST 15704']['words']
information['History']['HIST 15704']['words'] = information['History']['HIST 15704']['words'] - WORDS_IGNORE


words_NEHC_20416 = re.findall("[a-zA-Z][a-zA-Z0-9]*", "This course looks at the earliest attestation of East Semitic\
as a language: Akkadian which was first written in the 3rd millennium BC in Mesopotamia (modern Iraq).  Akkadians\
were in close contact with Sumerians, the other important language of Mesopotamia, and adapted their script\
(cuneiform) to write a Semitic language. This class critically examines the connection between script, language,\
peoples and ethnos. Furthermore, this course explores the political expansion of Akkadian in connection with the\
development of an early “empire” and the emergence of historical, legal and literary traditions in Akkadian and its\
influence for the Ancient Near East and beyond. Texts covered included historical inscriptions, the Law Code of\
Hammu-râpi, Flood Stories and divination texts (omina). Visits to the Oriental Institute Museum will complement the\
exploration of the Akkadian culture. Texts in English.")

words_NEHC_20416 = set(word.lower() for word in words_NEHC_20416)

information['Near Eastern Languages and Civilizations']['NEHC 20416']['words']\
= words_NEHC_20416 | information['Near Eastern Languages and Civilizations']['NEHC 20416']['words']
information['Near Eastern Languages and Civilizations']['NEHC 20416']['words']\
= information['Near Eastern Languages and Civilizations']['NEHC 20416']['words'] - WORDS_IGNORE


words_NEHC_20417 = re.findall("[a-zA-Z][a-zA-Z0-9]*", "This course explores the historical evidence for several\
Semitic peoples who dwelled in Syria and Northern Iraq in the third to first millennia BCE (Eblaites, Amorites,\
Ugariteans, Assyrians). These peoples' languages belong either to the larger group of Northwest Semitic, that\
comprises languages such as Aramaic and Canaanite (including Biblical Hebrew), or to the northern dialects of East\
Semitic. The shared characteristic of these people is to have recorded their cultural legacy on clay tablets, using\
Mesopotamian cuneiform or an alphabetic script adapted from it, noting either their own language or several aspects\
of their history, culture and religion through a borrowed language (Akkadian). The class will focus on major cultural\
traditions that have echoes in younger records that came to be influential for the modern Middle East and for the\
Western world – especially the Hebrew Bible, but also some traditions of Pre-Islamic Arabia. This includes a close\
examination and discussion of representative ancient sources, as well as readings in modern scholarship. Ancient\
sources include literary, historical, and legal documents. Texts in English.")

words_NEHC_20417 = set(word.lower() for word in words_NEHC_20417)

information['Near Eastern Languages and Civilizations']['NEHC 20417']['words']\
= words_NEHC_20417 | information['Near Eastern Languages and Civilizations']['NEHC 20417']['words']
information['Near Eastern Languages and Civilizations']['NEHC 20417']['words']\
= information['Near Eastern Languages and Civilizations']['NEHC 20417']['words'] - WORDS_IGNORE

information['Near Eastern Languages and Civilizations']['NEHC 20418']['instructors'] = 'R. Payne'
information['Near Eastern Languages and Civilizations']['NEHC 20418']['terms_offered'] = 'Spring'
information['Near Eastern Languages and Civilizations']['NEHC 20418']['notes'] = 'Not open to first-year students.'
information['Near Eastern Languages and Civilizations']['NEHC 20418']['equivalent_courses'] = 'HIST 15704,NEHC 30418'

information['Geophysical Sciences']['GEOS 22040']['terms_offered'] = 'Autumn'
information['Geophysical Sciences']['GEOS 22050']['terms_offered'] = 'Winter'
information['Geophysical Sciences']['GEOS 29001']['terms_offered'] = 'Winter'
information['Geophysical Sciences']['GEOS 29005']['terms_offered'] = 'Winter'
information['Romance Languages and Literatures']['SPAN 20303']['terms_offered'] = 'Autumn'
information['Romance Languages and Literatures']['ITAL 10123']['terms_offered'] = 'Autumn'
information['Romance Languages and Literatures']['FREN 24516']['terms_offered'] = 'Autumn'
information['Near Eastern Languages and Civilizations']['NEAA 20001']['terms_offered'] = 'Autumn'
information['Near Eastern Languages and Civilizations']['NEAA 20003']['terms_offered'] = 'Spring'
information['Near Eastern Languages and Civilizations']['NEAA 20004']['terms_offered'] = 'Autumn'
information['Near Eastern Languages and Civilizations']['NEAA 20005']['terms_offered'] = 'Winter'
information['Astronomy and Astrophysics']['ASTR 18500']['terms_offered'] = 'Spring'
information['Astronomy and Astrophysics']['ASTR 18300']['terms_offered'] = 'Spring'
information['Chemistry']['CHEM 32900']['terms_offered'] = 'Autumn'
information['Chemistry']['CHEM 30500']['terms_offered'] = 'Autumn'
information['Chemistry']['CHEM 31100']['terms_offered'] = 'Spring'
information['Chemistry']['CHEM 32400']['terms_offered'] = 'Winter'
information['Chemistry']['CHEM 32500']['terms_offered'] = 'Spring'
information['Chemistry']['CHEM 33000']['terms_offered'] = 'Spring'
information['Chemistry']['CHEM 33100']['terms_offered'] = 'Spring'
information['Chemistry']['CHEM 33400']['terms_offered'] = 'Winter'
information['Chemistry']['CHEM 36800']['terms_offered'] = 'Spring'
information['Chemistry']['CHEM 36900']['terms_offered'] = 'Spring'
information['Chemistry']['CHEM 37100']['terms_offered'] = 'Spring'
information['Chemistry']['CHEM 37200']['terms_offered'] = 'Spring'
information['Chemistry']['CHEM 51100']['terms_offered'] = 'Spring'
information['Physical Sciences']['PHSC 11902']['terms_offered'] = 'Autumn'
information['Physical Sciences']['PHSC 18300']['terms_offered'] = 'Autumn'
information['Physical Sciences']['PHSC 10900']['terms_offered'] = 'Autumn'
information['Physical Sciences']['PHSC 11300']['terms_offered'] = 'Autumn'
information['Physical Sciences']['PHSC 11400']['terms_offered'] = 'Autumn'
information['Physical Sciences']['PHSC 11500']['terms_offered'] = 'Spring'
information['Physical Sciences']['PHSC 12800']['terms_offered'] = 'Spring'
information['Physical Sciences']['PHSC 13500']['terms_offered'] = 'Autumn'
information['Physical Sciences']['PHSC 18500']['terms_offered'] = 'Autumn'
information['Public Policy Studies']['PBPL 23200']['terms_offered'] = 'Spring'
information['Public Policy Studies']['PBPL 26531']['terms_offered'] = 'Spring'
information['Public Policy Studies']['PBPL 26700']['terms_offered'] = 'Spring'
information['Public Policy Studies']['PBPL 28270']['terms_offered'] = 'Winter'
information['Public Policy Studies']['PBPL 28702']['terms_offered'] = 'Autumn'
information['English Language and Literature']['ENGL 10600']['terms_offered'] = 'Autumn'
information['Molecular Engineering']['MENG 20100']['terms_offered'] = 'Spring'
information['Molecular Engineering']['MENG 27100']['terms_offered'] = 'Autumn'
information['Molecular Engineering']['MENG 27200']['terms_offered'] = 'Winter'
information['Molecular Engineering']['MENG 27200']['terms_offered'] = 'Winter'
information['Mathematics']['MATH 29520']['terms_offered'] = 'Winter'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 20300']['terms_offered'] = 'Winter'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 21400']['terms_offered'] = 'Autumn'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 24000']['terms_offered'] = 'Spring'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 17402']['terms_offered'] = 'Winter'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 17501']['terms_offered'] = 'Spring'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 17503']['terms_offered'] = 'Winter'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 17402']['terms_offered'] = 'Winter'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 17501']['terms_offered'] = 'Autumn'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 17503']['terms_offered'] = 'Spring'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 20003']['terms_offered'] = 'Winter'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 21200']['terms_offered'] = 'Spring'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 21301']['terms_offered'] = 'Winter'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 22700']['terms_offered'] = 'Spring'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 23600']['terms_offered'] = 'Spring'
information['History, Philosophy, and Social Studies of Science and Medicine']['HIPS 26203']['terms_offered'] = 'Winter'
information['Biological Sciences']['BIOS 13132']['terms_offered'] = 'Autumn'
information['Biological Sciences']['BIOS 22236']['terms_offered'] = 'Spring'
information['Biological Sciences']['BIOS 27713']['terms_offered'] = 'Spring'
information['Biological Sciences']['BIOS 29323']['terms_offered'] = 'Spring'
information['Linguistics']['LING 27130']['terms_offered'] = 'Autumn'
information['Linguistics']['LING 27220']['terms_offered'] = 'Spring'
information['Linguistics']['LING 28600']['terms_offered'] = 'Autumn'
information['Computer Science']['CMSC 10200']['terms_offered'] = 'Spring'
information['Computer Science']['CMSC 11100']['terms_offered'] = 'Spring'
information['Computer Science']['CMSC 22311']['terms_offered'] = 'Spring'
information['Computer Science']['CMSC 22630']['terms_offered'] = 'Autumn'
information['Computer Science']['CMSC 25020']['terms_offered'] = 'Spring'
information['Psychology']['PSYC 21115']['terms_offered'] = 'Spring'
information['Psychology']['PSYC 25670']['terms_offered'] = 'Spring'
information['South Asian Languages and Civilizations']['PALI 10100']['terms_offered'] = 'Spring'
information['South Asian Languages and Civilizations']['PALI 10200']['terms_offered'] = 'Winter'
information['South Asian Languages and Civilizations']['PALI 10300']['terms_offered'] = 'Autumn'
information['South Asian Languages and Civilizations']['PALI 20300']['terms_offered'] = 'Spring'
information['South Asian Languages and Civilizations']['SALC 20900']['terms_offered'] = 'Spring'
information['South Asian Languages and Civilizations']['SALC 29700']['terms_offered'] = 'Spring'
information['Comparative Literature']['CMLT 21202']['terms_offered'] = 'Spring'
information['Comparative Literature']['CMLT 23702']['terms_offered'] = 'Winter'
information['Comparative Literature']['CMLT 25102']['terms_offered'] = 'Spring'
information['Comparative Literature']['CMLT 26600']['terms_offered'] = 'Winter'
information['Comparative Literature']['CMLT 27402']['terms_offered'] = 'Spring'
information['Comparative Literature']['CMLT 28240']['terms_offered'] = 'Winter'
information['Comparative Literature']['CMLT 28900']['terms_offered'] = 'Spring'
information['Human Rights']['HMRT 20101']['terms_offered'] = 'Spring'
information['Human Rights']['HMRT 20200']['terms_offered'] = 'Winter'
information['Human Rights']['HMRT 20201']['terms_offered'] = 'Spring'
information['Human Rights']['HMRT 24501']['terms_offered'] = 'Winter'
information['Human Rights']['HMRT 26150']['terms_offered'] = 'Spring'
information['Human Rights']['HMRT 27061']['terms_offered'] = 'Winter'
information['Human Rights']['HMRT 28602']['terms_offered'] = 'Spring'
information['Human Rights']['HMRT 26151']['terms_offered'] = 'Spring'
information['Comparative Race and Ethnic Studies']['CRES 29302']['terms_offered'] = 'Spring'
information['Comparative Race and Ethnic Studies']['CRES 21264']['terms_offered'] = 'Spring'
information['Comparative Race and Ethnic Studies']['CRES 22205']['terms_offered'] = 'Winter'
information['Comparative Race and Ethnic Studies']['CRES 27605']['terms_offered'] = 'Spring'
information['Comparative Race and Ethnic Studies']['CRES 31800']['terms_offered'] = 'Autumn'
information['Germanic Studies']['GRMN 24916']['terms_offered'] = 'Autumn'
information['Germanic Studies']['GRMN 24016']['terms_offered'] = 'Autumn'
information['Germanic Studies']['NORW 10500']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 21255']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 25200']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 20002']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 20003']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 20004']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 20100']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 21102']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 21217']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 21225']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 21230']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 21251']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 21254']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 21264']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 21265']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 21307']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 21401']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 21610']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 21725']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 22000']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 22105']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 22123']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 22125']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 22130']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 22205']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 22400']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 22535']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 22606']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 22609']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 22715']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 22609']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 22915']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 23700']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 23715']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 23805']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 24705']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 24800']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 24810']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 25305']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 25325']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 25500']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 25900']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 26020']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 26315']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 26320']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 26325']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 26830']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 26900']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 27130']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 27135']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 27300']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 27430']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 27505']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 27130']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 27510']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 27520']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 27615']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 28100']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 27615']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 28200']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 28210']['terms_offered'] = 'Spring'
information['Anthropology']['ANTH 28420']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 28510']['terms_offered'] = 'Autumn'
information['Anthropology']['ANTH 28702']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 29105']['terms_offered'] = 'Winter'
information['Anthropology']['ANTH 29500']['terms_offered'] = 'Winter'
information['Humanities']['HUMA 20710']['terms_offered'] = 'Autumn'
information['Humanities']['HUMA 20711']['terms_offered'] = 'Winter'
information['Humanities']['HUMA 20712']['terms_offered'] = 'Autumn'
information['Humanities']['HUMA 20713']['terms_offered'] = 'Winter'
information['Environmental Studies']['ENST 12100']['terms_offered'] = 'Autumn'
information['Environmental Studies']['ENST 27420']['terms_offered'] = 'Spring'
information['Environmental Studies']['ENST 13132']['terms_offered'] = 'Autumn'
information['Environmental Studies']['ENST 22000']['terms_offered'] = 'Spring'
information['Environmental Studies']['ENST 22506']['terms_offered'] = 'Winter'
information['Environmental Studies']['ENST 26201']['terms_offered'] = 'Spring'
information['Environmental Studies']['ENST 26220']['terms_offered'] = 'Winter'
information['Environmental Studies']['ENST 26531']['terms_offered'] = 'Autumn'
information['Environmental Studies']['ENST 26701']['terms_offered'] = 'Winter'
information['Environmental Studies']['ENST 27420']['terms_offered'] = 'Winter'
information['Environmental Studies']['ENST 28210']['terms_offered'] = 'Winter'
information['Latin American Studies']['LACS 22503']['terms_offered'] = 'Winter'
information['Latin American Studies']['LACS 22501']['terms_offered'] = 'Winter'
information['Latin American Studies']['LACS 22502']['terms_offered'] = 'Spring'
information['Latin American Studies']['LACS 27901']['terms_offered'] = 'Autumn'
information['Latin American Studies']['LACS 27903']['terms_offered'] = 'Spring'
information['Medieval Studies']['FREN 22210']['terms_offered'] = 'Spring'
information['Religious Studies']['RLST 21107']['terms_offered'] = 'Spring'
information['Religious Studies']['RLST 25903']['terms_offered'] = 'Winter'
information['Neuroscience']['NSCI 20100']['terms_offered'] = 'Spring'
information['Fundamentals: Issues and Texts']['FNDL 22211']['terms_offered'] = 'Winter'
information['Fundamentals: Issues and Texts']['FNDL 22310']['terms_offered'] = 'Spring'
information['Environmental Science']['ENSC 20209']['terms_offered'] = 'Winter'
information['Environmental Science']['ENSC 28100']['terms_offered'] = 'Spring'
information['Environmental Science']['ENSC 29005']['terms_offered'] = 'Winter'
information['Classical Studies']['GREK 22314']['terms_offered'] = 'Spring'
information['Classical Studies']['GREK 22400']['terms_offered'] = 'Autumn'
information['Classical Studies']['LATN 22100']['terms_offered'] = 'Spring'
information['Classical Studies']['LATN 22200']['terms_offered'] = 'Winter'
information['Classical Studies']['LATN 22300']['terms_offered'] = 'Spring'
information['Jewish Studies']['JWSC 21107']['terms_offered'] = 'Spring'
information['Statistics']['STAT 22400']['terms_offered'] = 'Autumn, Spring'
information['Statistics']['STAT 24410']['terms_offered'] = 'Autumn'
information['Statistics']['STAT 25300']['terms_offered'] = 'Winter'
information['Music']['MUSI 21814']['terms_offered'] = 'Winter'
information['Music']['MUSI 28000']['terms_offered'] = 'Winter'
information['Music']['MUSI 14300']['terms_offered'] = 'Autumn'
information['Music']['MUSI 22900']['terms_offered'] = 'Winter'
information['Music']['MUSI 22901']['terms_offered'] = 'Autumn'
information['Music']['MUSI 23104']['terms_offered'] = 'Winter'
information['Music']['MUSI 23410']['terms_offered'] = 'Spring'
information['Music']['MUSI 23509']['terms_offered'] = 'Winter'
information['Music']['MUSI 23514']['terms_offered'] = 'Spring'
information['Music']['MUSI 23614']['terms_offered'] = 'Winter'
information['Music']['MUSI 23911']['terms_offered'] = 'Spring'
information['Music']['MUSI 25300']['terms_offered'] = 'Winter'
information['Music']['MUSI 25514']['terms_offered'] = 'Spring'
information['Music']['MUSI 25701']['terms_offered'] = 'Winter'
information['Music']['MUSI 28000']['terms_offered'] = 'Autumn'
information['History']['HIST 15704']['terms_offered'] = 'Winter'
information['History']['HIST 17402']['terms_offered'] = 'Autumn'
information['History']['HIST 17501']['terms_offered'] = 'Spring'
information['History']['HIST 17503']['terms_offered'] = 'Autumn'
information['History']['HIST 20209']['terms_offered'] = 'Winter'
information['History']['HIST 20403']['terms_offered'] = 'Spring'
information['History']['HIST 29408']['terms_offered'] = 'Winter'
information['Religious Studies']['RLST 20702']['terms_offered'] = 'Spring'
information['Religious Studies']['RLST 21107']['terms_offered'] = 'Spring'
information['Religious Studies']['RLST 23904']['terms_offered'] = 'Spring'
information['Religious Studies']['RLST 25120']['terms_offered'] = 'Winter'
information['Religious Studies']['RLST 26150']['terms_offered'] = 'Spring'
information['Religious Studies']['RLST 25903']['terms_offered'] = 'Winter'
information['Religious Studies']['RLST 28704']['terms_offered'] = 'WInter'
information['Religious Studies']['RLST 20702']['terms_offered'] = 'Spring'
information['Economics']['ECON 20710']['terms_offered'] = 'Winter'
information['Economics']['ECON 20740']['terms_offered'] = 'Spring'
information['Economics']['ECON 20800']['terms_offered'] = 'Winter'
information['Economics']['ECON 21100']['terms_offered'] = 'Autumn'
information['Economics']['ECON 21150']['terms_offered'] = 'Spring'
information['Economics']['ECON 24000']['terms_offered'] = 'Spring'
information['Economics']['ECON 26540']['terms_offered'] = 'Winter'
information['Economics']['ECON 26700']['terms_offered'] = 'Autumn'
information['Economics']['ECON 28700']['terms_offered'] = 'Spring'
information['Comparative Human Development']['CHDV 20400']['terms_offered'] = 'Winter'
information['Comparative Human Development']['CHDV 27903']['terms_offered'] = 'Autumn'
information['Comparative Human Development']['CHDV 29701']['terms_offered'] = 'Autumn'


df_course = pd.DataFrame()
for program, program_info in information.items():
    df_program = pd.DataFrame.from_dict(program_info, orient = 'index')
    df_course = pd.concat([df_course, df_program])

df_course.ix['NEHC 20004']['terms_offered'] = 'Spring'
df_course.ix['NEHC 20005']['terms_offered'] = 'Spring'

df_words = pd.DataFrame({
        "course_code": np.repeat(df_course.course_code.values, df_course.words.str.len()),
        "words": list(chain.from_iterable(df_course.words))})

df_prerequisites = df_course.prerequisites.str.extractall('([A-Z]{4})*\s*(\d{5}?)\s*(and|\-|or|\, or|\:|\/|\.|\;|\(|\,)')
df_prerequisites['Compulsory'] = True
df_prerequisites.loc[df_prerequisites[2] == 'or', 'Compulsory'] = False
df_prerequisites.loc[df_prerequisites[2] == '/', 'Compulsory'] = False
df_prerequisites.loc[df_prerequisites[2] == ', or', 'Compulsory'] = False
df_prerequisites.loc[df_prerequisites[2] == '(', 'Compulsory'] = False

df_prerequisites.drop('HIPS 28101', level=0, axis=0, inplace=True)
df_prerequisites = df_prerequisites.fillna(method="ffill", axis=0)
df_prerequisites['course_code'] = df_prerequisites[0] + ' ' + df_prerequisites[1]


df_terms = pd.DataFrame(df_course.terms_offered.apply(lambda x: pd.Series(x.split(','))))
df_terms = df_terms.rename(columns = {0:'term1', 1:'term2', 2:'term3', 3:'term4'})

df_course[['course_title', 'course_unit', 'equivalent_courses', 'instructors',
           'notes']].to_csv('course_info.csv', sep = ',', encoding = 'utf-8')

df_words.to_csv('course_word.csv', sep = ',', encoding = 'utf-8')

df_terms.to_csv('terms_offered.csv', sep = ',', encoding = 'utf-8')

df_prerequisites[['course_code', 'Compulsory']].to_csv('course_prerequisites.csv', sep = ',', encoding = 'utf-8')
