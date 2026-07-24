import json
import logging
import re
from openai import OpenAI

from .models import Tag, Note, NoteRelation, UserSettings

logger = logging.getLogger(__name__)

MAX_TAGS = 15

# Провайдеры отдают через /models вообще все свои модели — эмбеддинги,
# генерацию картинок, TTS/STT, модерацию и т.п. Явного флага "это чат-модель"
# API не даёт, поэтому отсеиваем по ключевым словам в названии. Список можно
# смело дополнять, если у конкретного провайдера пролезет что-то новое.
EXCLUDED_MODEL_KEYWORDS = [
    "embed",           # text-embedding-3-small, embedding-001 и т.д.
    "image",           # dall-e, imagen, gpt-image
    "dall-e",
    "imagen",
    "vision-preview",  # старые vision-only модели без обычного чата
    "tts",             # text-to-speech
    "whisper",         # speech-to-text
    "audio",
    "moderation",
    "translate",
    "research",
    "aqa",             # attributed question answering (Gemini)
    "similarity",
    "search",
    "edit",            # code/text-edit модели, не chat-completions
    "realtime",
    "nano-banana",
    "computer-use",
]


def _is_chat_model(model_id):
    lowered = model_id.lower()
    return not any(keyword in lowered for keyword in EXCLUDED_MODEL_KEYWORDS)


# Единая точка правды о провайдерах: base_url, дефолтный ключ, фильтр моделей.
PROVIDER_CONFIG = {
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_key": None,
        "model_filter": None,
    },
    "openai": {
        "base_url": None,  # стандартный OpenAI endpoint
        "default_key": None,
        "model_filter": None,
    },
    "local": {
        "base_url": "http://localhost:11434/v1",
        "default_key": "ollama",  # Ollama требует любой непустой ключ
        "model_filter": None,
    },
    "claude": {
        # У Anthropic нет прямого OpenAI-совместимого эндпоинта, идём через OpenRouter
        "base_url": "https://openrouter.ai/api/v1",
        "default_key": None,
        "model_filter": lambda model_id: model_id.startswith("anthropic/"),
    },
}


def _build_client(provider, api_key):
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        return None
    key = api_key or config["default_key"] or "dummy_key"
    return OpenAI(api_key=key, base_url=config["base_url"])


def list_provider_models(provider, api_key):
    """Спрашивает у провайдера актуальный список моделей. Возвращает список id строк."""
    client = _build_client(provider, api_key)
    if client is None:
        return []

    try:
        response = client.models.list()
    except Exception as exc:
        logger.warning("Не удалось получить список моделей у %s: %s", provider, exc)
        return []

    model_ids = [m.id for m in response.data]

    model_filter = PROVIDER_CONFIG[provider]["model_filter"]
    if model_filter:
        model_ids = [m for m in model_ids if model_filter(m)]

    model_ids = [m for m in model_ids if _is_chat_model(m)]

    return sorted(model_ids)


def run_ai_analysis(note):
    try:
        settings = note.user.settings
    except UserSettings.DoesNotExist:
        settings = UserSettings.objects.create(user=note.user)

    full_model_name = settings.full_model_code
    if not full_model_name:
        return

    api_key = settings.api_key

    existing_tags = list(
        Tag.objects.filter(notes__user=note.user)
        .values_list("name", flat=True)
        .distinct()
    )

    tag_names = _generate_tags(note, settings.provider, settings.model_name, api_key, existing_tags)

    if not tag_names:
        tag_names = _fallback_tags(note.content, existing_tags)

    _attach_tags(note, tag_names)
    _update_relations(note, full_model_name)


def _generate_tags(note, provider, model_name, api_key, existing_tags):
    prompt = _build_prompt(note, existing_tags)

    client = _build_client(provider, api_key)
    if client is None:
        return []

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Ты возвращаешь только JSON-массив строк."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        raw_text = response.choices[0].message.content
    except Exception as exc:
        logger.warning("Ошибка при обращении к ИИ (%s/%s): %s", provider, model_name, exc)
        return []

    return _parse_tags(raw_text)


def _build_prompt(note, existing_tags):
    existing_block = ""
    if existing_tags:
        existing_block = (
                "Уже существующие теги (переиспользуй подходящие из них, "
                "не создавай дубликаты с другим написанием):\n"
                + ", ".join(existing_tags)
                + "\n\n"
        )
    content = (note.content or "")[:4000]

    return (
        "Ты — помощник для системы заметок. Проанализируй заметку и подбери "
        f"от 1 до {MAX_TAGS} коротких тегов (1-2 слова каждый), которые лучше "
        "всего описывают её тему и содержание.\n"
        "Предпочитай переиспользовать существующие теги.\n"
        "Ответь СТРОГО в формате JSON-массива строк без пояснений, например: "
        '["python", "базы данных", "django"].\n\n'
        f"{existing_block}"
        f"Заголовок: {note.title}\n"
        f"Текст:\n{content}\n"
    )


def _parse_tags(raw_text):
    if not raw_text:
        return []
    text = raw_text.strip()
    match = re.search(r"\[.*\]", text, re.DOTALL)
    candidate = match.group(0) if match else text

    tags = []
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, list):
            tags = [str(item) for item in parsed]
    except (ValueError, TypeError):
        tags = re.split(r"[,\n]+", text)

    return _clean_tags(tags)


def _clean_tags(tags):
    cleaned = []
    seen = set()
    for tag in tags:
        name = str(tag).strip().strip("\"'#[]").strip().lower()
        if not name:
            continue
        name = name[:50]
        if name in seen:
            continue
        seen.add(name)
        cleaned.append(name)
        if len(cleaned) >= MAX_TAGS:
            break
    return cleaned


def _fallback_tags(content, existing_tags=None):
    if not existing_tags:
        return []
    text = (content or "").lower()
    words = set(re.findall(r"\b\w+\b", text))
    matched = []
    for tag in existing_tags:
        name = str(tag).strip().lower()
        if not name:
            continue
        if " " in name:
            if name in text:
                matched.append(name)
        elif name in words:
            matched.append(name)
    return _clean_tags(matched[:MAX_TAGS])


def _attach_tags(note, tag_names):
    for name in tag_names:
        tag, _ = Tag.objects.get_or_create(name=name)
        note.tags.add(tag)


def _update_relations(note, model):
    other_notes = Note.objects.filter(user=note.user).exclude(pk=note.pk)
    for other in other_notes:
        common_tags = note.tags.all() & other.tags.all()
        count = common_tags.count()
        if count:
            reason = f"Модель {model}: Общие теги ({count})"
            NoteRelation.objects.update_or_create(
                source=note,
                target=other,
                defaults={"reason": reason, "weight": float(count)},
            )