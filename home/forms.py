from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()

class CSVUploadForm(forms.Form):
    file = forms.FileField()
