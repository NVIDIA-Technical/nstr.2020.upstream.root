from utils.gitclone import clone_repo, delete_repo
from ingest import ingest_from_path
from config import TMP_BASE_PATH


async def process_query(query: dict) -> str:
    print(query)
    await clone_repo(query['url'], query['id'])
        
    result = ingest_from_path(query, query['id'])

    txt_dump = result[1] + "\n" + result[2]
    with open(f"{TMP_BASE_PATH}/{query['id']}.txt", "w") as f:
        f.write(txt_dump)

    delete_repo(query['id'])
        
    return result
