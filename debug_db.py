import sqlite3
import datetime

conn = sqlite3.connect('quiz_app.db')
cursor = conn.cursor()

today = datetime.date.today().isoformat()
print(f"Today is: {today}")

cursor.execute("SELECT date, questions_json FROM quizzes")
rows = cursor.fetchall()
for row in rows:
    print(f"Quiz Date: {row[0]}")
    # print(f"Content: {row[1][:100]}...")

# Delete today's quiz so it can be regenerated
cursor.execute("DELETE FROM quizzes WHERE date = ?", (today,))
conn.commit()
print(f"Deleted quiz for {today} if it existed.")

conn.close()
