from fastapi import APIRouter,Body,Query,status,Request,HTTPException
from app.APIValidation.TaskSchema import TaskCreate,TaskAssignResponse
from typing import List, Dict
from app.APIValidation.EmployeeSchema import ActiveEmployee, InactiveEmployee, ExpertiseRequest, OptimalEmployeeResponse
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

# @router.post("/optimalexpertise", response_model=Dict[str, List[ActiveEmployee | InactiveEmployee]],
#     summary="Get employees sorted by optimal expertise",
#     description="Returns employees grouped by expertise domains with hybrid sorting: "
#               "1. Inactive high-scorers (≥80) first, "
#               "2. Active high-scorers (≥80) by availability, "
#               "3. Inactive low-scorers (<80), "
#               "4. Active low-scorers (<80) by availability"
# )
# async def get_optimal_employees(request: ExpertiseRequest):
#     return await find_optimal_employees_by_expertise(request.expertise_list)

@router.post(
    "/optimalexpertise",
    response_model=OptimalEmployeeResponse,
    summary="Get employees sorted by optimal expertise",
    description="Returns employees grouped by expertise domains with hybrid sorting..."
)
async def get_optimal_employees(
    request: ExpertiseRequest,
    
):
    return await find_most_optimal_employee(request.expertise_list)

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
        extracted = payload.get("call_report", {}).get("extracted_variables", {})

        manager_name = extracted.get("manager_name")
        employee_name = extracted.get("employee_name")
        description = extracted.get("description")
        priority = extracted.get("priority", "").upper()
        requirements_str = extracted.get("requirements", "")
        dateofassignment = extracted.get("dateofassignment")
        duration = extracted.get("duration")

        # Clean/normalize data
        if not manager_name or not employee_name or not description:
            raise HTTPException(status_code=400, detail="Missing required fields in extracted_variables")

        if priority == "VERY HIGH":
            priority = "HIGH"
        elif priority == "NOT PROVIDED":
            priority = "MEDIUM"

        requirements = [req.strip() for req in requirements_str.split("and") if req.strip()]
        if not requirements:
            requirements = ["General"]

        if not dateofassignment or "not provided" in dateofassignment.lower():
            dateofassignment = datetime.now().strftime("%Y-%m-%d")

        if not duration or "not provided" in duration.lower():
            duration = "03:00"  # Default to 3 hours

        # Find manager and employee
        manager = await manager_collection.find_one({"name": manager_name})
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")

        employee = await employee_collection.find_one({"name": employee_name})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        if not employee.get("fcm_token"):
            raise HTTPException(status_code=400, detail=f"Employee {employee_name} has no FCM token registered")

        # Compose task
        task_document = {
            "id": str(uuid4()),
            "name": f"Task from {manager_name}",
            "description": description,
            "priority": priority,
            "requirements": requirements,
            "dateofassignment": dateofassignment,
            "duration": duration,
            "image_url": "",
            "document_url": "",
            "manager_id": manager["id"],
            "employee_id": employee["id"],
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
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/webhook/assigntask")
async def assign_task_from_webhook(request: Request):
    try:
        payload = await request.json()
        print("Payload:", payload)
        return {"status": "OK"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
# @router.put("/update_task/{task_id}")

# @router.delete("/delete_task/{task_id}")

# @router.get("/free_employee")

# @router.get("/task_status/{task_id}")

# @router.get("/get_project_status")
