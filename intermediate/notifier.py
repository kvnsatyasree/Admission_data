import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header

logging.basicConfig(level=logging.INFO)

# --- Config ---
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT   = int(os.environ.get('SMTP_PORT', 587))
EMAIL_USER  = os.environ.get('EMAIL_USER', '')
EMAIL_PASS  = os.environ.get('EMAIL_PASS', '')
EMAIL_FROM  = os.environ.get('EMAIL_FROM', 'KIET AI Quiz Hub')


def send_winner_email(recipient_email, student_name, time_taken=None, answer_text=None):
    """
    Sends a congratulatory email to the winning student.
    """
    if not recipient_email or not EMAIL_USER or not EMAIL_PASS:
        logging.warning("Email config missing/incomplete — skipping email.")
        return False

    performance_msg = f"You completed the logic riddle in {time_taken} seconds!" if time_taken else ""
    answer_msg = f"Your winning answer: \"{answer_text}\"" if answer_text else ""

    subject = "🏆 Congratulations! You won the Daily AI Logic Riddle!"
    body = (
        f"Hello {student_name}!\n\n"
        f"Congratulations! Our AI Adjudicator has selected you as the winner of today's "
        f"KIET AI Quiz Hub challenge. 🎉\n\n"
        f"{performance_msg}\n"
        f"{answer_msg}\n\n"
        f"Your logic was spot on and your performance was outstanding. Please visit the "
        f"college admin office to claim your recognition and certificate.\n\n"
        f"Best Regards,\n"
        f"KIET Group of Institutions\n"
        f"http://kiet.edu.in"
    )

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = EMAIL_FROM
    msg['To'] = recipient_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, [recipient_email], msg.as_string())
        server.quit()
        logging.info(f"Winner email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logging.error(f"Email delivery failed: {e}")
        return False


def send_participation_email(recipient_email, student_name):
    """
    Sends a thank you email to student after they submit the quiz.
    """
    if not recipient_email or not EMAIL_USER or not EMAIL_PASS:
        return False

    subject = "Thank you for participating in the KIET AI Quiz!"
    body = (
        f"Hello {student_name},\n\n"
        f"Thank you for submitting your answer to today's KIET AI Quiz Hub logic riddle. "
        f"Your response has been successfully recorded.\n\n"
        f"Our AI Adjudicator will evaluate all submissions and announce the winner at 10 PM tonight.\n\n"
        f"Best of luck!\n"
        f"KIET Group of Institutions\n"
        f"http://kiet.edu.in"
    )

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = EMAIL_FROM
    msg['To'] = recipient_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, [recipient_email], msg.as_string())
        server.quit()
        logging.info(f"Participation email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logging.error(f"Participation email delivery failed: {e}")
        return False


def send_winner_notification(student_name, student_email, time_taken=None, answer_text=None):
    """
    Sends the Email notification to the Student.
    """
    return send_winner_email(student_email, student_name, time_taken, answer_text)


if __name__ == "__main__":
    print("Email Notifier module loaded")

