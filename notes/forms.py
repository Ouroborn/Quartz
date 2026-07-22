from django import forms
from .models import Note, Tag, UserSettings, PROVIDER_CHOICES


class UserSettingsForm(forms.ModelForm):
    provider = forms.ChoiceField(
        label="Провайдер",
        choices=[("", "Выберите провайдера...")] + PROVIDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_provider'}),
    )
    # CharField, а не ChoiceField: опции в <select> подставляет JS через AJAX,
    # и Django не должен валидировать значение против статичного списка choices,
    # иначе отправка формы будет падать с "Select a valid choice".
    model_name = forms.CharField(
        label="Модель ИИ",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_model_name'}),
        help_text="Список моделей запрашивается напрямую у провайдера.",
    )

    class Meta:
        model = UserSettings
        fields = ["provider", "model_name", "api_key"]
        widgets = {
            'api_key': forms.PasswordInput(
                attrs={'class': 'form-control', 'autocomplete': 'off'},
                render_value=True,
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Если у пользователя уже сохранена модель — покажем её как единственную
        # опцию сразу (иначе выбранное значение не пройдёт валидацию ChoiceField,
        # пока JS не подгрузит полный список).
        if self.instance and self.instance.pk and self.instance.model_name:
            self.fields['model_name'].widget.choices = [
                (self.instance.model_name, self.instance.model_name)
            ]

    def clean(self):
        cleaned_data = super().clean()
        provider = cleaned_data.get('provider')
        model_name = cleaned_data.get('model_name')
        if provider and not model_name:
            self.add_error('model_name', 'Выберите модель для этого провайдера.')
        return cleaned_data


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'content', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Заголовок'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Текст заметки (Markdown)', 'rows': 10}),
        }
