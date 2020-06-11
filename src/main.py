from fastapi import FastAPI, Request, Form, Response, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import uuid
import os
from dotenv import load_dotenv
import asyncio
from api_analytics.fastapi import Analytics
from starlette.middleware.trustedhost import TrustedHostMiddleware
import functools
from typing import TypeVar, Callable, Any
from ingest import analyze_codebase

MAX_DISPLAY_SIZE = 1000000

T = TypeVar("T")
def async_timeout(seconds: int = 10):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                return None
        return wrapper
    return decorator

# Load environment variables
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# https://www.apianalytics.dev/dashboard/6633361d116e473a981333ec0a375f59
app.add_middleware(Analytics, api_key=os.getenv('API_ANALYTICS_KEY'))
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["gitdigest.dev", "*.gitdigest.dev", "localhost"])
templates = Jinja2Templates(directory="templates")

with open("templates/index.html", "r") as f:
    html = f.read()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "result": None, "summary": "", "tree": "", "content": ""}
    )


@app.post("/", response_class=HTMLResponse)
async def process_input(request: Request, input_text: str = Form(...)):
    try:
        summary, tree, content = await process_input(input_text)
    except Exception as e:
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request, 
                "result": None, 
                "summary": "", 
                "tree": "", 
                "content": "",
                "error_message": f"Error processing repository: {e}"
            }
        )
    
    # Store the full content in session or temporary file
    digest_id = str(uuid.uuid4())
    with open(f"../tmp/digest-{digest_id}.txt", "w") as f:
        f.write(f"Summary:\n{summary}\n\nFile Tree:\n{tree}\n\nDetailed Content:\n{content}")
    
    if len(content) > MAX_DISPLAY_SIZE:
        content = f"(Files content cropped to {MAX_DISPLAY_SIZE/1000000}M characters, download full digest to see more)\n" + content[:MAX_DISPLAY_SIZE]
        
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "summary": summary,
            "result": True, 
            "tree": tree, 
            "content": content,
            "error_message": None,
            "digest_id": digest_id
        }
    )

# Add new endpoint for downloading
@app.get("/download/{digest_id}")
async def download_digest(digest_id: str):
    try:
        with open(f"../tmp/digest-{digest_id}.txt", "r") as f:
            content = f.read()
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=gitdigest-{digest_id[:8]}.txt"
            }
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Digest not found")

def sanitize_git_url(url: str) -> str:
    if not url.startswith("https://github.com/"):
        raise ValueError("Invalid GitHub URL. Please provide a valid GitHub repository URL.")
    return url.split(" ")[0]


    


@async_timeout(10)
async def clone_repo(repo_url: str) -> str:

    repo_url = sanitize_git_url(repo_url)
    if not repo_url:
        return None
    
    id = repo_url.replace("https://github.com/", "").replace("/", "-")
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth=1",
            repo_url,
            f"../tmp/{id}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            return None
            
        return id
    except Exception as e:
        return f"Error cloning repository: {str(e)}"

@async_timeout(15)  # Longer timeout for processing
async def process_repo(
    repo_id: str,
):
    return analyze_codebase(f"../tmp/{repo_id}")

def delete_repo(repo_id: str):

    os.system(f"rm -drf ../tmp/{repo_id}")
    os.system(f"rm -f ../tmp/digest-{repo_id}")

async def process_input(text: str) -> str:
    if not text.startswith("https://github.com/"):
        return "Invalid GitHub URL. Please provide a valid GitHub repository URL."
        
    repo_id = await clone_repo(text)
    if not repo_id:
        return "Repository clone failed or timed out after 10 seconds."
        
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
