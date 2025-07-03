#information: this file contains our business logic for manager related tasks
from app.models.Manager import Manager
from app.APIValidation.TaskSchema import TaskCreate,TaskAssignResponse
from app.models.Employee import Employee
from app.database import employee_collection
from app.database import task_collection
from app.database import manager_collection
from fastapi import HTTPException,status
from app.database import project_collection
from app.APIValidation.EmployeeSchema import ActiveEmployee, InactiveEmployee
from datetime import datetime
from typing import List
from uuid import uuid4
from passlib.context import CryptContext
import logging
logger = logging.getLogger(__name__)


# This contains our business logic to assign a Task to Employee. This controller is basically used from Nextjs DashBoard
async def assigntask(task: TaskCreate, manager_id: str, employee_id: str) -> TaskAssignResponse:
    try:
        logger.info(f"Looking for manager with id: {manager_id}")

        manager = await manager_collection.find_one({"id": manager_id})
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")

        employee = await employee_collection.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found or not under your management")

        if not employee.get("fcm_token"):
            raise HTTPException(
                status_code=400,
                detail=f"Employee {employee_id} has no FCM token registered"
            )

        task_data = task.model_dump()

        task_document = {
            **task_data,
            "id": str(uuid4()),
            "manager_id": manager_id,
            "employee_id": employee_id,
            "task_status": False,
            "descriptive_task_status":"",
            "Accepted_status": False,
             "created_at": datetime.now()
        }

       
        task_document['dateofassignment'] = task_document['dateofassignment'].isoformat()
        task_document['duration'] = task_document['duration'].isoformat()
        task_document['priority'] = task_document['priority'].value
        

        result = await task_collection.insert_one(task_document)
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to create task")

        task_id = str(result.inserted_id)

        return TaskAssignResponse(
            message="Task assigned successfully",
            task_id=task_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


# It contains the logic to get all all optimal  employees as a list, it returns a list in priority order
async def find_optimal_employees_by_expertise(expertise_list: List[str]):
    try:
        if not expertise_list:
            return {}

        query = {"$or": [{f"expertise.{domain}": {"$exists": True}} for domain in expertise_list]}
        employees = await employee_collection.find(query).to_list(length=None)

        results = {}
        THRESHOLD = 80

        for domain in expertise_list:
            domain_employees = []
            
            for emp in employees:
                if domain in emp.get("expertise", {}):
                    score = emp["expertise"][domain]
                    is_active = emp.get("task_status", False)
                    avail_status = str(emp.get("availablity_status", "0")).strip()
                    
                    if is_active:
                        if avail_status.lower() == "available":
                            available_time = 0  
                        else:
                            available_time = int(float(avail_status)) if avail_status.replace('.','',1).isdigit() else 0
                            
                    else:
                        available_time = 0  
                        
                    employee_data = {
                        "id": str(emp["id"]),
                        "name": emp["name"],
                        "work_email": emp["work_email"],
                        "score": score,
                        "mental_status": emp.get("mental_status"),
                        "task_status": is_active,
                        "available_time": available_time
                    }

                    if score >= THRESHOLD:
                        priority = 1 if not is_active else 2 
                    else:
                        priority = 3 if not is_active else 4 

                    domain_employees.append({
                        "priority": priority,
                        "sort_score": -score,  
                        "sort_avail": available_time,
                        "data": ActiveEmployee(**employee_data) if is_active else InactiveEmployee(**employee_data)
                    })
            domain_employees.sort(key=lambda x: (
                x["priority"],  
                x["sort_score"],  
                x["sort_avail"]  
            ))
            
            results[domain] = [emp["data"] for emp in domain_employees]
        
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")



# It contains the logic to a single most optimal employee. It is used during needassistance to find most appropriate helper
# It used Threashold Value of 80 in their expertise score to determine the priority, it just find for the available employee
# Further enhacement : - Dynamic Priority Based on Time left to be free
async def find_most_optimal_employee(expertise_list: List[str]) -> dict:
    try:
        if not expertise_list:
            return {"id": None}

        
        query = {"$or": [{f"expertise.{domain}": {"$exists": True}} for domain in expertise_list]}
        employees = await employee_collection.find(query).to_list(length=None)

        THRESHOLD = 80
        candidate_employees = []

        for emp in employees:
            is_active = emp.get("task_status", False)
            avail_status = str(emp.get("availablity_status", "0")).strip()

           
            if is_active:
                if avail_status.lower() == "available":
                    available_time = 0
                else:
                    available_time = int(float(avail_status)) if avail_status.replace('.', '', 1).isdigit() else 0
            else:
                available_time = 0

            
            matched_scores = [
                emp["expertise"].get(domain, 0)
                for domain in expertise_list
                if domain in emp.get("expertise", {})
            ]
            if not matched_scores:
                continue
            best_score = max(matched_scores)
            
            if best_score >= THRESHOLD:
                priority = 1 if not is_active else 2
            else:
                priority = 3 if not is_active else 4

            candidate_employees.append({
                "priority": priority,
                "sort_score": -best_score,
                "sort_avail": available_time,
                "id": emp.get("id")
            })

        if not candidate_employees:
            return {"id": None}

        candidate_employees.sort(key=lambda x: (
            x["priority"],
            x["sort_score"],
            x["sort_avail"]
        ))
        return candidate_employees[0]["id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")




# this controller is used for signing up of new manager, this controller requires all manager details as mentioned in Folder APIValidation
def signup_manager(manager: Manager):
    try:
        manager_data = manager.model_dump()
        manager_data["created_at"] = datetime.now()
        result = manager_collection.insert_one(manager_data)
        if result.inserted_id:
            return {"message": "Manager registered successfully", "manager_id": str(result.inserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Internal Server Error")

    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    


# employee enrollement logic
def enroll_employee(employee:Employee):
    try:
        employee_data = employee.model_dump()
        employee_data["created_at"] = datetime.now()
        result = employee_collection.insert_one(employee_data)
        if result.inserted_id:
            return {"message": "Employee enrolled successfully", "employee_id": str(result.inserted_id)}
        else:
            raise HTTPException(status_code=500, detail="Internal Server Error")

    except HTTPException as http_exc:
        raise http_exc
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# password hash creation
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# this controller is used to create an employee
async def create_employee(employee: Employee):
    existing = await employee_collection.find_one({
        "$or": [{"work_email": employee.work_email}, {"id": employee.id}]
    })
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee with this ID or work email already exists."
        )

    employee_dict = employee.model_dump()
    employee_dict["password"] = hash_password(employee.password.get_secret_value())

    employee_dict["created_at"] = datetime.utcnow()
    employee_dict["id"] = employee_dict.get("id", str(uuid4()))

    await employee_collection.insert_one(employee_dict)
    return {"message": "Employee registered successfully", "employee_id": employee_dict["id"]}





#this is helper for below controller
def safe_str(value):
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace")
        except:
            return "<binary>"
    return value

#this controller contains to logic to find out tasks given by a particular manager.
async def showallmanagertask(manager_id: str):
    print(manager_id)

    tasks_cursor = task_collection.find({"manager_id": manager_id})
    tasks = await tasks_cursor.to_list(length=100)

    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found for this manager.")

    
    manager = await manager_collection.find_one({"id": manager_id})
    manager_name = manager["name"] if manager else "Unknown"

    enriched_tasks = []

    for task in tasks:
        
        employee_id = task.get("employee_id")
        project_id = task.get("project_id")

        if not employee_id or not project_id:
            continue

        employee = await employee_collection.find_one({"id": employee_id})
        project = await project_collection.find_one({"id": project_id})

        employee_name = employee["name"] if employee else "Unknown"
        project_name = project["name"] if project else "Unknown"

        
        enriched_task = {
            "task_id": safe_str(task.get("id")),
            "task_name": safe_str(task.get("name")),
            "employee_name":safe_str(employee.get("name")),
            "description": safe_str(task.get("description")),
            "priority": safe_str(task.get("priority")),
            "status": safe_str(task.get("status")),
            "accepted": task.get("Accepted_status", False),
            "reject_reason": safe_str(task.get("reject_reason")),
            "employee_name": safe_str(employee_name),
            "manager_name": safe_str(manager_name),
            "project_name": safe_str(project_name),
            "created_at": safe_str(task.get("created_at"))
        }

        try:
            enriched_tasks.append(enriched_task)
        except Exception as e:
            raise e

    return enriched_tasks




#this controller to used to fetch the compete data regarding task, it is used by manager to get to know complete details of  any task assigned by him/her
async def get_task_details(taskid: str):
    
    task = await task_collection.find_one({"id": taskid})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    employee = await employee_collection.find_one({"id": task["employee_id"]})
    employee_name = employee["name"] if employee else "Unknown"

    manager = await manager_collection.find_one({"id": task["manager_id"]})
    manager_name = manager["name"] if manager else "Unknown"

    project = await project_collection.find_one({"id": task["project_id"]})
    project_name = project["name"] if project else "Unknown"

    task_details = {
        "task_id": task["id"],
        "task_name": task["name"],
        "description": task["description"],
        "priority": task["priority"],
        "task_status": task["status"],
        "descriptive_task_status":"In Progress",
        "accepted": task.get("Accepted_status", False),
        "reject_reason": task.get("reject_reason"),
        "duration": str(task["duration"]),
        "date_of_assignment": task["dateofassignment"],
        "employee_id": task["employee_id"],
        "employee_name": employee_name,
        "manager_id": task["manager_id"],
        "manager_name": manager_name,
        "project_id": task["project_id"],
        "project_name": project_name,
        "created_at": task["created_at"],
        "requirements": task.get("requirements", []),
        "image_url": task.get("image_url"),
        "document_url": task.get("document_url")
    }

    return task_details
