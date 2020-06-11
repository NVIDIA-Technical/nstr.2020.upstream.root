from fastapi import FastAPI, Request, Form
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
        "index.html", {"request": request, "result": None, "summary": "", "structure": "", "content": ""}
    )


@app.post("/", response_class=HTMLResponse)
async def process_input(request: Request, input_text: str = Form(...)):
    result = await process_input(input_text)
    
    # Check if result is an error message
    if not result:
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request, 
                "result": None, 
                "summary": "", 
                "structure": "", 
                "content": "",
                "error_message": "Repository can't be cloned"
            }
        )
    
    summary = extract_summary(result)
    structure = extract_structure(result)
    content = extract_content(result)

    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "result": result, 
            "summary": summary, 
            "structure": structure, 
            "content": content,
            "error_message": None
        }
    )

def sanitize_git_url(url: str) -> str:
    if not url.startswith("https://github.com/"):
        return None
    
    trimmed = url.split(" ")[0]
    return trimmed


    


@async_timeout(10)
async def clone_repo(repo_url: str) -> str:

    repo_url = sanitize_git_url(repo_url)
    if not repo_url:
        return None
    
    id = str(uuid.uuid4())
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
    max_depth: int = None,
    output_format: str = "text",
    show_size: bool = False,
    show_ignored: bool = False,
    ignore_patterns: list = None,
    no_content: bool = False,
    max_size: int = 10000000,
) -> str:
    cmd = f"cdigest ../tmp/{repo_id} -f ../tmp/digest-{repo_id} --copy-to-clipboard"

    if max_depth is not None:
        cmd += f" -d {max_depth}"
    if output_format:
        cmd += f" -o {output_format}"
    if show_size:
        cmd += " --show-size"
    if show_ignored:
        cmd += " --show-ignored"
    if ignore_patterns:
        patterns = " ".join(ignore_patterns)
        cmd += f" --ignore {patterns}"
    if no_content:
        cmd += " --no-content"
    if max_size != 10240:
        cmd += f" --max-size {max_size}"

    proc = await asyncio.create_subprocess_exec(
        *cmd.split(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    stdout, stderr = await proc.communicate()
    
    if proc.returncode != 0:
        return None

    try:
        with open(f"../tmp/digest-{repo_id}", "r") as f:
            content = f.read()
    except Exception as e:
        return "Error processing repo"
    
    idx = content.find("Directory Structure:")
    
    if idx == -1:
        return "Error processing repo"
    
    return content[idx:]

def delete_repo(repo_id: str):

    os.system(f"rm -drf ../tmp/{repo_id}")
    os.system(f"rm -f ../tmp/digest-{repo_id}")

def extract_summary(content: str) -> str:
    summary = ""
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('Total files analyzed:'):
            summary += line.replace("Total files analyzed:", "Files analyzed:") + "\n"
        elif line.startswith('Total directories analyzed:'):
            summary +=  line.replace("Total directories analyzed:", "Directories analyzed:") + "\n"
        elif line.startswith('Total tokens:'):
            summary +=  line + "\n"
        elif line.startswith('Actual text content size:'):
            summary +=  line + "\n"
            
    return summary

def extract_structure(content: str) -> str:
    return content[:content.find("Summary:")]

def extract_content(content: str) -> str:
    if not "File Contents:" in content:
        return content
    
    content = content[content.find("File Contents:") + len("File Contents:") + 2:]
    
    if len(content) > 500000:
        return "(cropped to 500k characters)\n" + content[:500000]
    return content

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
