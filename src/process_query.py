from ingest import ingest_from_query
from utils.clone import clone_repo
from utils.parse_query import parse_query
from typing import List
from fastapi.templating import Jinja2Templates
from fastapi import Request
from config import MAX_DISPLAY_SIZE, EXAMPLE_REPOS



templates = Jinja2Templates(directory="templates")


async def process_query(request: Request, input_text: str, slider_position: int, pattern_type: str = "exclude", pattern: str = "", is_index: bool = False) -> str:
    
    template = "index.jinja" if is_index else "github.jinja"
    try:
        query = parse_query(input_text, slider_position, pattern_type, pattern)
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
                "pattern_type": pattern_type,
                "pattern": pattern,
            }
        )
    
    if len(content) > MAX_DISPLAY_SIZE:
        content = f"(Files content cropped to {int(MAX_DISPLAY_SIZE/1000)}k characters, download full ingest to see more)\n" + content[:MAX_DISPLAY_SIZE]
        
    return templates.TemplateResponse(
        template, 
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
            "pattern_type": pattern_type,
            "pattern": pattern,
        }
    )
