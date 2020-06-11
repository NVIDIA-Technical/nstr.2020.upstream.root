from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uuid
from process_input import process_input
from config import MAX_DISPLAY_SIZE




router = APIRouter()
templates = Jinja2Templates(directory="templates")

EXAMPLE_REPOS = [
    {"name": "Gitingest", "url": "https://github.com/cyclotruc/gitingest"},
    {"name": "FastAPI", "url": "https://github.com/tiangolo/fastapi"},
    {"name": "Django", "url": "https://github.com/django/django"},
    {"name": "Flask", "url": "https://github.com/pallets/flask"},
    {"name": "Linux", "url": "https://github.com/torvalds/linux"},
    {"name": "Tldraw", "url": "https://github.com/tldraw/tldraw"},
]

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "examples": EXAMPLE_REPOS
        }
    )


@router.post("/", response_class=HTMLResponse)
async def index_post(request: Request, input_text: str = Form(...)):
    try:
        summary, tree, content = await process_input(input_text)
    except Exception as e:
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "error_message": str(e),
                "examples": EXAMPLE_REPOS
            }
        )
    
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
            "examples": EXAMPLE_REPOS,
            "error_message": None,
            "ingest_id": ingest_id
        }
    )

