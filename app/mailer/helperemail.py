import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from PIL import Image
from io import BytesIO

def send_workviser_task_email(employee_email, employee_name, employee_id, task_summary, decoded_images, task_id):
    body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>WorkViser Task Assignment</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          background-color: #f4f6f9;
          margin: 0;
          padding: 0;
        }}
        .container {{
          width: 80%;
          margin: 40px auto;
          background-color: #ffffff;
          border-radius: 10px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
          padding: 20px;
          border: 5px solid;
          border-image-slice: 1;
          border-image-source: linear-gradient(45deg, #007bff, #17a2b8);
        }}
        .header {{
          background-color: #007bff;
          color: #ffffff;
          text-align: center;
          padding: 20px;
          border-radius: 10px 10px 0 0;
        }}
        .header h1 {{
          margin: 0;
        }}
        .content {{
          padding: 30px;
          font-size: 16px;
          line-height: 1.6;
        }}
        .highlight {{
          color: #007bff;
          font-weight: bold;
        }}
        .footer {{
          background-color: #343a40;
          color: #ffffff;
          text-align: center;
          padding: 15px;
          border-radius: 0 0 10px 10px;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>📌 New Helping Task Assigned via WorkViser</h1>
        </div>
        <div class="content">
          <p>Dear <strong>{employee_name}</strong> (Employee ID: <strong>{employee_id}</strong>),</p>
          <p>
            You’ve been assigned a <span class="highlight">new helping task</span> through <strong>WorkViser</strong>. Please find the task summary and screenshots attached below.
          </p>
          <p><strong>📝 Task Summary:</strong><br>{task_summary}</p>
          <p>
            If you need assistance or clarification, feel free to reach out to your supervisor.
          </p>
          <p>Thank you for your commitment!<br><strong>WorkViser Team</strong></p>
        </div>
        <div class="footer">
          <p>© WorkViser | Empowering Remote Teams</p>
        </div>
      </div>
    </body>
    </html>
    """

    sender_email = 'adroituniversal@gmail.com'
    app_password = 'cslp clhh rtci ecbw'

    # Create Email Message
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = employee_email
    message['Subject'] = f"📢 New WorkViser Helping Task Assigned to You"

    # Attach HTML body
    message.attach(MIMEText(body, 'html'))

    # Attach Images
    for index, image in enumerate(decoded_images):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_data = buffered.getvalue()
        img_part = MIMEImage(img_data, name=f"screenshot_{task_id}_{index}.png")
        message.attach(img_part)

    # Send Email
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, app_password)
    server.send_message(message)
    server.quit()
