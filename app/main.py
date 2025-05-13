from io import BytesIO
from typing import Annotated

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tuner import HtmlAdapter, Tuner
from weasyprint import HTML

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request=request, name="pages/home.html")


@app.get("/cv-examples/1", response_class=HTMLResponse)
def cv_examples(request: Request):
    return templates.TemplateResponse(request=request, name="cv_templates/1.html")


@app.get("/cv-examples/1/pdf")
def cv_pdf(request: Request):
    # 1. Render HTML using the Jinja2 environment
    template = templates.env.get_template("cv_templates/1.html")
    rendered_html = template.render(request=request)

    # 2. Generate PDF from HTML
    pdf_io = BytesIO()
    HTML(string=rendered_html, base_url="templates").write_pdf(pdf_io)
    pdf_io.seek(0)

    # 3. Return PDF as a downloadable file
    return StreamingResponse(
        pdf_io,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=cv.pdf"},
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


@app.post("/cv-tunes/pdf")
def create_pdf(request: Request, tuning_result: Annotated[str, Form()]):
    # 1. Render HTML using the Jinja2 environment
    template = templates.env.get_template("cv_templates/1.html")
    rendered_html = template.render(request=request)

    html_adapter = HtmlAdapter(tuning_result=tuning_result, html_template=rendered_html)
    result_html = html_adapter.run()

    # 2. Generate PDF from HTML
    pdf_io = BytesIO()
    HTML(string=result_html, base_url="templates").write_pdf(pdf_io)
    pdf_io.seek(0)

    with open("result_cv.pdf", "wb") as f:
        f.write(pdf_io.read())

    return {"message": "PDF was saved to disc"}
