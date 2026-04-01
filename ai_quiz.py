import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HUGGINGFACE_API_KEY")

logging.basicConfig(level=logging.INFO)

_client = None


def get_client():
    """Lazily create and cache the Hugging Face InferenceClient."""
    global _client
    if _client is None:
        try:
            from huggingface_hub import InferenceClient
        except Exception as e:  # pragma: no cover
            logging.error(f"Failed to import huggingface_hub InferenceClient: {e}")
            raise

        if not HF_TOKEN:
            logging.warning("HUGGINGFACE_API_KEY not set; AI quiz will use fallback questions only.")

        _client = InferenceClient(model="HuggingFaceH4/zephyr-7b-beta", token=HF_TOKEN)
    return _client

def generate_daily_quiz() -> list:
    """
    Uses Hugging Face Inference API to generate 1 daily tricky logic/riddle question in a specific format.
    Returns a list of dictionaries with 'question' and 'answer_key' (no multiple choice options).
    """
    prompt = '''
    Generate EXACTLY 1 (one) TRICKY LOGIC PUZZLE or fun riddle.
    
    The value for the "question" field MUST strictly follow this exact template (including emojis and line breaks):
    
    Dear students, I have a question for you:
    
    [Insert the Tricky Riddle Here]
    
    🤔
    
    Important note
    No cheating 😜
    
    Constraint:
    1. Respond ONLY with a JSON array containing a single object.
    2. No preamble, no markdown, no explanation.
    3. The object must have keys: "id" (set to 1), "question" (the template above), and "answer_key".
    4. Ensure line breaks in the question are represented as \\n.
    '''
    
    try:
        client = get_client()
        messages = [{"role": "user", "content": prompt}]
        response = client.chat_completion(messages=messages, max_tokens=800)
        reply = response.choices[0].message.content.strip()
        
        # More robust JSON cleanup
        if "[" in reply and "]" in reply:
            reply = reply[reply.find("["):reply.rfind("]")+1]
        elif "{" in reply and "}" in reply:
            reply = "[" + reply[reply.find("{"):reply.rfind("}")+1] + "]"
        
        # FIX: AI often forgets to escape newlines in JSON strings.
        # We manually escape newlines that are NOT part of the JSON structure.
        # A simple way to do this for a single object/array is to replace all platform 
        # newlines with \n but keep the ones that actually separate JSON tokens.
        # However, a safer way is to just let json.loads handle it if we can pre-process bits.
        
        # Let's try to escape raw newlines inside the content
        processed_reply = ""
        in_string = False
        for char in reply:
            if char == '"':
                in_string = not in_string
                processed_reply += char
            elif char == '\n' and in_string:
                processed_reply += "\\n"
            elif char == '\r' and in_string:
                continue # Skip carriage returns
            else:
                processed_reply += char
        
        parsed_quiz = json.loads(processed_reply)
        return parsed_quiz

    except Exception as e:
        logging.error(f"Error generating AI Quiz: {e}")
        # Fallback Quiz perfectly formatted
        return [
            {
                "id": 1,
                "question": "Dear students, I have a question for you:\n\nIf you have three apples and you take away two, how many apples do you have? 🤔\n\nImportant note\nNo cheating 😜",
                "answer_key": "You have the two apples you took."
            }
        ]

def evaluate_winner(quiz_data: dict, attempts: list) -> int:
    """
    Takes the quiz question data and a list of attempt dictionaries: [{'id': 1, 'student_id': 5, 'answer_text': '...', 'time_taken': 120}, ...]
    Asks the Hugging Face model to determine the best valid answer. If multiple are correct, picks the fastest.
    Returns the student_id of the winner. Returns None if no valid answers.
    """
    if not attempts:
        return None
        
    prompt = f'''
    You are an adjudicator for a daily student logic contest.
    The official riddle asked was:
    "{quiz_data['question']}"
    
    The official answer key logic is: "{quiz_data['answer_key']}"
    
    Below is a list of attempts submitted by students. Return ONLY the ID of the student who provided a CORRECT (or logically sound) answer with the FASTEST time (lowest time_taken).
    If nobody got it correct, return "None".
    Only return the raw ID integer or "None". No other text.
    
    Submissions:
    '''
    
    for att in attempts:
        prompt += f"\n- Student ID: {att['student_id']}, Answer: '{att['answer_text']}', Time Taken: {att['time_taken']} seconds"
        
    try:
        client = get_client()
        messages = [{"role": "user", "content": prompt}]
        response = client.chat_completion(messages=messages, max_tokens=100)
        reply = response.choices[0].message.content.strip()
        
        # Extract digits only
        import re
        match = re.search(r'\d+', reply)
        if match:
            return int(match.group())
        else:
            return None
    except Exception as e:
        logging.error(f"AI Winner Evaluation Failed: {e}")
        # Fallback manual logic: Just pick the first non-empty response sorted by time
        sorted_attempts = sorted(attempts, key=lambda x: x['time_taken'])
        if sorted_attempts:
            return sorted_attempts[0]['student_id']
        return None

if __name__ == "__main__":
    q = generate_daily_quiz()
    print(json.dumps(q, indent=2))
