function toggleSection(header) {
    header.classList.toggle('collapsed');
    const content = header.nextElementSibling;
    content.classList.toggle('hidden');
}

// Небольшой общий хелпер: получить значение CSS-переменной как строку цвета.
// Нужен там, где цвет должен попасть не в CSS, а в JS/canvas (vis-network, chart.js и т.п.),
// потому что такие библиотеки не умеют резолвить var(--...) сами.
function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// CSRF-хелпер используется в нескольких страницах (note_detail и др.)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
