
we have all this apps in our projects 
if i may ask are they wired together im taking about there templates
'accounts',
    'school',
    'students',
    'exams',
    'reports',
    'subjects',
    'billing',
    'events',
  on base.html at report and analysis on the dashboard implement below 
     on exams i wanted the flow to be like i go 
    to exam analysis dasboard in our base.html i get form levels
     eg form1,form2,form3,form3,form4 then when i click on form eg form3 i will see a 
     list of exams it has done then when i click on the exam eg term2 i will be taken to combined 
     class list of merit where all the subjects cards thats when i can get to individual
     subject analysis eg english card i will see the perfomance in english the graphs 
     Nand the list below  then we should have a card form combined class 
     exam done in a table having 
     name,admission_number,stream,subjects,Number of subjects,total marks,mean marks,Grade,total points,Dev 
     if he has done previous exam,stream position,class position
     thats for combined 
      if will get streams eg east,west,south,north,east then i get individual
       stream analysis for the specific stream 

still on base when i click on student report card i should be taken to form level as usial 
form1,form2,form3,form4 then i should be taken to individual forms eg 1 then i can generate the reports for the
whole sterams like form 1 all the students they should be in pdf form all the analysis on one A4
page for the form1 then if i can go futher to individual stream like
east,west,north or south i will only be able to generate the specific stream  like north
then on both i should be able to generate the individual student report through search 

still on base we should add another thing we call upload exam here when i click i should be taken to 
form level eg form1,form2,form3,form4 thenwhen you click to formlike form1
you will see the list of exams that the form has done page eg endterm1,opener,midterm,end term
you wil lsee the status if it was released then you will enter to exam you are uploading wich 
is not hard coded its dinamic from the created exams then you will dive into 
stream  like if i took form there i will see the 
form there streams like
east,west,south,north then if i take south i will see the groups of those subjects like languages,sciences,
applied,mathematics
if i take humanities i will be taken to that specific dashboard for that eg geography,cre,history
if i take geography i will get toa section having a boolen where i will be asked to either upload manally or via
the excel then iwll be able to download the template wich i can again upload 
then i be for even that i will be able to select exam that i want to upload eg joint exam evaluation
then i will be taken to the real upload section to choose either manual or excel
then i will be able to enter maxmum marks eg 100 so the marks uploaded will be out of 100 for the percentage calcuklation
then the form will be in a form of a table having
name,admission_number,marks,then we will have an icon drop own  for combo {X,Y}
for absent and  Disqualified students  and when i enter even one student when i click on upload he shouldbe filtered
to go to the list now that table like will only contain students whose mamrks are not yet upload
and on a list i should show the students name,admission_number,makrs either a value even 0 or X,Y
 on the table like form i said i have uploadResult to save and filter then we have a place to ad student to your subjects 
 you cluck the it opens an interface to search the kid in the system and he/she should just be from the very class 
 then you enter admission_number and name will be populated then you will enter marks

 teachers dashboard individual when he logs in, he should be able to view his assigned classes and subjects. eg form1,form2,form3,form4
 then when i click on form1 i see the strams like east,west
 then if i enter east i see the subjects i have been assigned eg geography,computer
 then i see the list of students in the particular classes and stream we navigated 
 then we can click on exams and we select the type of exam like opener exam then when i click 
 on it i will see the mean points,mean makrs,mean grade,number of students card

 then on general teacher dashboard exam i will see the list in table form
 there i see the form like form2 i see the streams west,east
 then i have a status then action containing upload  then publish then we have paper ratio then grading system i want to use 
 so like if i form1 i teach east,west 
 on east i teach geography and west computer they will be profesionally in a list table form
 then i will see the status of specific subject in the stream then i will have paper ratio which i will either decide to use or not
 then we have acton to either upload or  publish if i publish only admins can publish or analys 
 the upload takes me to upload exam  section we have said  

## User Management Dashboard

### Overview
Administrators should have access to a dedicated user management dashboard to view and manage user roles.

### Requirements

#### User Role Display
- Display all users in a card-based layout
- Each user card should show:
  - User's full name (e.g., "Saul Kitui")
  - Current role badge/banner (e.g., "Principal", "Teacher", "Admin")
  - Profile information
  - Quick action buttons

#### Role Management Features
- **View User Details**: Click on any user card to open their detailed dashboard
- **Role Assignment**: Navigate to the user's dashboard to:
  - Reassign user roles (e.g., change from Teacher to Principal)
  - Assign/modify class assignments
  - Update subject responsibilities
  - Manage permissions based on role

#### User Interface
- Clean, card-based design with visual role indicators
- Search and filter functionality for finding specific users
- Quick access to role modification interface
- Confirmation dialogs for critical role changes

#### Permissions
- Only administrators should have access to modify user roles
- Role changes should be logged for audit purposes
- System should validate role assignments to prevent conflicts

update on our base.html and school dashboard so that they allign with our new updates  like on the base.html add  dashboards on our students so that it handles  /students/form/1/ > /students/form/1/stream/west/ as we had discussed  also update  forms & classes card also so that when i go to form i get on top card for streams and below we have a combined list having the details and the specific stream then when i clcick on streams like North i should get north students and i should be able to add remember we said saul kitui is the principal  then from this url http://127.0.0.1:8000/school/forms/  it should show me the card of strems which i will be able to navigate into specific stream and below it we have a combined list of students

ensure that we have 5 students in each stream like form 1 west 5,east 5,north 5 south 5 then now in the whole form 1 we have a combined list of 2o students do it accross the forms



Page not found (404)

No student found matching the query

Request Method: 	GET
Request URL: 	http://127.0.0.1:8000/students/187/enroll/
Raised by: 	students.views.StudentSubjectEnrollmentView

Using the URLconf defined in exam_system.urls, Django tried these URL patterns, in this order:

    admin/
    [name='root']
    login-selection/ [name='login_selection']
    accounts/
    students/ [name='student_list']
    students/ form/<int:form_level>/ [name='form_dashboard']
    students/ form/<int:form_level>/stream/<str:stream>/ [name='stream_students']
    students/ create/ [name='student_create']
    students/ <int:pk>/ [name='student_detail']
    students/ <int:pk>/update/ [name='update_student']
    students/ <int:pk>/delete/ [name='delete_student']
    students/ <int:pk>/enroll/ [name='enroll_student']

The current path, students/187/enroll/, matched the last one.

You’re seeing this error because you have DEBUG = True in your Django settings file. Change that to False, and Django will display a standard 404 page.
http://127.0.0.1:8000/students/187/enroll/  the enroll button should  take us to student dashboard individual becouse we clicked on specific student where we can access the section of subjects he is currently learning  so you can check or uncheck if the student is not intrested in learning that subject  like we have humanities which are there in number and we have 4 streams so the 2 will combine and do agriculture and the rest will have one so like if north and south do agriculture  the east will do computer ,west do business, to make it professional also lets add form subject selection dashboard where we have list of diffrent forms cards where when you click on like form 1 you will go to that specific one and you will be able  to select stream and now click on subjectects that stream will do the subjects should be in a just a good place where each is categorized in languages we have boolean selection for english,kiswahili then we have sciences  having Biology,physis,chemistry and the checkboxes so when you check for the east all the students in east form one will be availble in there dashboard 


http://127.0.0.1:8000/exams/  from here i should go to the dashbard showing forms like form1,form2,form3,form4 then when i enter to form3 or any i get streams then if i click on any stream like south i will see the subject groups like sciences,mathematics,technicals,humanities, languages then when i enter to humanities i will see the related subjects like geography,cre,history then when i enter to a subject like geography now i will get the selection between the excel sheet upload and i should be able to click and download it then i will be able to get to a paper ratio  section and i should specify the type of ratio or if  i deseclt i should enter the maxmum marks and it will be converted to percentage for the grade calculations then the enter result form in table like as we had before containing  name,admin,marks,then a combo at the end containing the grades x and y which can also be entered  then that form like a table  we will have buttons for upload just below it after clicking upload the students whose marks are entered are filtered out and there details are updated on a list of subject result which will also be availabe button to take you to the subject list which contains No this is auto increment number,Name,Adm for admission number ,marks showing the x and y 