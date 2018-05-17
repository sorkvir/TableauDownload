#####
# Author: Mike McCann
# Create Date: 02/21/17
# This script downloads workbooks from the Tableau Server for archival purposes.
# 
# Tableau API Version:  2.2
# Python Version:  2.7
#
#####

import math
import xml.etree.ElementTree as ET  
import requests  
import sys
import json
import os
import datetime
import logging
import time


from requests.packages.urllib3.fields import RequestField
from requests.packages.urllib3.filepost import encode_multipart_formdata
from configuration import *

xmlns = {"t": 'http://tableau.com/api'}  # The namespace for the REST API is 'http://tableausoftware.com/api' for Tableau Server 9.0 or 'http://tableau.com/api' for Tableau Server 9.1 or later 
starttimestamp = datetime.datetime.now()    # Gets the current date/time
start_time = time.time()    # Gets the current date/time and stores it to determine elapsed_time
fldrmonth = starttimestamp.strftime("%m")   # Returns the current month as the two digit month number
fldryear = starttimestamp.strftime("%Y")    # Returns the current year as YYYY
LOGFILE = DWNLDPATH + "\\" + "logs\\" + "TableauArchive" + str(starttimestamp.strftime("%d-%m-%Y")) + ".log"

def create_folders(parentfoldername, subfolder1=None, subfolder2=None):
    osparentfolder = "\\" + parentfoldername + "\\"
    if subfolder1 is None:
        ossubfolder1 = ""
    else:
        ossubfolder1 = "\\" + subfolder1 + "\\"
    if subfolder2 is None:
        ossubfolder2 = ""
    else:
        ossubfolder2 = "\\" + subfolder2 + "\\"
    if not os.path.exists(DWNLDPATH + osparentfolder + ossubfolder1 + ossubfolder2):
        os.makedirs(DWNLDPATH + osparentfolder + ossubfolder1 + ossubfolder2)

def _encode_for_display(text):
    """
    Encodes strings so they can display as ASCII in a Windows terminal window.
    This function also encodes strings for processing by xml.etree.ElementTree functions. 
    
    Returns an ASCII-encoded version of the text. Unicode characters are converted to ASCII placeholders (for example, "?").
    """
    return text.encode('ascii', errors="backslashreplace").decode('utf-8')

def sign_in(name, password, site=""):
    """
    Signs in to the server specified in the global SERVER variable.

    'name'     is the name (not ID) of the user to sign in as.
               Note that most of the functions in this example require that the user
               have server administrator permissions.
    'password' is the password for the user.
    'site'     is the ID (as a string) of the site on the server to sign in to. The
               default is "", which signs in to the default site.

    Returns the authentication token and the site ID.
    """
    url = SERVER + "/api/2.2/auth/signin"

    # Builds the request
    xml_payload_for_request = ET.Element('tsRequest')
    credentials_element = ET.SubElement(xml_payload_for_request, 'credentials', name=name, password=password)
    site_element = ET.SubElement(credentials_element, 'site', contentUrl=site)
    xml_payload_for_request = ET.tostring(xml_payload_for_request)

    # Makes the request to Tableau Server
    server_response = requests.post(url, data=xml_payload_for_request)
    if server_response.status_code != 200:
        print(server_response.text)
        sys.exit(1)
    # Reads and parses the response
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    
    # Gets the token and site ID
    token = xml_response.find('t:credentials', namespaces=xmlns).attrib.get('token')
    site_id = xml_response.find('.//t:site', namespaces=xmlns).attrib.get('id')
    user_id = xml_response.find('.//t:user', namespaces=xmlns).attrib.get('id')
    return token, site_id, user_id

def sign_out():
    """
    Destroys the active session
    """
    global TOKEN
    url = SERVER + "/api/2.2/auth/signout"
    server_response = requests.post(url, headers={'x-tableau-auth': TOKEN})
    TOKEN = None
    return

def _handle_error(server_response):
    """
    Parses an error response for the error subcode and detail message
    and then displays them.
    
    Returns the error code and error message.
    """
    print("An error occurred")
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    error_code = xml_response.find('t:error', namespaces=xmlns).attrib.get('code')
    error_detail = xml_response.find('.//t:detail', namespaces=xmlns).text
    print("\tError code: " + str(error_code))
    print("\tError detail: " + str(error_detail))
    return error_code, error_detail

def query_projects():
    """
    Returns a list of projects on the site (a list of <project> elements).

    The function paginates over results (if required) using a page size of 100.
    """
    pageNum, pageSize = 1, 100
    url = SERVER + "/api/2.2/sites/{0}/projects".format(SITE_ID)
    paged_url = url + "?pageSize={}&pageNumber={}".format(pageSize, pageNum)

    server_response = requests.get(paged_url, headers={"x-tableau-auth": TOKEN})
    server_response.encoding = "utf-8";
    if server_response.status_code != 200:
        print(_encode_for_display(server_response.text))
        sys.exit(1)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    
    total_count_of_projects = int(xml_response.find('t:pagination', namespaces=xmlns).attrib.get('totalAvailable'))

    if total_count_of_projects > pageSize:
        projects = []
        projects.extend(xml_response.findall('.//t:project', namespaces=xmlns))
        number_of_pages = int(math.ceil(total_count_of_projects / pageSize))
        
        # Starts from page 2 because page 1 has already been returned
        for page in range(2, number_of_pages + 1):
            paged_url = url + "?pageSize={}&pageNumber={}".format(pageSize, page)
            server_response = requests.get(paged_url, headers={"x-tableau-auth": TOKEN})
            if server_response.status_code != 200:
                print(_encode_for_display(server_response.text))
                sys.exit(1)
            projects_from_page = ET.fromstring(_encode_for_display(server_response.text)).findall('.//t:project', namespaces=xmlns)
            projects.extend(projects_from_page)
    else:
        projects = xml_response.findall('.//t:project', namespaces=xmlns)
    return projects

def query_workbooks(user_id):
    """
    Returns a list of workbooks that the current user has permission to read (a list of <workbook> elements).

    'user_id' is the LUID (as a string) of the user to get workbooks for.

    The function paginates over the results (if required) using a page size of 1000.
    """
    pageNum, pageSize = 1, 1000
    url = SERVER + "/api/2.2/sites/{0}/users/{1}/workbooks".format(SITE_ID, user_id)
    paged_url = url + "?pageSize={0}&pageNumber={1}".format(pageSize, pageNum)
    server_response = requests.get(paged_url, headers={"x-tableau-auth": TOKEN})
    if server_response.status_code != 200:
        print(_encode_for_display(server_response.text.encode))
        sys.exit(1)
    xml_response = ET.fromstring(_encode_for_display(server_response.text))
    total_count_of_workbooks = int(xml_response.find('t:pagination', namespaces=xmlns).attrib.get('totalAvailable'))
    if total_count_of_workbooks > pageSize:
        workbooks = []  # This list wil hold the users returned from Server
        workbooks.extend(xml_response.findall('.//t:workbook', namespaces=xmlns))
        number_of_pages = int(math.ceil(total_count_of_workbooks / pageSize))
        # Starts from page 2 since page 1 has already been returned
        for page in range(2, number_of_pages + 1):
            paged_url = url + "?pageSize={}&pageNumber={}".format(pageSize, page)
            server_response = requests.get(paged_url, headers={"x-tableau-auth": TOKEN})
            if server_response.status_code != 200:
                print(_encode_for_display(server_response.text))
                sys.exit(1)
            workbooks_from_page = ET.fromstring(_encode_for_display(server_response.text)).findall('.//t:workbook', namespaces=xmlns)
            # Adds the new page of workbooks to the list
            workbooks.extend(workbooks_from_page)
    else:
        workbooks = xml_response.findall('.//t:workbook', namespaces=xmlns)
    return workbooks	

# Signs in to get an authentication token and site ID to use later

# Creates the log folder, log file, and sets logging configuration

def findprojectguid():
    with open(os.path.join(FILELOC, 'TableauProjects'+"."+"json")) as data_file:
        data = json.load(data_file)
        for i in range (0, len (data['projects'])):
            for project in query_projects():
                if project.get('name') == data['projects'][i]['name']:
                    print (project.get('id'))
        data_file.close()

create_folders("logs")

logging.basicConfig(
	filename=LOGFILE, 
	format="%(asctime)s : %(levelname)s : %(message)s", 
	datefmt="%m/%d/%Y %I:%M:%S %p",
	level=logging.INFO)

logging.info("Logging Started: " + str(datetime.datetime.now()))
logging.getLogger("requests").setLevel(logging.WARNING)  # Sets the logging level in the requests library to WARNING to avoid HTTP INFO calls appearing in the log


logging.info('Logging into '+SERVER)
print("Signing in")

TOKEN, SITE_ID, MY_USER_ID = sign_in(USER, PASSWORD)

logging.info('Successfully logged into '+SERVER)



# Creates a list of Project GUID's based on JSON file.  Used to identify which workbooks to download
logging.info('Creating list of projects to download')
print("Creating list of projects to download")

ProjectIDList = []
with open(os.path.join(FILELOC, 'TableauProjects'+"."+"json")) as data_file:
    data = json.load(data_file)
    for i in range (0, len (data['projects'])):
        for project in query_projects():
            if project.get('name') == data['projects'][i]['name']:
                ProjectIDList.append(project.get('id')),
		logging.debug('Project added to list: ' + project.get('name') + ' with id of ' + project.get('id')),
    data_file.close()
logging.info('Project list created')
	
# Creates the folder structure to save the Tableau Workbooks in.
logging.info('Creating download folders')

print("Creating download folders")
with open(os.path.join(FILELOC, 'TableauProjects'+"."+"json")) as data_file:
	data = json.load(data_file)
	for i in range (0, len (data['projects'])):	
		create_folders(data['projects'][i]['name'], fldryear, fldrmonth)
	data_file.close()
logging.info('Download folders created')

# Downloads only the workbooks that have an Project ID in the ProjectIDList and saves them to the appropriate folder locations.
logging.info('Starting Workbook download')
print("Starting Workbook download")

downloadlist = [] 
for workbook in query_workbooks(MY_USER_ID):		
	for elem in workbook.iter("*"):
		for id in ProjectIDList:
			if elem.tag == '{http://tableau.com/api}project' and elem.get('id') == id:
				downloadurl = SERVER + "/api/2.2/sites/{0}/workbooks/".format(SITE_ID) +"".join(workbook.get('id')) + "/content downloadurl = SERVER + "/api/2.2/sites/{0}/workbooks/".format(SITE_ID) +"".join(workbook.get('id')) + "/content?includeExtract=TRUE"
				downloadlist.append(downloadurl)
				print("Downloading " + workbook.get('name'))
				for downloadurl in downloadlist:
					r = requests.get(downloadurl, headers={"x-tableau-auth":TOKEN})
					r.stream = True
					with open (DWNLDPATH + elem.get('name') + '\\' + fldryear + '\\' + fldrmonth + '\\' +workbook.get('name')+".twbx", "wb") as fd:
						for chunk in r.iter_content(chunk_size=128):
							fd.write(chunk)
							# Close stream?
				logging.info("Workbook downloaded: " + workbook.get('name'))
				logging.debug("Workbook downloaded: " + workbook.get('name') + " ID: " + workbook.get('id') + " URL: " + downloadurl)
				print("Complete")	
logging.info('Workbook download complete')
print('Download complete.  Ending session.')

# Ends sessions and closes log file.
logging.info('Signing out and invalidating authentication token')				

sign_out()

print("\nSigned out.  Authentication token has been invalidated")

logging.info('Signed out and authentication token is no longer valid')
logging.info('Process complete : ' + str(datetime.datetime.now()))

runtime = time.time()

logging.info('Total elapsed time: ' + str(float(runtime - start_time)/60))
logging.info("==============================")
logging.shutdown()

print('Total elapsed time (mins): ' + str(float(runtime - start_time)/60))
