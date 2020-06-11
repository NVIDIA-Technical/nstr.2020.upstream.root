from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uuid
from process_input import process_input
from config import MAX_DISPLAY_SIZE


router = APIRouter()
templates = Jinja2Templates(directory="templates")




def error_response(request: Request, error_message: str):
    return templates.TemplateResponse(
        "github.html", 
        {
            "request": request,
            "error_message": error_message
        }
    )


def reconstruct_github_url(full_path: str) -> str:
    path_parts = full_path.split('/')
    
    
    # Reconstruct the GitHub URL
    github_url = f"https://github.com/{path_parts[0]}/{path_parts[1]}"
    return github_url




@router.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    try:
        github_url = reconstruct_github_url(full_path)
    except Exception as e:
        return templates.TemplateResponse(
            "github.html", 
            {
                "request": request, 
                "result": False, 
                "loading": False,
                "github_url": full_path,
                "error_message": f"Error processing repository {e}"
            }
        )
    
    return templates.TemplateResponse(
        "github.html",
        {
            "request": request,
            "result": False,
            "loading": True,
            "github_url": github_url,
        }
    )

@router.post("/{full_path:path}", response_class=HTMLResponse)
async def process_github_path(request: Request, full_path: str, input_text: str = Form(...)):
    try:
        summary, tree, content = await process_input(input_text)
    except Exception as e:
        return templates.TemplateResponse(
            "github.html", 
            {
                "request": request, 
                "result": False, 
                "loading": False,
                "github_url": input_text,
                "error_message": f"Error processing repository {e}"
            }
        )
    
    ingest_id = str(uuid.uuid4())
    with open(f"../tmp/ingest-{ingest_id}.txt", "w") as f:
        f.write(f"Summary:\n{summary}\n\nFile Tree:\n{tree}\n\nDetailed Content:\n{content}")
    
    if len(content) > MAX_DISPLAY_SIZE:
        content = f"(Files content cropped to {int(MAX_DISPLAY_SIZE/1000)}k characters, download full digest to see more)\n" + content[:MAX_DISPLAY_SIZE]
        
    return templates.TemplateResponse(
        "github.html", 
        {
            "request": request, 
            "summary": summary,
            "result": True, 
            "loading": False,
            "tree": tree, 
            "content": content,
            "github_url": input_text,
            "error_message": None,
            "ingest_id": ingest_id
        }
    )