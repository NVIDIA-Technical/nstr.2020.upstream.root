from fastapi import FastAPI, Request, Form, Response, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import uuid
import os
from dotenv import load_dotenv
import asyncio
from api_analytics.fastapi import Analytics
from starlette.middleware.trustedhost import TrustedHostMiddleware
import functools
from ingest import analyze_codebase
from utils.decorators import async_timeout
from utils.clone import get_repo_id, clone_repo, delete_repo

MAX_DISPLAY_SIZE = 300000

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(Analytics, api_key=os.getenv('API_ANALYTICS_KEY'))
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["gitingest.com", "*.gitingest.com", "gitdigest.dev", "localhost"])
templates = Jinja2Templates(directory="templates")


def error_response(request: Request, error_message: str):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "error_message": error_message
        }
    )


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", {
            "request": request, 
            "result": None, 
            "summary": "", 
            "tree": "", 
            "content": "",
        }
    )


@app.post("/", response_class=HTMLResponse)
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

@app.get("/download/{ingest_id}")
async def download_ingest(ingest_id: str):
    try:
        with open(f"../tmp/ingest-{ingest_id}.txt", "r") as f:
            content = f.read()
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=gitingest-{ingest_id[:8]}.txt"
            }
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Digest not found")

    
async def process_input(text: str) -> str:
    if not text.startswith("https://github.com/"):
        return "Invalid GitHub URL. Please provide a valid GitHub repository URL."
    
    repo_id = get_repo_id(text)
    if not repo_id:
        return "Invalid GitHub URL. Please provide a valid GitHub repository URL."
    
    delete_repo(repo_id)
    await clone_repo(text, repo_id)
        
    result = await process_repo(repo_id)
    delete_repo(repo_id)
    
    if not result:
        return "Repository processing failed or timed out after 30 seconds."
        
    return result


    

@app.get("/api", response_class=HTMLResponse)
async def api_docs(request: Request):
    return templates.TemplateResponse(
        "api.html", {"request": request}
    )

@app.get('/favicon.ico')
async def favicon():
    return FileResponse('static/favicon.ico')



def reconstruct_github_url(full_path: str) -> str:
    path_parts = full_path.split('/')
    
    
    # Reconstruct the GitHub URL
    github_url = f"https://github.com/{path_parts[0]}/{path_parts[1]}"
    return github_url

@app.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    try:
        github_url = reconstruct_github_url(full_path)
    except Exception as e:
        return templates.TemplateResponse(
            "github.html", 
            {
                "request": request, 
                "result": False, 
                "github_url": full_path,
                "summary": "", 
                "tree": "", 
                "content": "",
                "error_message": f"Error processing repository {e}"
            }
        )
    
    # Return the template with loading state
    return templates.TemplateResponse(
        "github.html",
        {
            "request": request,
            "result": False,
            "github_url": github_url,
        }
    )

@app.post("/{full_path:path}", response_class=HTMLResponse)
async def process_github_path(request: Request, full_path: str, input_text: str = Form(...)):
    try:
        summary, tree, content = await process_input(input_text)
    except Exception as e:
        return templates.TemplateResponse(
            "github.html", 
            {
                "request": request, 
                "result": False, 
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
            "tree": tree, 
            "content": content,
            "github_url": input_text,
            "error_message": None,
            "ingest_id": ingest_id
        }
    )

@async_timeout(10)
async def process_repo(repo_id: str):
    return analyze_codebase(f"../tmp/{repo_id}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
