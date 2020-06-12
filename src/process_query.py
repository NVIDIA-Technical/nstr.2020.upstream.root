from utils.clone import clone_repo, delete_repo
from ingest import ingest_from_query


async def process_query(query: dict) -> str:
    
    await clone_repo(query)

    result = ingest_from_query(query)
    txt_dump = result[1] + "\n" + result[2]
    with open(f"{query['local_path']}.txt", "w") as f:
        f.write(txt_dump)
        
    delete_repo(query['slug'])
        
    return result
