import os
import sys
import logging
import json
import time
import datetime
import tableauserverclient as TSC

from DownloadConfiguration import *

start_time = time.time()
tableau_auth = TSC.TableauAuth(USER, PASSWORD, site_id=SITENAME)
server = TSC.Server(SERVER)
starttimestamp = datetime.datetime.now()
start_time = time.time()
fldrmonth = starttimestamp.strftime("%m")
fldryear = starttimestamp.strftime("%Y")
paging_options = TSC.RequestOptions(pagesize=1000)

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
    if not os.path.exists(MAINFOLDER + osparentfolder + ossubfolder1 + ossubfolder2):
        os.makedirs(MAINFOLDER + osparentfolder + ossubfolder1 + ossubfolder2)

create_folders("logs")

logging.basicConfig(filename=LOGFILE,format='%(asctime)s %(message)s', level=logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)  # Sets the logging level in the requests library to WARNING to avoid HTTP INFO calls appearing in the log

logging.info('Process started : ' + str(datetime.datetime.now()))

with server.auth.sign_in(tableau_auth):
	
	with open(os.path.join(FILELOC, 'TableauProjects'+"."+"json")) as data_file:
		data = json.load(data_file)
		logging.info('Successfully loaded JSON file : '+ str(data_file))
		for i in range (0, len (data['projects'])):
			logging.info('Started download for '+ data['projects'][i]['name'])
			DWNLDSTARTTIME = time.time()
			DWNLDPATH = MAINFOLDER + data['projects'][i]['name'] + "\\" + fldryear + "\\" + fldrmonth + "\\"
			create_folders(data['projects'][i]['name'], fldryear, fldrmonth)
			logging.info('Download path created : ' + DWNLDPATH)
			all_workbooks = list(TSC.Pager(server.workbooks, paging_options))
			for wb in all_workbooks:
				if wb.project_name == data['projects'][i]['name']:
					server.workbooks.download(wb.id, filepath=DWNLDPATH)
			DWNLDCOMPTIME = time.time()
			logging.info('Total download time (mins) : ' + str(float(DWNLDCOMPTIME - DWNLDSTARTTIME)/60))
		data_file.close()

server.auth.sign_out()
logging.shutdown()

logging.info('Process complete : ' + str(datetime.datetime.now()))

totalruntime = time.time()

logging.info('Total elapsed time (mins) : ' + str(float(totalruntime - start_time)/60))
logging.info("==============================")
logging.shutdown()

sys.exit()





