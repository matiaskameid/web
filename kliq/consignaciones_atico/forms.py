# WEB/kliq/consignaciones_atico/forms.py
from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(
        label="Sube el archivo Excel maestro (.xlsx)",
        widget=forms.ClearableFileInput(attrs={'accept':'.xlsx'})
    )

class ContactInfoForm(forms.Form):
    editorial = forms.CharField(widget=forms.HiddenInput())
    PROVEEDOR   = forms.CharField(label="Proveedor",   required=False)
    CONTACTO    = forms.CharField(label="Contacto",    required=False)
    FONO_MAIL   = forms.CharField(label="Fono / Mail", required=False)
    DESCUENTO   = forms.CharField(label="Descuento",   required=False)
    PAGO        = forms.CharField(label="Pago",        required=False)
    FECHA       = forms.CharField(label="Fecha",       required=False)
