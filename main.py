import ast
import os
import re
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.notes_engine import build_notes_document, extract_english_title
from core.exam_engine import generate_exam_docx, generate_answer_key_docx

app = FastAPI(title="ExaNota API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ParseRequest(BaseModel):
    python_dict: str

def clean_input(text: str) -> str:
    return re.sub(r'```(?:python|json)?|```', '', text).strip()

@app.post("/api/parse-title")
async def parse_title(request: ParseRequest):
    try:
        data = ast.literal_eval(clean_input(request.python_dict))
        title = data.get("title", "Untitled")
        english_title = extract_english_title(title)
        return {"suggested_filename": english_title}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/generate")
async def generate(
    mode: str = Form(...), # "notes" or "exam"
    python_dict: str = Form(...),
    filename: str = Form(...),
    is_tamil: bool = Form(True),
    is_teacher_copy: bool = Form(False),
    template: UploadFile = File(None)
):
    try:
        data = ast.literal_eval(clean_input(python_dict))
        
        # Temp file for generation
        fd, tmp_path = tempfile.mkstemp(suffix=".docx")
        os.close(fd)
        
        template_path = None
        if template:
            os.makedirs("temp", exist_ok=True)
            template_path = os.path.join("temp", f"tpl_{template.filename}")
            with open(template_path, "wb") as f:
                f.write(await template.read())

        if mode == "notes":
            build_notes_document(data, tmp_path, template_path)
        elif mode == "exam":
            # For Exam, we might want to return both Exam and Answer Key as a ZIP?
            # But the user asked for "same" as notes, so maybe just the paper.
            # I'll return the Paper for now, or the Answer Key if teacher copy is selected?
            # Actually, let's return the Paper.
            exam_stream = generate_exam_docx(data, is_tamil, is_teacher_copy)
            with open(tmp_path, "wb") as f:
                f.write(exam_stream.getbuffer())
        else:
            raise HTTPException(status_code=400, detail="Invalid mode")

        # Cleanup template
        if template_path and os.path.exists(template_path):
            try: os.remove(template_path)
            except: pass

        clean_filename = re.sub(r'[^\w\s-]', '', filename).strip().replace(' ', '_')
        if not clean_filename.lower().endswith(".docx"):
            clean_filename += ".docx"

        return FileResponse(
            tmp_path,
            filename=clean_filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass
        raise HTTPException(status_code=500, detail=str(e))

# PWA & Static
@app.get("/manifest.json")
async def get_manifest():
    return FileResponse("static/manifest.json")

@app.get("/sw.js")
async def get_sw():
    return FileResponse("static/sw.js", media_type="application/javascript")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
