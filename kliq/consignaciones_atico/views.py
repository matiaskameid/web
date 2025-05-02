import os
import json
import re
import zipfile
from io import BytesIO

import pandas as pd
from django import forms   
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse

from openpyxl import Workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter

from .forms import UploadFileForm, ContactInfoForm

# Directorio raíz de esta app
APP_DIR = os.path.join(settings.BASE_DIR, 'consignaciones_atico')
CONTACT_DATA_FILE = os.path.join(APP_DIR, 'contact_data.json')
LOGO_PATH = os.path.join(
    APP_DIR,
    'static',
    'consignaciones_atico',
    'logo.png'
)

def load_contact_data():
    if os.path.exists(CONTACT_DATA_FILE):
        try:
            with open(CONTACT_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            # No interrumpe el flujo, simplemente lo ignoramos
            print(f"Error cargando contactos: {e}")
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
    except Exception:
        return None

def create_export_excel(df, editorial, logo_content=None, contact_info=None):
    wb = Workbook()
    ws = wb.active
    ws.title = "Liquidación"
    ws.sheet_view.showGridLines = False

    # 📐 Estilos
    title_font  = Font(name="Arial", size=16, bold=True)
    header_font = Font(name="Arial", size=11, bold=True)
    normal_font = Font(name="Arial", size=10)
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Altura de fila para logo
    ws.row_dimensions[1].height = 45

    # Logo
    if logo_content:
        try:
            img = OpenpyxlImage(BytesIO(logo_content))
            img.width  = 80
            img.height = 50
            ws.add_image(img, "A1")
        except Exception:
            pass

    # Título (celdas B1:D2)
    ws.merge_cells("B1:D2")
    cell_title  = ws["B1"]
    title_text  = f"LIQUIDACION CONSIGNACIONES {editorial}"
    cell_title.value     = title_text
    cell_title.font      = title_font
    cell_title.alignment = Alignment(horizontal="center", vertical="center")

    # Info Cliente (B3:D6)
    ws.merge_cells("B3:D6")
    cell_cli   = ws["B3"]
    cell_cli.value = (
        "CLIENTE: Librería Virtual y Distribuidora El Ático Ltda.\n"
        "Venta y Distribución de Libros\n"
        "General Bari 234, Providencia - Santiago, Teléfono: (56)2 21452308\n"
        "Rut: 76082908-0"
    )
    cell_cli.font      = normal_font
    cell_cli.alignment = Alignment(wrap_text=True, vertical="top", horizontal="center")

    # Tabla de contacto (filas 8–13)
    fields = ["PROVEEDOR:", "CONTACTO:", "FONO / MAIL:", "DESCUENTO:", "PAGO:", "FECHA:"]
    for i, field in enumerate(fields, start=8):
        ws.cell(row=i, column=2, value=field).font = header_font
        ws.merge_cells(start_row=i, start_column=3, end_row=i, end_column=4)
        c = ws.cell(row=i, column=3)
        key = field.replace(":", "")
        c.value = contact_info.get(key, "") if contact_info else ""
        c.font  = normal_font
        for col in (2, 3, 4):
            ws.cell(row=i, column=col).border = thin_border

    # Encabezados de datos (fila 16)
    start_row, start_col = 16, 2
    for offset, header in enumerate(df.columns):
        cell = ws.cell(row=start_row, column=start_col+offset, value=header)
        cell.font      = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border    = thin_border

    # Filas de datos
    for r, row_data in enumerate(df.itertuples(index=False), start=start_row+1):
        for offset, value in enumerate(row_data):
            col = start_col + offset
            cell = ws.cell(row=r, column=col, value=value)
            if offset == 2:  # ISBN → int y formato
                try:
                    cell.value = int(value)
                except Exception:
                    pass
                cell.number_format = "0"
            cell.font      = normal_font
            cell.alignment = Alignment(horizontal="left", vertical="center")
            cell.border    = thin_border

    # Ajuste de ancho de columnas
    units_w = len("Unidades a liquidar") + 2
    prod_w  = max(df["Producto"].astype(str).map(len).max() if not df.empty else 0, len("Producto")) + 5
    isbn_w  = 15
    # si el título exige más espacio
    total_req = 2 * len(title_text)
    if units_w + prod_w + isbn_w < total_req:
        prod_w += total_req - (units_w + prod_w + isbn_w)

    ws.column_dimensions[get_column_letter(2)].width = units_w
    ws.column_dimensions[get_column_letter(3)].width = prod_w
    ws.column_dimensions[get_column_letter(4)].width = isbn_w

    # Elimina columnas sobrantes
    max_col = ws.max_column
    if max_col > 5:
        ws.delete_cols(6, max_col - 5)

    # Volcar a bytes
    output = BytesIO()
    wb.save(output)
    return output.getvalue()

def process_master_file(file_bytes, logo_content=None, contact_infos=None):
    # Lee el maestro
    df = pd.read_excel(file_bytes, sheet_name=0, header=5)
    df.columns = df.columns.str.strip()
    if "Código" in df.columns:
        df.rename(columns={"Código": "Codigo"}, inplace=True)

    all_cols      = df.columns.tolist()
    consign_cols  = [c for c in all_cols if re.search(r'consignacion', c, re.IGNORECASE)]
    output_files  = {}
    no_data_edits = []

    # Procesa cada columna de consignación
    for col in consign_cols:
        # Limpieza del nombre
        name = re.sub(r'(?i)consignacion(es)?', '', col)
        name = re.sub(r'\s+', ' ', name)
        name = re.sub(r'[:]+', '', name)
        name = re.sub(r'[0-9-]+', '', name)
        name = name.strip().upper() or "SIN EDITORIAL"

        # Requiere estas columnas
        if not all(x in df.columns for x in ["Producto", "Codigo", "BODEGA GENERAL BARI"]):
            return {}, []

        temp = df[["Producto", "Codigo", "BODEGA GENERAL BARI", col]].copy()
        temp.rename(columns={col: "Consignaciones"}, inplace=True)
        temp = temp[temp["BODEGA GENERAL BARI"] >= 0]
        temp["Unidades a liquidar"] = temp["Consignaciones"] - temp["BODEGA GENERAL BARI"]
        temp = temp[temp["Unidades a liquidar"] > 0]
        temp = temp.sort_values("Producto")

        if temp.empty:
            no_data_edits.append(name)
            continue

        export_df = temp[["Unidades a liquidar", "Producto", "Codigo"]].copy()
        export_df.rename(columns={"Codigo": "ISBN"}, inplace=True)
        export_df["ISBN"] = (
            export_df["ISBN"]
            .astype(str)
            .apply(lambda x: x.split("/")[0][:13])
        )

        ci = contact_infos.get(name, {}) if contact_infos else {}
        excel_bytes = create_export_excel(export_df, name, logo_content, ci)
        filename    = f"Liquidacion_Consignaciones_{name}.xlsx"
        output_files[filename] = excel_bytes

    return output_files, no_data_edits

def index(request):
    # Carga contactos previos
    contact_data  = load_contact_data()
    upload_form   = UploadFileForm(request.POST or None, request.FILES or None)
    ContactFS     = forms.formset_factory(ContactInfoForm, extra=0)

    editorial_list = []
    file_bytes     = None

    # Paso 1: Leer Excel y extraer editoriales
    if request.method == "POST" and upload_form.is_valid():
        f          = upload_form.cleaned_data["file"]
        file_bytes = f.read()
        df_t = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=5)
        df_t.columns = df_t.columns.str.strip()
        for col in df_t.columns:
            if re.search(r'consignacion', col, re.IGNORECASE):
                ed = re.sub(r'(?i)consignacion(es)?', '', col)
                ed = re.sub(r'\s+', ' ', ed)
                ed = re.sub(r'[:]+', '', ed)
                ed = re.sub(r'[0-9-]+', '', ed)
                ed = ed.strip().upper() or "SIN EDITORIAL"
                editorial_list.append(ed)
        editorial_list = sorted(set(editorial_list))

    # Paso 2: Formset con datos guardados
    initial = []
    for ed in editorial_list:
        d = contact_data.get(ed, {})
        d["editorial"] = ed
        initial.append(d)
    formset = ContactFS(request.POST or None, initial=initial)

    # Paso 3: Guardar contactos
    if (
        request.method == "POST"
        and "save_contacts" in request.POST
        and formset.is_valid()
    ):
        new_data = {}
        for frm in formset:
            cd = frm.cleaned_data
            ed = cd.pop("editorial")
            new_data[ed] = cd
        save_contact_data(new_data)
        messages.success(request, "Datos de contacto guardados correctamente.")

    # Paso 4: Generar ZIP
    if (
        request.method == "POST"
        and "generate_liquidaciones" in request.POST
        and upload_form.is_valid()
        and formset.is_valid()
    ):
        ci    = {
            frm.cleaned_data["editorial"]: {
                "PROVEEDOR":    frm.cleaned_data["PROVEEDOR"],
                "CONTACTO":     frm.cleaned_data["CONTACTO"],
                "FONO / MAIL":  frm.cleaned_data["FONO_MAIL"],
                "DESCUENTO":    frm.cleaned_data["DESCUENTO"],
                "PAGO":         frm.cleaned_data["PAGO"],
                "FECHA":        frm.cleaned_data["FECHA"],
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
            resp = HttpResponse(buf.read(), content_type="application/zip")
            resp["Content-Disposition"] = 'attachment; filename="Liquidaciones.zip"'
            return resp

    return render(
        request,
        'consignaciones_atico/index.html',
        {
            'upload_form':     upload_form,
            'formset':         formset,
            'editorial_list':  editorial_list,
        }
    )
