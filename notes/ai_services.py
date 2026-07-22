import re
from .models import Tag, Note, NoteRelation

def run_ai_analysis(note):
    """
    Анализирует текст заметки, извлекает теги и находит связи с другими заметками.
    В данной версии используется базовая логика (mock), имитирующая работу ИИ.
    """
    content = note.content.lower()
    
    # 1. Извлечение тегов из текста (слова, начинающиеся с #)
    hashtags = re.findall(r'#(\w+)', content)
    for tag_name in hashtags:
        tag, created = Tag.objects.get_or_create(name=tag_name)
        note.tags.add(tag)
        
    # 2. Поиск связей на основе общих тегов
    other_notes = Note.objects.filter(user=note.user).exclude(pk=note.pk)
    
    for other in other_notes:
        common_tags = note.tags.all() & other.tags.all()
        if common_tags:
            reason = f"Общие теги: {', '.join([t.name for t in common_tags])}"
            NoteRelation.objects.get_or_create(
                source=note,
                target=other,
                defaults={'reason': reason, 'weight': 0.8}
            )
            # Создаем обратную связь для неориентированного графа в визуализации
            NoteRelation.objects.get_or_create(
                source=other,
                target=note,
                defaults={'reason': reason, 'weight': 0.8}
            )

    # 3. Дополнительная логика: поиск вхождений названий других заметок в тексте
    for other in other_notes:
        if other.title.lower() in content:
            NoteRelation.objects.get_or_create(
                source=note,
                target=other,
                defaults={'reason': f"Упоминание названия '{other.title}' в тексте", 'weight': 1.0}
            )
