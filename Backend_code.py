from fastapi import FastAPI, Request
import mysql.connector
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import threading

# Load environment variables from .env file


app = FastAPI()


# Function to connect to the database
def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="Your_DB_Paasword",
            database="DB_name"
        )

    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        return None


# Function to send email
def send_email(to_email, subject, body):
    # Gmail credentials
    EMAIL_ADDRESS = "someone123@gmail.com"  # Replace with your Gmail
    APP_PASSWORD = "Your_API_Passcode"  # Replace with your App Password from google

    # Create email message
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Send email via Gmail SMTP
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()  # Identify with the server
        server.starttls()  # Secure connection
        server.ehlo()
        server.login(EMAIL_ADDRESS, APP_PASSWORD)  # Login with App Password
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


# Webhook endpoint
@app.post("/webhook")
async def webhook(request: Request):

    try:
        body = await request.json()
        session_id = body.get("session", "")
        query_result = body.get("queryResult", {})
        parameters = query_result.get("parameters", {})
        intent = query_result.get("intent", {}).get("displayName", "")
        contexts = query_result.get("outputContexts", [])



        if not intent:
            return {"fulfillmentText": "Intent not recognized."}

        if intent == "GetPatientDetails":
            patient_name = parameters.get("patient_name")
            phone_number = parameters.get("phone_number")


            if not patient_name:
                return {"fulfillmentText": "Could you please provide your name?"}

            return {
                "fulfillmentText": f"Thank you, {patient_name}. Now, please choose a department.",
                "outputContexts": [
                    {
                        "name": f"{session_id}/contexts/awaiting_patient_details",
                        "lifespanCount": 10,
                        "parameters": {
                            "patient_name": patient_name,
                            "phone_number": phone_number
                        }
                    }
                ]
            }

        elif intent == "GetDepartment":
            department = parameters.get("department")
            if not department:
                return {"fulfillmentText": "Which department do you need?"}

            db = get_db_connection()
            if not db:
                return {"fulfillmentText": "Database connection failed."}

            cursor = db.cursor()
            cursor.execute("SELECT name, available_days, available_time FROM doctors WHERE specialization = %s",
                           (department,))
            doctors = cursor.fetchall()
            cursor.close()
            db.close()

            if not doctors:
                return {"fulfillmentText": f"No doctors found in {department}."}

            doctor_list = "\n".join([f"{doctor[0]} (Available: {doctor[1]} at {doctor[2]})" for doctor in doctors])
            return {
                "fulfillmentText": f"Available doctors in {department}:\n{doctor_list}\nPlease choose one.",
                "outputContexts": [
                    {
                        "name": f"{session_id}/contexts/awaiting_doctor_selection",
                        "lifespanCount": 5,
                        "parameters": {
                            "department": department,
                            "doctors": [doctor[0] for doctor in doctors]
                        }
                    }
                ]
            }

        elif intent == "ChooseDoctor":
            doctor_name = parameters.get("doctor_name")
            if not doctor_name:
                return {"fulfillmentText": "Please choose a doctor from the list."}

            db = get_db_connection()
            if not db:
                return {"fulfillmentText": "Database connection failed."}

            cursor = db.cursor()
            cursor.execute("SELECT available_days, available_time FROM doctors WHERE name = %s", (doctor_name,))
            doctor = cursor.fetchone()
            cursor.close()
            db.close()

            if not doctor:
                return {"fulfillmentText": f"Doctor {doctor_name} not found."}

            available_days, available_time = doctor

            return {
                "fulfillmentText": f"{doctor_name} is available on {available_days} at {available_time}. Provide the appointment date (YYYY-MM-DD).",
                "outputContexts": [
                    {
                        "name": f"{session_id}/contexts/awaiting_appointment_details",
                        "lifespanCount": 5,
                        "parameters": {
                            "doctor_name": doctor_name,
                            "available_days": available_days,
                            "available_time": available_time
                        }
                    }
                ]
            }

        elif intent == "SelectAppointmentDate":
            appointment_date = parameters.get("date")
            appointment_time = parameters.get("time")
            doctor_name = parameters.get("doctor_name")
            patient_name = parameters.get("patient_name")  # Ensure this is captured in Dialogflow
            phone_number = parameters.get("phone_number")

            if not phone_number:
                for ctx in contexts:
                    if "awaiting_patient_details" in ctx.get("name", ""):
                        phone_number = ctx.get("parameters", {}).get("phone_number")
                        break

            if not doctor_name:
                for ctx in contexts:
                    if "awaiting_appointment_details" in ctx.get("name", ""):
                        doctor_name = ctx.get("parameters", {}).get("doctor_name")
                        break

            if not doctor_name:
                return {"fulfillmentText": "Please select a doctor first before choosing an appointment time."}

            if not appointment_date or not appointment_time:
                return {"fulfillmentText": f"Please provide both the appointment date and time for Dr. {doctor_name}."}

            db = get_db_connection()
            if not db:
                return {"fulfillmentText": "Database connection failed. Please try again later."}

            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT available_days, available_time FROM doctors WHERE name = %s", (doctor_name,))
            doctor_data = cursor.fetchone()

            if not doctor_data:
                cursor.close()
                db.close()
                return {"fulfillmentText": f"Doctor {doctor_name} not found. Please choose another doctor."}

            available_days = doctor_data["available_days"].split(", ")
            available_time = doctor_data["available_time"]

            try:
                parsed_date = datetime.fromisoformat(appointment_date)
                parsed_time = datetime.fromisoformat(appointment_time)
                appointment_day = parsed_date.strftime("%A")
                formatted_date = parsed_date.strftime("%Y-%m-%d")
                formatted_time = parsed_time.strftime("%I:%M %p")

                if appointment_day not in available_days:
                    cursor.close()
                    db.close()
                    return {
                        "fulfillmentText": f"Dr. {doctor_name} is not available on {appointment_day}. Available days: {', '.join(available_days)}."
                    }

                start_time_str, end_time_str = available_time.split(" - ")
                start_time = datetime.strptime(start_time_str, "%I:%M %p").time()
                end_time = datetime.strptime(end_time_str, "%I:%M %p").time()
                appointment_time_only = parsed_time.time()

                if not (start_time <= appointment_time_only <= end_time):
                    cursor.close()
                    db.close()
                    return {
                        "fulfillmentText": f"Dr. {doctor_name} is not available at {formatted_time}. Available time: {available_time}."
                    }

                cursor.close()
                db.close()

                # Store appointment details in session context (no database insertion)
                return {
                    "fulfillmentText": f"You have selected an appointment with Dr. {doctor_name} on {appointment_day}, {formatted_date} at {formatted_time}. Do you want to confirm this booking?",
                    "outputContexts": [
                        {
                            "name": f"{session_id}/contexts/awaiting_confirmation",
                            "lifespanCount": 5,
                            "parameters": {
                                "doctor_name": doctor_name,
                                "appointment_date": formatted_date,
                                "appointment_time": formatted_time,
                                "patient_name": patient_name,
                                "phone_number": phone_number
                            }
                        }
                    ]
                }

            except ValueError:
                cursor.close()
                db.close()
                return {
                    "fulfillmentText": "Invalid date or time format. Please provide a valid appointment date and time."}

        # Function to send email in a background thread
        def send_email_async(to_email, subject, content):
            thread = threading.Thread(target=send_email, args=(to_email, subject, content))
            thread.start()

        # Webhook function handling appointment confirmation
        if intent == "Confirmation_booking":
            # Fetch appointment details from context
            context = next((c for c in contexts if "awaiting_confirmation" in c.get("name", "")), None)
            if not context:
                return {"fulfillmentText": "No appointment details found. Please start over."}

            # Extract details
            doctor_name = context.get("parameters", {}).get("doctor_name")
            appointment_date = context.get("parameters", {}).get("appointment_date")
            appointment_time = context.get("parameters", {}).get("appointment_time")
            patient_name = parameters.get("patient_name")
            phone_number = context.get("parameters", {}).get("phone_number")

            # If patient_name is missing, get it from stored context
            if not patient_name:
                for ctx in contexts:
                    if "awaiting_patient_details" in ctx.get("name", ""):
                        patient_name = ctx.get("parameters", {}).get("patient_name")
                        break
            patient_email = parameters.get("email")

            if not patient_email:
                return {"fulfillmentText": "Please provide your email address for confirmation."}

                # Insert into MySQL Database
            db = get_db_connection()
            if not db:
                return {"fulfillmentText": "Database connection failed. Please try again later."}

            cursor = db.cursor()
            insert_query = """
                   INSERT INTO appointments (patient_name, phone_number, doctor_name, appointment_date, appointment_time, email)
                   VALUES (%s, %s, %s, %s, %s, %s)
               """
            cursor.execute(insert_query,
                           (patient_name, phone_number, doctor_name, appointment_date, appointment_time, patient_email))
            db.commit()
            cursor.close()
            db.close()

            # Prepare email content
            email_subject = "Appointment Confirmation"
            email_body = f"""
            Dear {patient_name},

            Your appointment with {doctor_name} has been confirmed.
            Date: {appointment_date}
            Time: {appointment_time}

            Thank you for choosing our Life Care hospital!
            """

            # Send email asynchronously
            send_email_async(patient_email, email_subject, email_body)

            # Return a quick response to Dialogflow
            return {
                "fulfillmentText": f"Your appointment with {doctor_name} on {appointment_date} at {appointment_time} has been confirmed. A confirmation email will be sent to {patient_email}. Thank you!"
            }
        if intent == "CancelAppointment":
            phone_number = parameters.get("phone_number")

            if not phone_number:
                return {"fulfillmentText": "Please provide your registered phone number to proceed with cancellation."}

            db = get_db_connection()
            if not db:
                return {"fulfillmentText": "Database connection failed."}

            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT doctor_name, appointment_date, appointment_time FROM appointments WHERE phone_number = %s",
                (phone_number,))
            appointments = cursor.fetchall()
            cursor.close()
            db.close()

            if not appointments:
                return {"fulfillmentText": "No appointments found for this phone number."}

            if len(appointments) > 1:
                appointment_list = "\n".join(
                    [f"{i + 1}. {a['doctor_name']} on {a['appointment_date']} at {a['appointment_time']}" for i, a in
                     enumerate(appointments)])
                return {
                    "fulfillmentText": f"You have multiple appointments. Please specify which one to cancel:\n{appointment_list}"}

            doctor_name = appointments[0]['doctor_name']
            appointment_date = appointments[0]['appointment_date']
            appointment_time = appointments[0]['appointment_time']

            return {
                "fulfillmentText": f"Are you sure you want to cancel your appointment with Dr. {doctor_name} on {appointment_date} at {appointment_time}? Reply with 'yes' to confirm or 'no' to keep it.",
                "outputContexts": [
                    {
                        "name": f"{session_id}/contexts/awaiting_cancellation_confirmation",
                        "lifespanCount": 5,
                        "parameters": {
                            "doctor_name": doctor_name,
                            "appointment_date": appointment_date,
                            "appointment_time": appointment_time,
                            "phone_number": phone_number
                        }
                    }
                ]
            }

            # Handle Confirmation_Cancellation Intent

        if intent == "Confirmation_Cancellation":
            context = next((c for c in contexts if "awaiting_cancellation_confirmation" in c.get("name", "")), None)
            if not context:
                return {"fulfillmentText": "No appointment details found. Please start over."}

            confirmation = parameters.get("confirmation")
            phone_number = context.get("parameters", {}).get("phone_number")
            doctor_name = context.get("parameters", {}).get("doctor_name")
            appointment_date = context.get("parameters", {}).get("appointment_date")
            appointment_time = context.get("parameters", {}).get("appointment_time")

            # **Fix: Retrieve email from context if not in parameters**
            patient_email = parameters.get("email") or context.get("parameters", {}).get("email")

            if confirmation is None:
                return {"fulfillmentText": "I didn't get a confirmation response. Please reply with 'yes' or 'no'."}

            if confirmation.lower() != "yes":
                return {"fulfillmentText": "Cancellation aborted. Your appointment remains booked."}

            # Connect to the database
            db = get_db_connection()
            if not db:
                return {"fulfillmentText": "Database connection failed. Please try again later."}

            cursor = db.cursor()
            delete_query = """
                DELETE FROM appointments WHERE phone_number = %s 
                AND doctor_name = %s AND appointment_date = %s AND appointment_time = %s
            """
            cursor.execute(delete_query, (phone_number, doctor_name, appointment_date, appointment_time))
            db.commit()
            cursor.close()
            db.close()

            # If email is missing, ask the user for it
            if not patient_email:
                return {
                    "fulfillmentText": "Your appointment has been canceled. Please provide your email if you need a cancellation confirmation."}

            # Prepare email content
            email_subject = "Appointment Cancellation Confirmation"
            email_body = f"""
            Dear Patient,

            Your appointment with Dr. {doctor_name} on {appointment_date} at {appointment_time} has been successfully canceled.

            If you wish to reschedule, please book a new appointment.

            Best Regards,  
            Life Care Hospital
            """

            # Send email asynchronously
            send_email_async(patient_email, email_subject, email_body)

            return {
                "fulfillmentText": f"Your appointment with Dr. {doctor_name} on {appointment_date} at {appointment_time} has been successfully canceled. A confirmation email has been sent to {patient_email}."
            }

        return {"fulfillmentText": "Intent not recognized."}
    except Exception as e:
        import traceback
        error_message = traceback.format_exc()  # Captures full error details
        print(f"Error occurred: {error_message}")  # Displays error details in logs
        return {"fulfillmentText": f"An unexpected error occurred: {str(e)}"}