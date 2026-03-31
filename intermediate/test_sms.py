import os
import requests
from dotenv import load_dotenv

load_dotenv()

FAST2SMS_API_KEY = os.environ.get('FAST2SMS_API_KEY')

# ✏️  CHANGE THIS to your own phone number (10 digits, no +91)
TEST_PHONE = input("Enter your phone number to receive the test SMS (10 digits): ").strip()

student_name = "Test Student"
message_body = (
    f"Hello! This is a test message from the KIET AI Student Quiz Portal. "
    f"Congratulations {student_name}! You are the winner of today's quiz. "
    f"Keep it up! - KIET Group, Kakinada"
)

print(f"\n📤 Sending SMS to: {TEST_PHONE}")
print(f"📝 Message: {message_body}\n")

url = "https://www.fast2sms.com/dev/bulkV2"
params = {
    "authorization": FAST2SMS_API_KEY,
    "message": message_body,
    "language": "english",
    "route": "q",
    "numbers": TEST_PHONE
}

try:
    response = requests.get(url, params=params, headers={"cache-control": "no-cache"})
    data = response.json()
    print("🔁 API Response:", data)
    
    if data.get("return") == True:
        print("\n✅ SUCCESS! SMS sent. Check your phone!")
    else:
        print("\n❌ FAILED. Reason:", data.get("message", data))
except Exception as e:
    print(f"\n❌ Error connecting to Fast2SMS: {e}")
