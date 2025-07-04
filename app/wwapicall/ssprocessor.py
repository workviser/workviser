import os
import json
import base64
from PIL import Image
from dotenv import load_dotenv
from together import Together
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient


# Load env and setup
load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
DATABASE_NAME = os.getenv("DATABASE_NAME", "workviser")

# MongoDB
mongo_client = AsyncIOMotorClient("mongodb+srv://workviseraws:0NXOubYehEVjby4x@cluster0.oi0xh0i.mongodb.net/")
db = mongo_client[DATABASE_NAME]
task_collection = db["Task"]



# Enhanced base prompt
base_prompt = """
Look at this screenshot of a developer's screen and describe what is happening. Be detailed and explain everything visible, including UI, code, error messages, and data.

*WHAT IS HAPPENING:*
1. What is the developer currently doing?
2. Which tools or files are visible (filenames, editors)?
3. What browser tabs or applications are open?
4. Is there a terminal or command prompt visible? If yes, analyze its output in deeply technical context.

*IF AND ONLY IF THERE ARE VISIBLE ERRORS:*
5. What is the exact error message you see?
6. What is causing this specific error?

8. Which technical domain does the error belong to (Python, Node.js, React, etc.)?
9. Step-by-step: How would a developer fix this?

*IF THERE ARE GRAPHS OR STATISTICS:*
10. If any charts, plots, or statistical graphs are visible, explain:
   - What type of graph is shown?
   - What does it represent?
   - What insight can be derived?

*HELP NEEDED:*
11. What kind of developer could help? (Frontend, Backend, Data Scientist, DevOps, etc.)

*RULES:*
- Only describe errors if they are explicitly visible (red text, tracebacks, etc.)
- If no error: say “No visible errors.”
- Write in complete paragraphs, not short bullet points.
- Be specific and technical.
"""

# Helper to encode image to base64
import base64
from io import BytesIO
from PIL import Image

# updates for proper encoding by nawaz 
def encode_image(image_input):
    """
    Takes either a file path (str) or a PIL.Image object.
    Returns base64-encoded image string.
    """
    if isinstance(image_input, str):
        # If it's a file path
        with open(image_input, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    
    elif isinstance(image_input, Image.Image):
        # If it's a PIL Image object
        buffered = BytesIO()
        image_input.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    else:
        raise ValueError("Unsupported input: must be a file path or PIL.Image")

# Analyze a single image using vision model
def analyze_image(image_path):
    # image_data = encode_image(image_path)
    image_data = encode_image(image_path)

    response = client.chat.completions.create(
        model="meta-llama/Llama-Vision-Free",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert vision assistant. Carefully examine the screenshot and explain everything in a clear, multi-sentence paragraph. "
                    "Make sure to explain terminal outputs, code, errors, and graphs. If multiple things are visible, cover each one detailed contextc."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": base_prompt
                    }
                ]
            }
        ],
        temperature=0.2,
        max_tokens=1024
    )

    content = response.choices[0].message.content.strip()

    return {
        "image": image_path,
        "analysis": content
    }



# Renamed and fixed: removed asyncio.run
async def get_task_description(task_id):
    print("🔍 Fetching task with ID:", task_id)
    task = await task_collection.find_one({"id": task_id})
    if task:
        return task.get("description", "No task description provided")
    else:
        print("❌ No task found.")
        return "No task found."



    


# Build summarization prompt from all per-image outputs and task description
def build_summarization_prompt(image_analyses, task_description):

    prompt = f"""You are an AI assistant. A developer is working on the following task:

**Task Description:** {task_description}

Based on the following step-by-step analysis of screenshots and keeping the Task Description in mind, summarize:

1. provide brief information about task description
2. What is the developer trying to accomplish overall?
3. If there are errors: What issues or errors did they face?
4. What is the likely cause of those errors?
5. Which type of developer can help (Backend, Python, etc.)?
6. If there is no error but the if and only if thers an image contains graphs/statistical content, give a brief explanation of the data.

Step-by-step analysis:\n\n"""

    for i, entry in enumerate(image_analyses, 1):
        prompt += f"Step {i} ({entry['image']}):\n"
        prompt += entry["analysis"] + "\n\n"

    prompt += "Now provide a concise summary with technical clarity."
    return prompt


# ✅ Main processing function
async def process_task(task_id, image_paths):
    results = []

    for image_path in image_paths:
        print(f"Analyzing {image_path}...")
        result = analyze_image(image_path)
        results.append(result)

    
    
    # ✅ Fetch task description
    task_description = await get_task_description(task_id)
    

    

    # ✅ Build final prompt
    summary_prompt = build_summarization_prompt(results, task_description)

    summary_response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful and verbose technical analyst provide brief information about task description"
                    "Answer each question one by one in detail manner, clearly and with structured reasoning like question then answer. "
                    "Include summaries of terminal activity and graphs where applicable. Avoid vague answers."
                )
            },
            {
                "role": "user",
                "content": summary_prompt
            }
        ],
        temperature=0.4,
        max_tokens=1024
    )

    final_summary = summary_response.choices[0].message.content.strip()

    # Save final summary only
    summary_json = {
        "task_id": task_id,
        "summary": final_summary
    }

    with open(f"{task_id}_summary.json", "w") as f:
        json.dump(summary_json, f, indent=2)

    return summary_json







