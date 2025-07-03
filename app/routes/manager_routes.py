from fastapi import APIRouter,Body,Query,status,Request,HTTPException
from app.APIValidation.TaskSchema import TaskCreate,TaskAssignResponse
from typing import List, Dict
from app.APIValidation.EmployeeSchema import ActiveEmployee, InactiveEmployee, ExpertiseRequest, OptimalEmployeeResponse
from app.controller.manager_controller import assigntask
from app.controller.manager_controller import find_optimal_employees_by_expertise
from app.controller.manager_controller import find_most_optimal_employee
from app.controller.manager_controller import showallmanagertask
from app.controller.manager_controller import get_task_details
from app.models.Manager import Manager
from app.models.Employee import Employee
from app.controller.manager_controller import create_employee
from uuid import uuid4
from uuid import UUID
from datetime import datetime
from app.database import manager_collection, employee_collection, task_collection,project_collection
from app.APIValidation.TaskSchema import TaskAssignResponse
from app.models.Project import Project

router = APIRouter()

# This route is used at manager end to assign a particular task, required API Input Data and Response is Present in APIValidation Folder
@router.post("/assign_task", status_code=201, response_model=TaskAssignResponse)
async def assign_task(
    task_data: TaskCreate=Body(...),
    manager_id: str=Query(...) ,
    employee_id: str=Query(...) 
):
    return await assigntask(task_data, manager_id, employee_id)

@router.post("/available", response_model=Dict[str, List[ActiveEmployee | InactiveEmployee]],
    summary="Get employees sorted by optimal expertise",
    description="Returns employees grouped by expertise domains with hybrid sorting: "
              "1. Inactive high-scorers (≥80) first, "
              "2. Active high-scorers (≥80) by availability, "
              "3. Inactive low-scorers (<80), "
              "4. Active low-scorers (<80) by availability"
)
async def get_optimal_employees(request: ExpertiseRequest):
    return await find_optimal_employees_by_expertise(request.expertise_list)

# This Route is used to get the optimal employee as a helper. It returns single most optimal employee
@router.post(
    "/optimalexpertise",
    response_model=str,
)
async def get_optimal_employees(
    request: ExpertiseRequest,
    
):
    return await find_most_optimal_employee(request.expertise_list)


# This route is used to register employee i.e. to create a new employee
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def createemployee(
    employee:Employee=Body(...)
):return await create_employee(employee) 


# This route is used to get all tasks assigned by manager 
@router.get("/get_tasks")
async def get_tasks(manager_id: str=Query(...)):
   return await showallmanagertask(manager_id)


# This route provides details of particular task
@router.get("/view_task")
async def viewtaskdetails(taskid : str=Query(...)):
    return await get_task_details(taskid)

# This route is used as a webhook to get event from OmniDimension Voice Agent. It pushes complete  post call logs at this endpoint. 
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
            duration = "03:00:00"  

        manager = await manager_collection.find_one({"name": manager_name})
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")

        employee = await employee_collection.find_one({"name": employee_name})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        if not employee.get("fcm_token"):
            raise HTTPException(status_code=400, detail=f"Employee {employee_name} has no FCM token registered")

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


@router.get("/details", response_model=Manager)
async def get_manager_details(manager_id: str = Query(...)):
    manager = await manager_collection.find_one({"id": manager_id})
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    return manager

@router.get("/manager/project/details", response_model=Project)
async def get_project_details(project_id: str = Query(...)):
    project = await project_collection.find_one({"id": project_id})
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    
    if "_id" in project:
        project["_id"] = str(project["_id"])  
    return project
