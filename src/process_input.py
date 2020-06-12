from utils.gitclone import delete_repo, clone_repo
from utils.parse_url import id_from_repo_url
from ingest import analyze_codebase


async def process_input(text: str, digest_id: str) -> str:
    if not text.startswith("https://github.com/"):
        return "Invalid GitHub URL. Please provide a valid GitHub repository URL."
    
    
    delete_repo(digest_id)
    await clone_repo(text, digest_id)
        
    result = analyze_codebase(f"../tmp/{digest_id}", digest_id)

    txt_dump = result[1] + "\n" + result[2]
    with open(f"../tmp/{digest_id}.txt", "w") as f:
        f.write(txt_dump)


    delete_repo(digest_id)
    
    if not result:
        return "Repository processing failed or timed out after 30 seconds."
        
    return result
