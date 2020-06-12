
from fastapi import HTTPException, APIRouter
from fastapi.responses import Response
from config import TMP_BASE_PATH

router = APIRouter()


@router.get("/download/{digest_id}")
async def download_ingest(digest_id: str):
    try:
        with open(f"{TMP_BASE_PATH}/{digest_id}.txt", "r") as f:
            content = f.read()
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={digest_id}.txt"
            }
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Digest not found")