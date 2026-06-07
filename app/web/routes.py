from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def trip_list(request: Request):
    trips = []
    return templates.TemplateResponse(request, "trips.html", {"trips": trips})


@router.get("/imports")
def import_review(request: Request):
    return templates.TemplateResponse(request, "import_review.html", {"files": []})
