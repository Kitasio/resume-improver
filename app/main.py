import asyncio
from io import BytesIO
from typing import Annotated
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from resume_improver import HtmlAdapter, ResumeImprover
from weasyprint import HTML

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
cv_templates = Jinja2Templates(directory="app/static/cv_templates")


class UserContext(BaseModel):
    base_resume: str
    job_description: str
    improved_resume: str | None = None
    pdf_bytes: bytes | None = None


cache: dict[str, UserContext] = {}

# Time (in seconds) before cleanup
CONTEXT_LIFETIME = 1200


async def expire_context(ctx_id: str, delay: int):
    await asyncio.sleep(delay)
    cache.pop(ctx_id, None)
    print(f"User context {ctx_id} expired and removed from cache.")


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request=request, name="pages/home.html")


@app.get("/pdf-templates/{id}")
def pdf_template(request: Request, id: str):
    template = cv_templates.env.get_template(f"{id}.html")
    rendered_html = template.render(request=request)
    pdf_io = BytesIO()
    HTML(string=rendered_html).write_pdf(pdf_io)
    pdf_io.seek(0)

    return StreamingResponse(
        pdf_io,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cv.pdf"},
    )


@app.get("/html-templates/{id}", response_class=HTMLResponse)
def html_template(request: Request, id: str):
    return templates.TemplateResponse(request=request, name=f"resumes/{id}.html")


@app.get("/html-templates/{id}/compilations", response_class=HTMLResponse)
def compile_html_template(request: Request, id: str):
    pass


@app.post("/resume-improvements", response_class=HTMLResponse)
def improve_resume(
    response: Response,
    cv_input: Annotated[str, Form()],
    jd_input: Annotated[str, Form()],
    bg_tasks: BackgroundTasks,
):
    resume_improver = ResumeImprover(cv_input=cv_input, jd_input=jd_input)
    result = resume_improver.run()

    context_id = str(uuid4())
    cache[context_id] = UserContext(
        base_resume=cv_input, job_description=jd_input, improved_resume=result
    )
    bg_tasks.add_task(expire_context, context_id, CONTEXT_LIFETIME)

    response.headers["HX-Redirect"] = f"/resume-improvements/{context_id}"
    return "OK"


@app.get("/resume-improvements/{id}", response_class=HTMLResponse)
def improved_resume(request: Request, id: str):
    ctx = cache.get(id)
    if not ctx:
        raise HTTPException(
            status_code=404, detail="Context not found or already expired."
        )

    context = {
        "id": id,
        "improved_resume": ctx.improved_resume,
        "base_resume": ctx.base_resume,
    }

    return templates.TemplateResponse(
        request=request, name="pages/improved-resume.html", context=context
    )


@app.post("/resume-improvements/{id}/pdf-templates/{tpl_id}")
def create_pdf(
    id: str,
    tpl_id: str,
    request: Request,
    response: Response,
    tuning_result: Annotated[str, Form()],
):
    # 1. Render HTML using the Jinja2 environment
    template = cv_templates.env.get_template(f"{tpl_id}.html")
    rendered_html = template.render(request=request)

    html_adapter = HtmlAdapter(tuning_result=tuning_result, html_template=rendered_html)
    result_html = html_adapter.run()

    # 2. Generate PDF from HTML
    pdf_io = BytesIO()
    HTML(string=result_html).write_pdf(pdf_io)
    pdf_io.seek(0)

    cache[id].pdf_bytes = pdf_io.read()

    response.headers["HX-Redirect"] = (
        f"/resume-improvements/{id}/pdf-templates/{tpl_id}"
    )
    return {"message": "OK"}


@app.get("/resume-improvements/{id}/pdf-templates/{tpl_id}")
def get_pdf(id: str):
    ctx = cache.get(id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Context not found")

    if not ctx.pdf_bytes:
        raise HTTPException(status_code=404, detail="PDF not found")

    return StreamingResponse(
        BytesIO(ctx.pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cv.pdf"},
    )
