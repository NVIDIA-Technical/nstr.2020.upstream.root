from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uuid
from process_input import process_input
from config import MAX_DISPLAY_SIZE




def error_response(request: Request, error_message: str):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "error_message": error_message
        }
    )



router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", {
            "request": request, 
            "result": None, 
        }
    )


@router.post("/", response_class=HTMLResponse)
async def index_post(request: Request, input_text: str = Form(...)):
    try:
        summary, tree, content = await process_input(input_text)
    except Exception as e:
        return error_response(request, f"Error processing repository: {e}")
    
    ingest_id = str(uuid.uuid4())
    with open(f"../tmp/ingest-{ingest_id}.txt", "w") as f:
        f.write(f"Summary:\n{summary}\n\nFile Tree:\n{tree}\n\nDetailed Content:\n{content}")
    
    if len(content) > MAX_DISPLAY_SIZE:
        content = f"(Files content cropped to {int(MAX_DISPLAY_SIZE/1000)}k characters, download full ingest to see more)\n" + content[:MAX_DISPLAY_SIZE]
        
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "summary": summary,
            "result": True, 
            "tree": tree, 
            "content": content,
            "error_message": None,
            "ingest_id": ingest_id
        }
    )

