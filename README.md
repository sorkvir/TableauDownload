# TableauDownload
Python script to download workbooks from a Tableau Server.  Developed against version 2.2 of the Tableau Server RESTAPI.

Publishing:
boundary string should be a GUID in header:
https://onlinehelp.tableau.com/current/api/rest_api/en-us/REST/rest_api_concepts_publish.htm
"Each section of the request body begins with a Content-Disposition header and a Content-Type header that describes the type of data in that section. The following example shows the request body for a Publish Workbook request. For this example, the boundary string has been set in the header to 6691a87289ac461bab2c945741f136e6"

