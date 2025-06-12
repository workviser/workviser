# # guide:-  @app.get("/")   this is basic get request

# #@app.get("/items/{item_id}")   this is get request with parameter
# def read_item(item_id: int):
#     return {"item_id": item_id}

# from pydantic import BaseModel
# class Item(BaseModel):
#     name: str
#     price: float
# @app.post("/items/")
# def create_item(item: Item):     this is post request
#     return {"item": item}

# @app.put("/items/{item_id}")
# def update_item(item_id: int, item: Item):     
#     return {"item_id": item_id, "item": item}    this is put request 

# @app.delete("/items/{item_id}")         this is delete request
# def delete_item(item_id: int):
#     return {"message": f"Item {item_id} deleted"}

# @app.get("/search/")                          this is query request
# def search_items(query: str = None):
#     return {"query": query}


from fastapi import APIRouter,Query,Body
from pydantic import BaseModel
from app.APIValidation.accept_reject_status import accceptrequest,acceptresponse
from app.APIValidation.TaskSchema import TaskNotificationResponse
from app.controller.employee_controller import accept_reject_taskcontroller
from app.controller.employee_controller import complete_task
from app.controller.conversation import addconversation
from app.controller.employee_controller import get_task_notification
router = APIRouter()




# This route is used by employee to check if any new task is assigned to him or not
# Continnuously after 1 min this route will be pinged by client(c#)
@router.get("/notifications", response_model=TaskNotificationResponse)
async def get_employee_notifications(
    employee_id: str = Query(...)
):
    return await get_task_notification(employee_id)



# This route is used to accept or reject the task from user end. 
# If the task is accepted the user will send taskid , acceptrequest (present in APIValidation Folder)
# If the task is rejected then the user needs to submit a reason for it
@router.post("/updatetaskstatus")
async def accept_reject_task(
    taskid: str = Query(...),
    data: accceptrequest= Body(...)
):
    return await accept_reject_taskcontroller(data,taskid)



# This route is used to accept the response from user rapidly based on cs value
# This route will continuously accept response from user untill the task is completed
# It requires taskid , employeeid as query string and requires userresponse in body
@router.post("/response")
async def acceptresponse(
    taskid: str=Query(...),
    useresponse: str=Body(...),
    employeeid: str=Query(...)
):
    return await addconversation(taskid,employeeid,useresponse)



class TaskCompletionRequest(BaseModel):
    completion_status: bool = True
    notes: str = None

# This route is used when the task is completed
@router.post("/complete_task/{task_id}")
async def end_task(
    task_id: str,
    request: TaskCompletionRequest = Body(...)
):
    """
    Endpoint to mark a task as complete
    """
    return await complete_task(
        task_id=task_id,
        completion_status=request.completion_status,
        notes=request.notes
    )


# @router.post("/login",)

# @router.get("/view_assigned_task")

# @router.post("/accept_task/{task_id}")

# @router.post("/reject_task/{task_id}")

# @router.get("/get_task_status/{task_id}")

# @router.get("/get_project_status/{project_id}")

# @router.put("/update_task_status/{task_id}")

# @router.get("/view_own_profile")

# @router.get("/view_assigned_expert")

# @router.post("/reply/{conversation_id}")


