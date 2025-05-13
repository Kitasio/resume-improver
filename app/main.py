from typing import Annotated

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(request=request, name="pages/home.html")


@app.post("/cv-tunes", response_class=HTMLResponse)
def cv_tunes(
    request: Request, cv_input: Annotated[str, Form()], jd_input: Annotated[str, Form()]
):
    context = {
        "cv_input": cv_input,
        "jd_input": jd_input,
    }

    return templates.TemplateResponse(
        request=request, name="components/cv-tuning-response.html", context=context
    )
