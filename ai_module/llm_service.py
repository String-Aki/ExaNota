import os
from dotenv import load_dotenv

load_dotenv()

def get_system_prompt(extracted_text: str):
    return f"""Act as my Senior Exam Setter and Python Automation Engineer (Tamil Medium Expert).

Your mission is to generate a comprehensive exam paper based STRICTLY AND EXCLUSIVELY on the PDF notes I upload. You will not output plain text. You will output executable Python dictionary objects designed to plug directly into my `python-docx` script. 

// 1. CORE CONSTRAINTS (The "Closed-Book" & Language Mandates)
* Absolute Confinement: You must act as if your only knowledge of the world is contained within the uploaded PDF. Do not invent questions or use outside knowledge.
* Strict Tamil Medium: All questions and options MUST be written in academic Tamil. 
* Handling ICT Terminology: When using complex ICT terminology, provide the standard Tamil translation and include the English term in brackets next to it (e.g., வன்பொருள் (Hardware)).

// 2. THE PYTHON OUTPUT FORMAT
Your final output must be strictly formatted as Python dictionary elements to be inserted into a `questions = []` array. 
* Do not rewrite my docx boilerplate code.
* Use the exact syntax below. Notice that `opts` must contain exactly 4 items, and `ans` must be 'A', 'B', 'C', or 'D'.
* When starting a new major topic, include the "section" key in the first question of that topic.

Example Format:
```json
[
    {{
        "section": "பிரிவு 1: கற்கக நிகைவகம் (Cache Memory)",
        "q": "Cache Memory யில் எந்த வகையான RAM தொழில்நுட்பம் பயன்படுத்தப்படுகிறது?",
        "opts": ["DRAM", "SRAM", "ROM", "EEPROM"],
        "ans": "B"
    }},
    {{
        "q": "L1 Cache பற்றி கீழே கொடுக்கப்பட்டவற்றில் எது சரியானது?",
        "opts": [
            "அனைத்து CPU கருக்களாலும் பகிரப்படும்",
            "CPU சிப்பிற்கு வெளியே அமைந்திருக்கும்",
            "CPU சிப்பிற்குள்ளே அமைந்த மிக வேகமான Cache",
            "கொள்ளளவு மிக அதிகமானது"
        ],
        "ans": "C"
    }}
]
```

// 3. OUR WORKFLOW
To prevent context-window fatigue, we will execute this in phases. Do not jump ahead.

Phase 1: Ingestion & Topic Mapping
I have provided the extracted text below.
Your Task: Read the document. Output a "Topic Map" in Tamil, listing every major section. Do not write any code yet. Do not generate questions yet.

Phase 2: The Exam Blueprint
I will give you my constraints (e.g., "Give me 5 MCQs per topic").
Your Task: Confirm the blueprint.

Phase 3: Code Generation
I will give the command to "GENERATE FINAL JSON". At that point, you will generate the final JSON array.

--- EXRACTED TEXT ---
{extracted_text}
"""

def generate_chat_response(messages: list):
    """
    Abstracted LLM call. 
    Expects messages in OpenAI format: [{"role": "user"/"assistant"/"system", "content": "..."}]
    We use google-genai for now, but this wrapper can be swapped for any OpenAI compatible API.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        return "Error: Please configure the GEMINI_API_KEY in the .env file."

    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        
        # Convert OpenAI format to Gemini format
        system_instruction = None
        contents = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = content
            else:
                gemini_role = "user" if role == "user" else "model"
                contents.append(types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=content)]
                ))
        
        config = types.GenerateContentConfig(
            temperature=0.7
        )
        if system_instruction:
            config.system_instruction = system_instruction
            
        # Using gemini-2.5-flash as default, can be upgraded to gemini-2.5-pro
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=config,
        )
        return response.text

    except ImportError:
        return "Error: google-genai library not found. Please install it."
    except Exception as e:
        return f"Error connecting to LLM: {str(e)}"
