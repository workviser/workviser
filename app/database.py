#information: this file contains our configuration for mongoDB

import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = "mongodb+srv://workviseraws:0NXOubYehEVjby4x@cluster0.oi0xh0i.mongodb.net/"
print("The Format is "+ MONGO_URI)
# changed
DATABASE_NAME = os.getenv("DATABASE_NAME","WorkviserDB")

# MongoDB client setup
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
database = client[DATABASE_NAME]

# Collections
employee_collection = database.Employee
task_collection = database.Task
conversation_collection = database.Conversation
manager_collection = database.Manager
project_collection = database.Project

