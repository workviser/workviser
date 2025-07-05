from app.wwapicall.ssprocessor import process_task
from app.wwapicall.domain_extractor import domain_extractor
from app.controller.manager_controller import find_most_optimal_employee
from app.controller.manager_controller import assigntask
from app.database import task_collection
from app.mailer.helperemail import send_workviser_task_email
async def starting_grant_assistant_employee(taskid:str ,employeeid:str,decoded_images:list ):
    """
    1.In this function we will be calling the vision analysis model by passing the employeeid and taskid to and the list of the decoded images i.e screenshots.
    2.The function will return the result of the vision analysis in an json format which will tell what is the probabale cause of the obstacle . and who person can solve this issue.
    3.The json will passsed to te Domain extractor to extrac the domains
    4.According to that filers sort will be appiled : A. PEmployee having Expertiese in the Particular Domain more than 3-4 Years (May vary accordingh to the company Policy)
                                                      B. And should be free withtin most 15 Min
    5.Prepare the New Helping task Details : ex. Whome to help ? what to do? what previously done? the screenhots.
    6.Now assign the Task and also Send the Email.
    7.And return the Name of the Helper Employee    
    """
    print("Enetered in the Needassistance.py")
    extracted_json = await  process_task(task_id=taskid,image_paths=decoded_images)
    print("The JSON after Processing is the screenshot is "+str(extracted_json))
    
    extracted_domains_for_helper_emp = domain_extractor("Below are the summary of the person who is failed in a task and suggesting the person , now extract the domains form here ::"+str(extracted_json)+"only print the list, dont say like Here is the list of domains extracted from the text. YOUR WORK IS TO ONLY RETURN THE LIST OF DOMAINS LIKE ['AWS','CLOUD','S3','DEPLOYMENT','STATIC HOSTING']")
    print("Type of the data recived is "+str(type(extracted_domains_for_helper_emp)))
    print("The Extracted Domains for the Employee is "+str(extracted_domains_for_helper_emp))
    best_helper_employees_list = await find_most_optimal_employee(extracted_domains_for_helper_emp)
    print("The best helper employees are "+str(best_helper_employees_list))
    
    taskdata = await task_collection.find_one({"id": taskid})
    print("The Helping Employee is"+str(taskdata))
    send_workviser_task_email("shrutilap01@gmail.com","Helper",str(taskdata),task_summary=extracted_json,decoded_images=decoded_images,task_id=taskid)
    
    assigntask()
    return best_helper_employees_list
