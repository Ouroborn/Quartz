from django.db import models
from django.contrib.auth.models import User

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes", verbose_name="Пользователь")
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержимое (Markdown)")
    cover = models.ImageField(upload_to='covers/', blank=True, null=True, verbose_name="Обложка")
    views_count = models.PositiveIntegerField(default=0, verbose_name="Количество просмотров")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    
    tags = models.ManyToManyField(Tag, blank=True, related_name="notes", verbose_name="Теги")
    
    relations = models.ManyToManyField(
        "self", 
        through="NoteRelation", 
        symmetrical=False, 
        related_name="related_to",
        verbose_name="Связи"
    )

    class Meta:
        verbose_name = "Заметка"
        verbose_name_plural = "Заметки"

    def __str__(self):
        return self.title

class NoteRelation(models.Model):
    source = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="source_relations")
    target = models.ForeignKey(Note, on_delete=models.CASCADE, related_name="target_relations")
    reason = models.TextField(blank=True, verbose_name="Причина связи")
    weight = models.FloatField(default=1.0, verbose_name="Вес связи")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Связь заметок"
        verbose_name_plural = "Связи заметок"
        unique_together = ("source", "target")

    def __str__(self):
        return f"{self.source} -> {self.target} ({self.weight})"