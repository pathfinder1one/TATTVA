from pathlib import Path

from fastapi import HTTPException

from app.config import Settings


def write_text_version(settings: Settings, document_id: str, index_version: str, text: str) -> str:
    root = Path(settings.file_storage_root).resolve()
    relative = Path("extracted") / document_id / f"{index_version}.txt"
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Invalid extracted text storage path.")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".txt.tmp")
    temporary.write_text(text, encoding="utf-8", newline="")
    temporary.replace(target)
    return relative.as_posix()


def read_text_version(settings: Settings, storage_key: str) -> str:
    root = Path(settings.file_storage_root).resolve()
    target = (root / Path(storage_key)).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(status_code=404, detail="Stored source text is unavailable.")
    return target.read_text(encoding="utf-8")
