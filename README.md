
# 🩺 Hospital Assistant Chatbot

An intelligent chatbot designed to streamline hospital operations such as appointment booking, doctor selection, department suggestions, and symptom-based recommendations. Built with **Dialogflow**, **FastAPI**, and **MySQL**, with optional **Google Sheets + Pipedream** integration for cloud-based appointment management.

---

## 📌 Features

- 🗣️ Natural conversation using **Dialogflow**
- 🏥 Appointment booking with dynamic **doctor & department selection**
- 📅 Date/time slot availability based on **live database queries**
- 💡 Symptom-based department recommendations using AI
- 📋 Integration with **Google Sheets (via Pipedream)** for no-code appointment tracking
- ⚙️ Built with **FastAPI** backend and **MySQL** or **Google Sheets** as DB
- 🧠 Easily extendable for labs, ICU, bed space, and other services

---

## 🚀 Tech Stack

| Layer | Tech |
|------|------|
| Chatbot | Dialogflow CX/ES |
| Backend API | FastAPI (Python) |
| Database | MySQL / Google Sheets |
| Hosting (dev) | Ngrok / Localhost |
| Optional | Weaviate (Vector DB for symptom search) |

---


---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/mikhlas911/Hospital_Assistant_chatbot.git
cd Hospital_Assistant_chatbot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run FastAPI Server

```bash
uvicorn backend_code:app --reload
```

### 4. Connect to Dialogflow Fulfillment

- Set your webhook URL (use Ngrok for dev):
  ```
  https://<your-ngrok-url>/webhook
  ```
- Deploy intents & entities (if exported in `/dialogflow/`)

### 5. (Optional) Set up Google Sheets + Pipedream

- Follow `/google_sheets/pipedream_workflow.md` for setup
- Connect to your Google Sheets for appointments

---

## 📸 Screenshots

| Chatbot UI | Architecture |
|------------|--------------|
![image](https://github.com/user-attachments/assets/48faeed3-70ff-4a72-a5a5-7f9eb303ba15)
| ![chatbot d![chatbot in website](https://github.com/user-attachments/assets/4759e37d-5643-465a-a02d-3f0d4103ac85)
|![mysql_db_pic1](https://github.com/user-attachments/assets/d3da5296-89a3-4186-8543-71e852a3186f)
![Doctors_list](https://github.com/user-attachments/assets/f14e74f6-75d0-4997-a53c-ecce5ef7c0e2)
![Sample_departments](https://github.com/user-attachments/assets/0ec9e49a-7d61-47a7-aedc-03842d618558)

emo](docs/chatbot_demo.gif) | ![architecture](docs/architecture.png) 


---

## 📃 License

Licensed under the **Apache License 2.0**.  
Feel free to use, modify, and distribute with attribution.

---

## 🙌 Credits

Developed by [@mikhlas911](https://github.com/mikhlas911) — Biomedical + AI + Cybersecurity Enthusiast 💡  
Got inspired? Feel free to **star 🌟** the repo or reach out for collaborations!
