from django import forms

from .models import PublicDocument


class PublicDocumentForm(forms.ModelForm):
    class Meta:
        model = PublicDocument
        fields = ["title", "category", "description", "file", "is_public", "display_order"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-checkbox"
            else:
                suffix = " form-input form-select" if isinstance(field.widget, forms.Select) else " form-input"
                field.widget.attrs["class"] = (field.widget.attrs.get("class", "") + suffix).strip()
