import os
import json
import re
import zipfile
from io import BytesIO

import pandas as pd
from django import forms
from django.shortcuts          import render
from django.conf               import settings
from django.contrib            import messages
from django.http               import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base    import ContentFile

from openpyxl import Workbook
from openpyxl.drawing.image   import Image as OpenpyxlImage
from openpyxl.styles          import Alignment, Font, Border, Side
from openpyxl.utils           import get_column_letter

from .forms import UploadFileForm, ContactInfoForm

# — rutas dentro de la app —
APP_DIR = os.path.join(settings.BASE_DIR, 'consignaciones_atico')
CONTACT_DATA_FILE = os.path.join(APP_DIR, 'contact_data.json')
LOGO_PATH = os.path.join(APP_DIR, 'static', 'consignaciones_atico', 'logo.png')

def load_contact_data():
    try:
        with open(CONTACT_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_contact_data(data):
    try:
        with open(CONTACT_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        messages.error(None, f"Error al guardar contactos: {e}")

def load_default_logo():
    try:
        with open(LOGO_PATH, 'rb') as f:
            return f.read()
    except:
        return None

def extract_editorials_from_bytes(file_bytes):
    """Lee el maestro y devuelve lista de nombres de editoriales."""
    df_t = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=5)
    df_t.columns = df_t.columns.str.strip()
    edits = []
    for col in df_t.columns:
        if re.search(r"consignacion", col, re.IGNORECASE):
            ed = re.sub(r"(?i)consignacion(es)?", "", col)
            ed = re.sub(r"\s+", " ", ed)
            ed = re.sub(r"[:]+", "", ed)
            ed = re.sub(r"[0-9-]+", "", ed)
            edits.append(ed.strip().upper() or "SIN EDITORIAL")
    return sorted(set(edits))

# Aquí van create_export_excel y process_master_file tal cual los tenías
# … (omitidos por brevedad, copia tu implementación) …

def index(request):
    # 1) En GET, siempre limpiamos para empezar “fase 1”
    if request.method == "GET":
        request.session.pop("uploaded_file_path", None)

    contact_data = load_contact_data()
    upload_form  = UploadFileForm(request.POST or None, request.FILES or None)
    FormSet      = forms.formset_factory(ContactInfoForm, extra=0)

    # 2) Si pulsaron “Procesar Archivo” y es válido, lo guardamos en sesión
    if request.method == "POST" and "upload" in request.POST and upload_form.is_valid():
        f = upload_form.cleaned_data["file"]
        temp_path = default_storage.save("temp/" + f.name, ContentFile(f.read()))
        request.session["uploaded_file_path"] = temp_path

    # 3) Reconstruimos editorial_list SI tenemos un archivo en sesión
    editorial_list = []
    uploaded_path  = request.session.get("uploaded_file_path")
    if uploaded_path and default_storage.exists(uploaded_path):
        file_bytes     = default_storage.open(uploaded_path).read()
        editorial_list = extract_editorials_from_bytes(file_bytes)

    # 4) Preparamos el formset con datos guardados y los “editorial” como hidden
    initial = []
    for ed in editorial_list:
        entry = contact_data.get(ed, {}).copy()
        entry["editorial"] = ed
        initial.append(entry)
    formset = FormSet(request.POST or None, initial=initial)

    # 5) Si guardan contactos…
    if request.method == "POST" and "save_contacts" in request.POST and formset.is_valid():
        new_data = {}
        for frm in formset:
            cd = frm.cleaned_data
            ed = cd.pop("editorial")
            new_data[ed] = cd
        save_contact_data(new_data)
        messages.success(request, "Datos de contacto guardados correctamente.")

    # 6) Si generan liquidaciones…
    if request.method == "POST" and "generate_liquidaciones" in request.POST and formset.is_valid():
        uploaded_path = request.session.get("uploaded_file_path")
        if not uploaded_path or not default_storage.exists(uploaded_path):
            messages.error(request, "Debes procesar el archivo antes de generar las liquidaciones.")
        else:
            file_bytes = default_storage.open(uploaded_path).read()
            # reconstruimos dict de contactos
            ci = {
                frm.cleaned_data["editorial"]: {
                    "PROVEEDOR":   frm.cleaned_data["PROVEEDOR"],
                    "CONTACTO":    frm.cleaned_data["CONTACTO"],
                    "FONO / MAIL": frm.cleaned_data["FONO_MAIL"],
                    "DESCUENTO":   frm.cleaned_data["DESCUENTO"],
                    "PAGO":        frm.cleaned_data["PAGO"],
                    "FECHA":       frm.cleaned_data["FECHA"],
                }
                for frm in formset
            }
            logo, no_data = load_default_logo(), []
            files, no_data = process_master_file(file_bytes, logo, ci)

            if not files:
                messages.error(request, "No se generaron liquidaciones.")
            else:
                buf = BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for name, content in files.items():
                        zf.writestr(name, content)
                buf.seek(0)
                response = HttpResponse(buf.read(), content_type="application/zip")
                response["Content-Disposition"] = 'attachment; filename="Liquidaciones.zip"'
                return response

    # 7) Render final
    return render(request, "consignaciones_atico/index.html", {
        "upload_form":    upload_form,
        "formset":        formset,
        "editorial_list": editorial_list,
    })
