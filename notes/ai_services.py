import re
from .models import Tag, Note, NoteRelation, UserSettings

def run_ai_analysis(note):
    """
    Анализирует текст заметки и генерирует теги.
    Учитывает настройки пользователя для выбора модели (в будущем).
    """
    try:
        settings = note.user.settings
    except UserSettings.DoesNotExist:
        settings = UserSettings.objects.create(user=note.user)

    # Имитация выбора модели
    model = settings.ai_model
    api_key = settings.api_key

    content = note.content.lower()
    
    # Простая логика извлечения тегов: слова > 7 символов
    # В реальном ИИ здесь был бы запрос к OpenAI/Claude/Ollama
    words = re.findall(r'\b\w{8,}\b', content)
    
    for word in set(words[:10]): # Ограничим до 10 тегов от ИИ
        tag, created = Tag.objects.get_or_create(name=word)
        note.tags.add(tag)

    # Обновление связей в графе
    other_notes = Note.objects.filter(user=note.user).exclude(pk=note.pk)
    for other in other_notes:
        common_tags = note.tags.all() & other.tags.all()
        if common_tags.exists():
            reason = f"Модель {model}: Общие теги ({common_tags.count()})"
            NoteRelation.objects.update_or_create(
                source=note,
                target=other,
                defaults={'reason': reason, 'weight': 1.0}
            )
