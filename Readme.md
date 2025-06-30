# 🧠 WorkViser: AI-Powered Productivity Platform for Remote Teams

WorkViser is a cross-platform AI-powered software tool designed to **enhance the productivity and efficiency** of **remotely working employees and managers**. It uses voice automation, real-time notifications, and smart task orchestration to streamline communication and work management.


---

## 🏗️ Architecture Diagram

![Screenshot](./Screenshot%202025-06-30%20181622.png)

<!-- Replace the above path with your actual diagram image or external link -->

---

WorkViser is designed to optimize remote workflows with a modular architecture:

- 🎙️ **Voice Agent (OmniDimension)**: Users can access the AI agent by simply calling a phone number. The voice assistant is hosted and managed via OmniDimension, providing task assistance and conversational support without requiring local setup.
- ⚙️ **Backend**: FastAPI handles business logic, authentication, and API endpoints.
- 💼 **Manager Frontend**: A Next.js dashboard for assigning, tracking, and evaluating employee tasks.
- 🖥️ **Employee Desktop Client**: Built with C# .NET for notifications, check-ins, and voice triggers.
- 📡 **MongoDB**: NoSQL database for efficient storage of task, user, and interaction data.

---

## 🧰 Tech Stack

| Component           | Technology/Service                         |
|---------------------|---------------------------------------------|
| 🧠 Voice Agent       | **OmniDimension** – Accessible via phone call |
| 🖥️ Employee App      | **C# .NET** – Windows desktop application    |
| 🌐 Manager Frontend  | **Next.js** – React, Tailwind CSS            |
| ⚙️ Backend API       | **FastAPI (Python)**  |
| 🗃️ Database          | **MongoDB** – Cloud/Local NoSQL datastore    |
| 🚀 Deployment        | AWS EC2, GitHub Actions            |

---

## ⚙️ Backend Installation (FastAPI)

```bash
# Step 1: Clone the repository
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>/server
