# websql / routes / tracking

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from websql.api import api_get, api_post, api_stream
from websql.main import templates

router = APIRouter(prefix="/tracking", tags=["Tracking UI"])


@router.get("", response_class=HTMLResponse)
def tracking_home(request: Request, status: str = None):
    try:
        params = f"?status={status}" if status else ""
        packages = api_get(f"/tracking/packages{params}")
        stats = api_get("/tracking/stats")

        return templates.TemplateResponse(
            "tracking.html",
            {"request": request, "packages": packages, "stats": stats, "filter_status": status},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_class=HTMLResponse)
def search_package(request: Request, q: str = ""):
    if not q:
        return templates.TemplateResponse(
            "tracking_search.html",
            {"request": request, "query": q, "package": None, "error": None},
        )
    try:
        package = api_get(f"/tracking/track/{q}")
        return templates.TemplateResponse(
            "tracking_search.html",
            {"request": request, "query": q, "package": package, "error": None},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "tracking_search.html",
            {"request": request, "query": q, "package": None, "error": str(e)},
        )


@router.get("/create", response_class=HTMLResponse)
def create_package_form(request: Request):
    return templates.TemplateResponse("tracking_create.html", {"request": request, "error": None})


@router.post("/create", response_class=HTMLResponse)
def create_package(
    request: Request,
    tracking_number: str = Form(...),
    sender: str = Form(...),
    recipient: str = Form(...),
    destination: str = Form(...),
    weight_kg: float = Form(None),
):
    try:
        entity_payload = {
            "external_id": tracking_number,
            "type": "package",
            "extra_data": {
                "sender": sender,
                "recipient": recipient,
                "destination": destination,
                "weight_kg": weight_kg
            }
        }
        entity = api_post("/entities", entity_payload)

        event_payload = {
            "entity_id": entity["id"],
            "event_type": "created",
            "payload": {"creator": "web-ui"}
        }
        api_post("/events", event_payload)

        return RedirectResponse(url=f"/tracking/{tracking_number}", status_code=303)

    except Exception as e:
        return templates.TemplateResponse("tracking_create.html", {"request": request, "error": str(e)})


@router.get("/{tracking_number}", response_class=HTMLResponse)
def track_package(tracking_number: str, request: Request):
    try:
        package = api_get(f"/tracking/track/{tracking_number}")
        return templates.TemplateResponse("tracking_detail.html", {"request": request, "package": package})
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{tracking_number}/add-event", response_class=HTMLResponse)
def add_event_form(tracking_number: str, request: Request):
    return templates.TemplateResponse(
        "tracking_add_event.html",
        {"request": request, "tracking_number": tracking_number, "error": None}
    )


@router.post("/{tracking_number}/add-event", response_class=HTMLResponse)
def add_event(
    tracking_number: str,
    request: Request,
    status: str = Form(...),
    location: str = Form(None),
    actor: str = Form(None),
    notes: str = Form(None)
):
    try:
        entity = api_get(f"/entities/external/{tracking_number}")
    except Exception as e:
        return templates.TemplateResponse(
            "tracking_add_event.html",
            {"request": request, "tracking_number": tracking_number, "error": f"Package not found: {e}"},
        )

    if not entity or "id" not in entity:
        return templates.TemplateResponse(
            "tracking_add_event.html",
            {"request": request, "tracking_number": tracking_number, "error": "Package not found"},
        )

    payload = {
        "entity_id": entity["id"],
        "event_type": status,
        "location": location,
        "actor": actor,
        "payload": {"notes": notes},
    }

    try:
        api_post("/events", payload)
        return RedirectResponse(url=f"/tracking/{tracking_number}", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "tracking_add_event.html",
            {"request": request, "tracking_number": tracking_number, "error": str(e)},
        )


# ---------------- PDF Download ----------------
@router.get("/{tracking_number}/download-pdf")
def download_package_pdf(tracking_number: str):
    """
    Calls the dedicated backend PDF endpoint in tracking_pdf router.
    """
    try:
        # This hits the backend endpoint: /tracking_pdf/download-pdf/{tracking_number}
        pdf_response = api_stream(f"/tracking_pdf/download-pdf/{tracking_number}")

        return StreamingResponse(
            pdf_response,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={tracking_number}.pdf"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download PDF: {str(e)}")
