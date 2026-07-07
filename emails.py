import os
import smtplib
from dotenv import load_dotenv
from email.message import EmailMessage


class EmailSender:
    load_dotenv()
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM", smtp_user)
    #print(smtp_host, smtp_port, smtp_user, smtp_password, from_email)
    

    def send_team_registration_email(to_email: str, team_id: str, team_name: str, division: str):
        if not all([EmailSender.smtp_host, EmailSender.smtp_user, EmailSender.smtp_password, EmailSender.from_email]):
            return False

        message = EmailMessage()
        message["Subject"] = "You have successfully joined a team"
        message["From"] = EmailSender.from_email
        message["To"] = to_email
        message.set_content(
            f"Hello,\n\n"
            f"You have successfully joined team {team_name} ({team_id}).\n"
            f"Division: {division}\n\n"
            f"Please contact your team captain if you have any further questions. Their contact email is listed in the team information page.\n"
            f"Happy running!\n\n\n"
            f"This is an automated email. Please do not reply to this email. Contact vancouverrun@gmail.com for support."
        )

        try:
            with smtplib.SMTP(EmailSender.smtp_host, EmailSender.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(EmailSender.smtp_user, EmailSender.smtp_password)
                smtp.send_message(message)
            return True
        except Exception as e:
            print(e)
            return False
        
    
    def send_team_registration_email_captain(to_email: str, team_id: str, team_name: str, user_email: str):
        if not all([EmailSender.smtp_host, EmailSender.smtp_user, EmailSender.smtp_password, EmailSender.from_email]):
            return False

        message = EmailMessage()
        message["Subject"] = "Someone joined your team!"
        message["From"] = EmailSender.from_email
        message["To"] = to_email
        message.set_content(
            f"Hello,\n\n"
            f"A runner {user_email} joined your team {team_name} ({team_id}).\n"
            f"If you don't recognize them, you can remove them by going to the home page, 'Manage my Teams', select your team, and removing them from the members list. Also be sure to change your team token by clicking 'Regenerate Team Token'.\n"
            f"Thank you.\n\n\n"
            f"This is an automated email. Please do not reply to this email. Contact vancouverrun@gmail.com for support."
        )

        try:
            with smtplib.SMTP(EmailSender.smtp_host, EmailSender.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(EmailSender.smtp_user, EmailSender.smtp_password)
                smtp.send_message(message)
            return True
        except Exception as e:
            print(e)
            return False
        
    
    def send_team_payment_email(to_email: str, team_id: str, transaction_ids: list[str]):
        if not all([EmailSender.smtp_host, EmailSender.smtp_user, EmailSender.smtp_password, EmailSender.from_email]):
            return False
        
        message = EmailMessage()
        message["Subject"] = "Your team payment has been completed"
        message["From"] = EmailSender.from_email
        message["To"] = to_email
        message.set_content(
            f"Hello,\n\n"
            f"We successfully received payment for your team with ID {team_id}.\n"
            f"Your transaction ID(s) are: {'\n'.join(transaction_ids)}\n\n"
            f"If you have any questions, please contact support at vancouverrun@gmail.com with the transaction ID(s).\n\n"
            f"Thank you for participating!\n\n\n"
            f"This is an automated email. Please DO NOT reply to this email."
        )

        try:
            with smtplib.SMTP(EmailSender.smtp_host, EmailSender.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(EmailSender.smtp_user, EmailSender.smtp_password)
                smtp.send_message(message)
            return True
        except Exception as e:
            print(e)
            return False
