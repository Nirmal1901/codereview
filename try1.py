from fastapi import FastAPI, HTTPException, Body
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart  
import smtplib
import traceback

app = FastAPI()

@app.post("/send_mail")
async def send_mail(to: str = Body(...), subject: str = Body(...), body: str = Body(...)):
    try:
        smtp_server = "smtp.office365.com"
        port = 587
        sender_email = "nirmalnathani01@outlook.com"
        password = "qxiavnfzdwkrowus"

        message = MIMEMultipart()
        message["From"] = '"Nirmal" <nirmalnathani01@outlook.com>'
        message["To"] = to
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, to, message.as_string())

        result = {
            "status": "Mail sent successfully"
        }

        return result

    except Exception as e:
        import logging
        logging.error(f"Failed to send mail: {e}")
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to send mail: {str(e)}")
