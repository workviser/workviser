from fastapi import APIRouter,Body,Query,status
from app.APIValidation.TaskSchema import TaskCreate,TaskAssignResponse
from typing import List, Dict
from app.APIValidation.EmployeeSchema import ActiveEmployee, InactiveEmployee, ExpertiseRequest
from app.controller.manager_controller import assigntask
from app.controller.manager_controller import find_optimal_employees_by_expertise

from app.controller.manager_controller import showallmanagertask
from app.controller.manager_controller import get_task_details
from app.models.Employee import Employee
from app.controller.manager_controller import create_employee

# from app.controller.manager_controller import signup_manager
# from app.controller.manager_controller import enroll_employee
router = APIRouter()

# @router.post("/login",)

# @router.post("/register",)
# def register_manager(manager: Manager):
#    return signup_manager(manager)

# @router.post("/enroll_employee")
# def enroll_employee(employee: Employee):
#    return enroll_employee(employee)

# In your route:
@router.post("/assign_task", status_code=201, response_model=TaskAssignResponse)
async def assign_task(
    task_data: TaskCreate=Body(...),
    manager_id: str=Query(...) ,
    employee_id: str=Query(...) 
):
    return await assigntask(task_data, manager_id, employee_id)

@router.post("/optimalexpertise", response_model=Dict[str, List[ActiveEmployee | InactiveEmployee]],
    summary="Get employees sorted by optimal expertise",
    description="Returns employees grouped by expertise domains with hybrid sorting: "
              "1. Inactive high-scorers (≥80) first, "
              "2. Active high-scorers (≥80) by availability, "
              "3. Inactive low-scorers (<80), "
              "4. Active low-scorers (<80) by availability"
)
async def get_optimal_employees(request: ExpertiseRequest):
    return await find_optimal_employees_by_expertise(request.expertise_list)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def createemployee(
    employee:Employee=Body(...)
):return await create_employee(employee) 


@router.get("/get_tasks")
async def get_tasks(manager_id: str=Query(...)):
   return await showallmanagertask(manager_id)

@router.get("/view_task")
async def viewtaskdetails(taskid : str=Query(...)):
    return get_task_details(taskid)

from uuid import uuid4
from datetime import datetime
from app.database import manager_collection, employee_collection, task_collection
from app.APIValidation.TaskSchema import TaskAssignResponse


@router.post("/webhook/assign-task", response_model=TaskAssignResponse)
async def assign_task_from_webhook(request: Request):
    try:
        payload = await request.json()

        manager_id = payload.get("manager_id")
        employee_id = payload.get("employee_id")
        task_data = payload.get("task")

        if not (manager_id and employee_id and task_data):
            raise HTTPException(status_code=400, detail="Missing required fields")

     
        manager = await manager_collection.find_one({"id": manager_id})
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")

        employee = await employee_collection.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        if not employee.get("fcm_token"):
            raise HTTPException(status_code=400, detail=f"Employee {employee_id} has no FCM token registered")

        # Flatten and clean task data
        if "image_url" in task_data:
            task_data["image_url"] = str(task_data["image_url"])
        if "document_url" in task_data:
            task_data["document_url"] = str(task_data["document_url"])
        if "priority" in task_data and hasattr(task_data["priority"], "value"):
            task_data["priority"] = task_data["priority"].value
        if "dateofassignment" in task_data:
            task_data["dateofassignment"] = datetime.fromisoformat(task_data["dateofassignment"]).isoformat()
        if "duration" in task_data:
            task_data["duration"] = datetime.fromisoformat(task_data["duration"]).isoformat()
        if "requirements" not in task_data or task_data["requirements"] is None:
            task_data["requirements"] = []

        task_document = {
            **task_data,
            "id": str(uuid4()),
            "manager_id": manager_id,
            "employee_id": employee_id,
            "status": False,
            "Accepted_status": False,
            "created_at": datetime.now().isoformat()
        }

        result = await task_collection.insert_one(task_document)
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to create task")

        return TaskAssignResponse(
            message="Task assigned successfully",
            task_id=str(result.inserted_id)
        )

    except HTTPException:
        raise
    except Exception as e:
       
        raise HTTPException(status_code=500, detail="Internal Server Error")
# @router.put("/update_task/{task_id}")

# @router.delete("/delete_task/{task_id}")

# @router.get("/free_employee")

# @router.get("/task_status/{task_id}")

# @router.get("/get_project_status")
