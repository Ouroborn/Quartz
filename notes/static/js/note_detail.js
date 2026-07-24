document.addEventListener('DOMContentLoaded', function () {
    const root = document.getElementById('note-detail-root');
    const csrftoken = getCookie('csrftoken');

    const urls = {
        regenerateTags: root.dataset.regenerateTagsUrl,
        addTag: root.dataset.addTagUrl,
        removeTag: root.dataset.removeTagUrl,
        trackView: root.dataset.trackViewUrl,
    };

    function buildTagBadge(tagName) {
        const badge = document.createElement('span');
        badge.className = 'tag-badge';
        badge.dataset.tag = tagName;

        const removeBtn = document.createElement('span');
        removeBtn.className = 'tag-remove';
        removeBtn.innerHTML = '&times;';
        removeBtn.onclick = () => removeTag(tagName);

        badge.appendChild(document.createTextNode(tagName + ' '));
        badge.appendChild(removeBtn);
        return badge;
    }

    async function regenerateTags() {
        const btn = document.getElementById('regenerate-tags-btn');
        const status = document.getElementById('regenerate-status');

        btn.disabled = true;
        const originalText = btn.textContent;
        btn.textContent = 'Генерируем теги...';
        status.style.display = 'block';
        status.className = 'regenerate-status info';
        status.textContent = 'ИИ анализирует текущий текст заметки, это может занять несколько секунд...';

        try {
            const response = await fetch(urls.regenerateTags, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken }
            });
            const data = await response.json();

            if (response.ok && data.status === 'ok') {
                const container = document.getElementById('tag-container');
                const addBox = container.querySelector('.add-tag-box');

                container.querySelectorAll('.tag-badge').forEach(el => el.remove());
                data.tags.forEach(tagName => {
                    container.insertBefore(buildTagBadge(tagName), addBox);
                });

                status.className = 'regenerate-status success';
                status.textContent = `Готово: ${data.tags.length} тег(ов) обновлено.`;
            } else {
                status.className = 'regenerate-status error';
                status.textContent = data.message || 'Не удалось обновить теги.';
            }
        } catch (e) {
            status.className = 'regenerate-status error';
            status.textContent = 'Ошибка сети при обращении к серверу.';
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
            setTimeout(() => { status.style.display = 'none'; }, 6000);
        }
    }

    async function addTag() {
        const input = document.getElementById('new-tag-input');
        const addBtn = document.getElementById('add-tag-btn');
        const tagName = input.value.trim();
        if (!tagName) return;

        const lowerName = tagName.toLowerCase();
        const already = Array.from(document.querySelectorAll('.tag-badge'))
            .some(el => (el.dataset.tag || '').toLowerCase() === lowerName);
        if (already) {
            input.value = '';
            return;
        }

        addBtn.disabled = true;

        const formData = new FormData();
        formData.append('tag_name', tagName);

        try {
            const response = await fetch(urls.addTag, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                const container = document.getElementById('tag-container');
                const addBox = container.querySelector('.add-tag-box');
                container.insertBefore(buildTagBadge(data.tag), addBox);
                input.value = '';
            }
        } finally {
            addBtn.disabled = false;
            input.focus();
        }
    }

    async function removeTag(tagName) {
        const formData = new FormData();
        formData.append('tag_name', tagName);

        const response = await fetch(urls.removeTag, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
            body: formData
        });

        if (response.ok) {
            const tagEl = document.querySelector(`.tag-badge[data-tag="${CSS.escape(tagName)}"]`);
            if (tagEl) tagEl.remove();
        }
    }

    // Кнопки
    document.getElementById('regenerate-tags-btn').addEventListener('click', regenerateTags);
    document.getElementById('add-tag-btn').addEventListener('click', addTag);
    document.getElementById('new-tag-input').addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            addTag();
        }
    });
    document.querySelectorAll('.tag-remove').forEach(el => {
        const tagName = el.closest('.tag-badge').dataset.tag;
        el.addEventListener('click', () => removeTag(tagName));
    });

    // Smart View Tracking
    setTimeout(async () => {
        try {
            const response = await fetch(urls.trackView, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken }
            });
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'view_tracked') {
                    console.log('View tracked:', data.count);
                }
            }
        } catch (e) {
            console.error('View tracking failed', e);
        }
    }, 15000); // 15 секунд
});
