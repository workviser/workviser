import os
from dotenv import load_dotenv
from together import Together
from PIL import Image
import base64
import json

# Load environment variables from .env file
load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

# Enhanced base prompt
base_prompt = """
Look at this screenshot of a developer's screen and describe what is happening. Be detailed and explain everything visible, including UI, code, error messages, and data.

**WHAT IS HAPPENING:**
1. What is the developer currently doing?
2. Which tools or files are visible (filenames, editors)?
3. What browser tabs or applications are open?
4. Is there a terminal or command prompt visible? If yes, analyze its output in deeply technical context.

**IF AND ONLY IF THERE ARE VISIBLE ERRORS:**
5. What is the exact error message you see?
6. What is causing this specific error?
7. How to fix it? Give 3 different solutions:
   - Solution 1: [most likely fix]
   - Solution 2: [alternative fix]
   - Solution 3: [fallback fix]
8. Which technical domain does the error belong to (Python, Node.js, React, etc.)?
9. Step-by-step: How would a developer fix this?

**IF THERE ARE GRAPHS OR STATISTICS:**
10. If any charts, plots, or statistical graphs are visible, explain:
   - What type of graph is shown?
   - What does it represent?
   - What insight can be derived?

**HELP NEEDED:**
11. What kind of developer could help? (Frontend, Backend, Data Scientist, DevOps, etc.)

**RULES:**
- Only describe errors if they are explicitly visible (red text, tracebacks, etc.)
- If no error: say “No visible errors.”
- Write in complete paragraphs, not short bullet points.
- Be specific and technical.
"""

# Helper to encode image to base64
def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

# Analyze a single image using vision model
def analyze_image(image_path):
    image_data = encode_image(image_path)

    response = client.chat.completions.create(
        model="meta-llama/Llama-Vision-Free",  # ✅ Correct model
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

    # Save individual image analysis
    img_name = os.path.basename(image_path).split('.')[0]
    with open(f"analysis_{img_name}.txt", "w") as f:
        f.write(content)

    return {
        "image": image_path,
        "analysis": content
    }

# Build summarization prompt from all per-image outputs
def build_summarization_prompt(image_analyses):
    prompt = """You are an AI assistant. Based on the following step-by-step analysis of screenshots, summarize:

1. What is the developer trying to accomplish overall?
2. If there are errors: What issues or errors did they face?
3. What is the likely cause of those errors?
4. Which type of developer can help (Backend, Python, etc.)?
5. What next step should they take?
6. If there is no error but the if and only if thers an image contains graphs/statistical content, give a brief explanation of the data.

Step-by-step analysis:\n\n"""

    for i, entry in enumerate(image_analyses, 1):
        prompt += f"Step {i} ({entry['image']}):\n"
        prompt += entry["analysis"] + "\n\n"

    prompt += "Now provide a concise summary with technical clarity."
    return prompt

# Main execution
def main(image_folder):
    results = []

    image_files = sorted([
        f for f in os.listdir(image_folder)
        if f.endswith(('.png', '.jpg', '.jpeg'))
    ])

    for image_file in image_files:
        path = os.path.join(image_folder, image_file)
        print(f"Analyzing {image_file}...")
        result = analyze_image(path)
        results.append(result)

    # Save all analysis results to JSON
    with open("all_image_analyses.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nGenerating summary...\n")
    summary_prompt = build_summarization_prompt(results)

    # Final summary generation
    summary_response = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",  # ✅ High-quality model
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful and verbose technical analyst. "
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

    # Print + Save the final summary
    final_summary = summary_response.choices[0].message.content.strip()
    print("===== FINAL SUMMARY =====")
    print(final_summary)

    with open("final_summary.txt", "w") as f:
        f.write(final_summary)

# Entry point
if __name__ == "__main__":
    image_dir = "images"  # Change as needed
    main(image_dir)
