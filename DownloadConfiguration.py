#####
# Configuration file that contains the global variables for the 
# python file.  
# 
# Created so that modifications to global variables can be made 
# in a single file and not the main script
####
USER = '<<< TABLEAU USER >>>'                					# Set to your Tableau Server username. The user must be a server administrator.
PASSWORD = '<<< TABLEAU USER PASSWORD >>>'            					# Set to your Tableau Server password.
FILELOC = "C:\\Temp\\WorkbookDownload\\"    # Location of the files to be used by this script
SERVER = "<<< URL OF TABLEAU SERVER >>>"         # Set to the server URL without a trailing slash (/).
SITENAME=""										# Site on Tableau server to Publish
LOGFILENAME = 'download.log'                                # Location and name of logfile
MAINFOLDER = "C:\\Temp\\WorkbookDownload\\files\\"    # Location of the files used by this script
LOGFILE = MAINFOLDER + "\\" + "logs\\" + LOGFILENAME
####
