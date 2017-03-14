CREATE TABLE major_requirements
   (track_name varchar(50),
   descriptions varchar(50),
   must_take varchar(50),
   program_name varchar(10),
   track varchar(10),
   elective varchar(50));

.separator ","
.import majors_info.csv major_requirements

CREATE TABLE minor_requirements
   (track_name varchar(50),
   must_take varchar(50),
   program_name varchar(10),
   track varchar(10),
   elective varchar(50));

.separator ","
.import minors_info.csv minor_requirements

CREATE TABLE major_requirements_only
   (track_name varchar(50),
   Requirement0 varchar(50),
   Requirement1 varchar(50),
   Requirement2 varchar(50),
   Requirement3 varchar(50),
   Requirement4 varchar(50),
   Requirement5 varchar(50),
   Requirement6 varchar(50),
   Requirement7 varchar(50),
   Requirement8 varchar(50),
   Requirement9 varchar(50),
   Requirement10 varchar(50),
   Requirement11 varchar(50),
   Requirement12 varchar(50));
.separator ","
.import requirements_info.csv major_requirements_only
CREATE TABLE minor_requirements_only
   (track_name varchar(50),
   Requirement0 varchar(50),
   Requirement1 varchar(50),
   Requirement2 varchar(50),
   Requirement3 varchar(50),
   Requirement4 varchar(50),
   Requirement5 varchar(50),
   Requirement6 varchar(50),
   Requirement7 varchar(50),
   Requirement8 varchar(50),
   Requirement9 varchar(50));
.separator ","
.import minor_requirements_info.csv minor_requirements_only

CREATE TABLE course_info
   (course_code varchar(50),
   course_title varchar(50),
   course_unit integer,
   equivalent_courses varchar(50),
   instructors varchar(50),
   notes varchar(50));

.separator ","
.import course_info.csv course_info

CREATE TABLE course_keyword
   (count integer,
   course_code varchar(50),
   keyword varchar(50));

.separator ","
.import course_word.csv course_keyword

CREATE TABLE prerequisites
   (course_code varchar(50),
   match integer,
   prerequisite_course_code varchar(50),
   compulsory varchar(10));

.separator ","
.import course_prerequisites.csv prerequisites

CREATE TABLE terms_offered
   (course_code varchar(50),
   term1 varchar(10),
   term2 varchar(10),
   term3 varchar(10),
   term4 varchar(10));

.separator ","
.import terms_offered.csv terms_offered

CREATE TABLE user_input
   (courses_taken varchar(100),
    courses_to_take varchar(100));
