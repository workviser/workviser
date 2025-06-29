async def starting_grant_assistant_employee(taskid:str ,employeeid:str,decoded_images:list ):
    """
    1.In this function we will be calling the vision analysis model by passing the employeeid and taskid to and the list of the decoded images i.e screenshots.
    2.The function will return the result of the vision analysis in an json format which will tell what is the probabale cause of the obstacle . and who person can solve this issue.
    3.The json will passsed to te Domain extractor to extrac the domains
    4.According to that filers sort will be appiled : A. PEmployee having Expertiese in the Particular Domain more than 3-4 Years (May vary accordingh to the company Policy)
                                                      B. And should be free withtin most 15 Min
    5.Prepare the New Helping task Details : ex. Whome to help ? what to do? what previously done? the screenhots.
    6.Now assign the Task and also Send the Email.
    """
    
