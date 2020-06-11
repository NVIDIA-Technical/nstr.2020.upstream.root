from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv
import asyncio
from api_analytics.fastapi import Analytics
from starlette.middleware.trustedhost import TrustedHostMiddleware
import functools
from ingest import analyze_codebase
from utils.decorators import async_timeout
from routers import download, dynamic, index


load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(Analytics, api_key=os.getenv('API_ANALYTICS_KEY'))
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["gitingest.com", "*.gitingest.com", "gitdigest.dev", "localhost"])
templates = Jinja2Templates(directory="templates")

    

@app.get("/api", response_class=HTMLResponse)
async def api_docs(request: Request):
    return templates.TemplateResponse(
        "api.html", {"request": request}
    )

@app.get('/favicon.ico')
async def favicon():
    return FileResponse('static/favicon.ico')



@async_timeout(10)
async def process_repo(repo_id: str):
    return analyze_codebase(f"../tmp/{repo_id}")

app.include_router(index)
app.include_router(download)
app.include_router(dynamic)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
