import os
import json
from groq import Groq

SYSTEM_PROMPT = """You are a WhatsApp Template creation assistant.
Your goal is to gather requirements from the user and automatically build a valid WhatsApp template JSON.
Only ask 1-2 questions at a time if information is missing. Auto-fill what you can based on the user's prompt.

Meta WhatsApp Template Rules:
1. Variables must be positional like {{1}} or named like {{order_id}}.
2. Body must not end or start with a variable. Positional variables must start at {{1}} and be sequential.
3. Supported languages: hi, bn_IN, gu, kn, ml, mr, pa, ta, te, ur, en, en_IN, en_US, en_GB.
4. Categories: MARKETING, UTILITY, AUTHENTICATION.
5. Buttons: URL buttons max 2. QUICK_REPLY text max 25 chars.
6. A template can have an IMAGE, VIDEO, or DOCUMENT header. In that case, add an `example.header_handle` list.
7. Carousel templates have cards, no top-level buttons or footer.

You MUST respond strictly with a valid JSON object matching this schema:
{
  "ai_message": "Your conversational reply asking clarifying questions or confirming.",
  "template": {
    "name": "template_name",
    "category": "UTILITY",
    "language": "en",
    "components": [
       {"type": "BODY", "text": "...", "example": {"body_text": [["sample"]]}}
    ]
  }
}
"""

def generate_response(user_input, chat_history, current_template):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"ai_message": "GROQ_API_KEY missing.", "template": current_template}
        
    client = Groq(api_key=api_key)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    for msg in chat_history:
        if msg.get("role") in ["user", "assistant"]:
            messages.append({
                "role": msg["role"], 
                "content": msg.get("content", "")
            })
            
    prompt_text = f"User: {user_input}\n\nCurrent Template State:\n{json.dumps(current_template, indent=2)}"
    messages.append({"role": "user", "content": prompt_text})
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        return data
    except Exception as e:
        return {
            "ai_message": f"Error: {str(e)}",
            "template": current_template
        }
