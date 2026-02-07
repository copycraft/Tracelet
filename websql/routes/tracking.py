# websql / routes / tracking

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from websql.api import api_get, api_post
from websql.main import templates
from PIL import Image

import io
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

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
        # ✅ Match backend schema: external_id, type, extra_data
        api_post("/entities", {
            "external_id": tracking_number,
            "type": "package",
            "extra_data": {
                "label": f"Package {tracking_number}"
            }
        })

        api_post(f"/events/{tracking_number}", {
            "event_type": "created",
            "data": {
                "sender": sender,
                "recipient": recipient,
                "destination": destination,
                "weight_kg": weight_kg,
            }
        })

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
    return templates.TemplateResponse("tracking_add_event.html", {"request": request, "tracking_number": tracking_number, "error": None})


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
        api_post(f"/events/{tracking_number}", {
            "event_type": status,
            "data": {
                "location": location,
                "actor": actor,
                "notes": notes,
            }
        })
        return RedirectResponse(url=f"/tracking/{tracking_number}", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "tracking_add_event.html",
            {"request": request, "tracking_number": tracking_number, "error": str(e)},
        )


# ---------------- PDF Download with QR Code ----------------

@router.get("/{tracking_number}/download-pdf")
def download_package_pdf(tracking_number: str):
    package = api_get(f"/tracking/track/{tracking_number}")

    # Access created_at correctly
    created_at = package['package']['created_at']
    qr_data = f"{tracking_number} | {created_at}"

    # Generate QR code using QRCode class
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")  # PIL Image

    # Save QR code to a temporary buffer
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_pil = Image.open(qr_buffer)

    # Create PDF
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4

    # Add package info
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, f"Package: {tracking_number}")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Created at: {created_at}")
    c.drawString(50, height - 110, f"Status: {package['status']}")
    c.drawString(50, height - 140, f"Current location: {package.get('current_location', 'Unknown')}")

    details = package.get('package', {}).get('details', {})
    c.drawString(50, height - 170, f"Sender: {details.get('sender', 'N/A')}")
    c.drawString(50, height - 200, f"Recipient: {details.get('recipient', 'N/A')}")
    c.drawString(50, height - 230, f"Destination: {details.get('destination', 'N/A')}")
    if 'weight_kg' in details:
        c.drawString(50, height - 260, f"Weight: {details['weight_kg']} kg")

    # Draw QR code image on PDF
    c.drawInlineImage(qr_pil, 400, height - 300, 150, 150)

    c.showPage()
    c.save()
    pdf_buffer.seek(0)

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={tracking_number}.pdf"}
    )