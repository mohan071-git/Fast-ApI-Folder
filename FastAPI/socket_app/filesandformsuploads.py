from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.responses import StreamingResponse
import io

from forms.database import SessionaLocal, engine
from forms import models
from forms.auth import router as auth_router, get_current_user

# ---------- APP ----------
app = FastAPI()
app.include_router(auth_router)

models.Base.metadata.create_all(bind=engine)

# ---------- DB DEP ----------
def get_db():
    db = SessionaLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# ---------- UPLOAD ----------
@app.post("/forms/upload")
async def upload_file(
    title: str,
    file: UploadFile = File(...),
    
    current_user: dict = Depends(get_current_user)
):
    file_bytes = await file.read()

    form = models.Form(
        title=title,
        file_name=file.filename,
        file_type=file.content_type,
        file_data=file_bytes,
        user_id=current_user["id"]
    )

    db.add(form)
    db.commit()
    db.refresh(form)

    return {"message": "File uploaded", "form_id": form.id}


# ---------- GET USER FILES ----------
@app.get("/users/{user_id}/files")
def get_user_files(
    user_id: int,
    db: db_dependency,
    current_user: dict = Depends(get_current_user)
):
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    files = db.query(models.Form).filter(
        models.Form.user_id == user_id
    ).all()

    return files


# ---------- DOWNLOAD ----------
@app.get("/forms/{form_id}/download")
def download_file(
    form_id: int,
    db: db_dependency,
    current_user: dict = Depends(get_current_user)
):
    form = db.query(models.Form).filter(
        models.Form.id == form_id
    ).first()

    if not form:
        raise HTTPException(status_code=404, detail="File not found")

    if form.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return StreamingResponse(
        io.BytesIO(form.file_data),
        media_type=form.file_type,
        headers={
            "Content-Disposition":
            f"attachment; filename={form.file_name}"
        }
    )
