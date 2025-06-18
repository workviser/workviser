from app.database import conversation_collection,task_collection
from app.models.Conversation import EmployeeStatus
from datetime import datetime,timezone
from app.models.Conversation import TaskConversationEntry
from app.wwapicall.mental_state_analyzer import mental_status_analyzer

# this function may have some issues , approch is correct but will fail in some conditions 
# def analyze_mental_state(message: str) -> EmployeeStatus:
#     if "help" in message.lower():
#         return EmployeeStatus.NeedAssitance
#     elif "waiting" in message.lower():
#         return EmployeeStatus.WaitingForResponse
#     elif "trying" in message.lower():
#         return EmployeeStatus.Trying
#     elif "give up" in message.lower():
#         return EmployeeStatus.givenup
#     else:
#         return EmployeeStatus.Trying 


async def addconversation(taskid: str,employeeid:str, response: str):
   
    conversation = await conversation_collection.find_one({"task_id": taskid})
    if not conversation:
        raise ValueError("Conversation with the given task ID does not exist")

    
    task_doc = await task_collection.find_one({"id": taskid,"employee_id":employeeid})
    if not task_doc:
        raise ValueError("Task not found")

    task_details = task_doc.get("description", "No task description provided")

    new_entry = TaskConversationEntry(
        # there was an error ragrding time zone seriliazation so removed by adding sioformat date 17/6/2025 time 11:39Pm 
        timestamp=datetime.now(timezone.utc).isoformat(),
        message=response,
        mental_status=""  
    )
    
    history = conversation.get("task_Conversation_history", [])
    history.append(new_entry.dict(exclude={"mental_status"}))  

    updated_status = mental_status_analyzer(convo_history=history, taskdetails=task_details)
    
    new_entry.mental_status = updated_status
    history[-1]["mental_status"] = updated_status  
    print(f""" Conversation.py  \n The Complelete Conversation History After Processing is \n :
          {history}
          """)

    await conversation_collection.update_one(
        {"task_id": taskid},
        {
            "$set": {
                "task_Conversation_history": history,
                "employee_message": response,
                "status": updated_status
            }
        }
    )

    return {"status": "success", "message": "Response added with updated mental status"}

print(datetime.now(timezone.utc).isoformat())


