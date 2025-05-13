import asyncio
from io import BytesIO
from typing import Annotated
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tuner import HtmlAdapter, Tuner
from weasyprint import HTML

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
cv_templates = Jinja2Templates(directory="app/static/cv_templates")

pdf_cache: dict[str, BytesIO] = {}

# Time (in seconds) before cleanup
PDF_LIFETIME = 300


async def expire_pdf(pdf_id: str, delay: int):
    await asyncio.sleep(delay)
    pdf_cache.pop(pdf_id, None)
    print(f"PDF {pdf_id} expired and removed from cache.")


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request=request, name="pages/home.html")


@app.get("/cv-examples/1", response_class=HTMLResponse)
def cv_examples(request: Request):
    return templates.TemplateResponse(request=request, name="cv_templates/1.html")


@app.post("/cv-tunes-trigger-button", response_class=HTMLResponse)
def cv_tunes_trigger(request: Request):
    return templates.TemplateResponse(
        request=request, name="components/cv-tuning-in-progress.html"
    )


@app.post("/cv-tunes", response_class=HTMLResponse)
def cv_tunes(
    request: Request, cv_input: Annotated[str, Form()], jd_input: Annotated[str, Form()]
):
    tuner = Tuner(cv_input=cv_input, jd_input=jd_input)
    result = tuner.run()

    context = {
        "tuning_result": result,
        "cv_input": cv_input,
    }

    return templates.TemplateResponse(
        request=request, name="components/cv-tuning-response.html", context=context
    )


@app.post("/cv-tunes/pdf-trigger-button")
def create_pdf_trigger(request: Request):
    return templates.TemplateResponse(
        request=request, name="components/create-pdf-in-progress.html"
    )


@app.post("/cv-tunes/pdf")
def create_pdf(
    request: Request,
    response: Response,
    bg_tasks: BackgroundTasks,
    tuning_result: Annotated[str, Form()],
):
    # 1. Render HTML using the Jinja2 environment
    template = cv_templates.env.get_template("1.html")
    rendered_html = template.render(request=request)

    html_adapter = HtmlAdapter(tuning_result=tuning_result, html_template=rendered_html)
    result_html = html_adapter.run()

    # 2. Generate PDF from HTML
    pdf_io = BytesIO()
    HTML(string=result_html).write_pdf(pdf_io)
    pdf_io.seek(0)

    pdf_id = str(uuid4())
    pdf_cache[pdf_id] = pdf_io

    bg_tasks.add_task(expire_pdf, pdf_id, PDF_LIFETIME)

    response.headers["HX-Redirect"] = f"/cv-tunes/pdf/{pdf_id}"
    return {"message": "ok"}


@app.get("/cv-tunes/pdf/{id}")
def get_pdf(id):
    pdf_io = pdf_cache.pop(id, None)
    if not pdf_io:
        raise HTTPException(
            status_code=404, detail="PDF not found or already accessed."
        )

    return StreamingResponse(
        pdf_io,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cv.pdf"},
    )


@app.get("/cv-examples/1/pdf")
def cv_pdf(request: Request):
    # 1. Render HTML using the Jinja2 environment
    template = cv_templates.env.get_template("1.html")
    rendered_html = template.render(request=request)

    # 2. Generate PDF from HTML
    pdf_io = BytesIO()
    HTML(string=rendered_html).write_pdf(pdf_io)
    pdf_io.seek(0)

    # 3. Return PDF as a downloadable file
    return StreamingResponse(
        pdf_io,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cv.pdf"},
    )
