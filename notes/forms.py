from django import forms
from .models import Note, Tag

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'cover', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Заголовок'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Текст заметки (Markdown)', 'rows': 10}),
            'cover': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
