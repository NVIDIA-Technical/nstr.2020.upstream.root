from ingest import ingest_from_query
from utils.clone import clone_repo
from utils.parse_url import parse_url
from utils.log_convert import logSliderToSize
from fastapi.templating import Jinja2Templates
from fastapi import Request
from config import MAX_DISPLAY_SIZE, EXAMPLE_REPOS



templates = Jinja2Templates(directory="templates")

async def process_query(request: Request, input_text: str, max_file_size: int, is_index: bool) -> str:


    template = "index.jinja.html" if is_index else "github.jinja.html"
    slider_position = max_file_size
    size_in_kb = logSliderToSize(max_file_size)
    
    try:
        query = parse_url(input_text)
        query["max_file_size"] = int(size_in_kb) * 1024
        await clone_repo(query)
        summary, tree, content = ingest_from_query(query)
        with open(f"{query['local_path']}.txt", "w") as f:
            f.write(tree + "\n" + content)
    except Exception as e:
        return templates.TemplateResponse(
            template, 
            {
                "request": request,
                "github_url": input_text,
                "error_message": f"Error: {e}",
                "examples": EXAMPLE_REPOS if is_index else [],
                "default_file_size": slider_position,
            }
        )
    
    if len(content) > MAX_DISPLAY_SIZE:
        content = f"(Files content cropped to {int(MAX_DISPLAY_SIZE/1000)}k characters, download full ingest to see more)\n" + content[:MAX_DISPLAY_SIZE]
        
    return templates.TemplateResponse(
        "index.jinja.html", 
        {
            "request": request, 
            "github_url": input_text,
            "result": True, 
            "summary": summary,
            "tree": tree, 
            "content": content,
            "examples": EXAMPLE_REPOS if is_index else [],
            "ingest_id": query['id'],
            "default_file_size": slider_position,  
        }
    )
