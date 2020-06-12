from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.parse_url import id_from_repo_url
from process_input import process_input
from config import MAX_DISPLAY_SIZE




router = APIRouter()
templates = Jinja2Templates(directory="templates")

EXAMPLE_REPOS = [
    {"name": "Gitingest", "url": "https://github.com/cyclotruc/gitingest"},
    {"name": "FastAPI", "url": "https://github.com/tiangolo/fastapi"},
    {"name": "Ollama", "url": "https://github.com/ollama/ollama"},
    {"name": "Flask", "url": "https://github.com/pallets/flask"},
    {"name": "Tldraw", "url": "https://github.com/tldraw/tldraw"},
    {"name": "Linux", "url": "https://github.com/torvalds/linux"},
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
    ingest_id = id_from_repo_url(input_text)

    try:
        summary, tree, content = await process_input(input_text, ingest_id)
    except Exception as e:
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "error_message": str(e),
                "examples": EXAMPLE_REPOS
            }
        )
    
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

