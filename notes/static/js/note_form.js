document.addEventListener('DOMContentLoaded', function () {
    const contentField = document.getElementById('id_content');
    const wrapper = document.getElementById('content-editor-wrapper');
    const uniqueId = (wrapper && wrapper.dataset.autosaveId) || 'new';

    new EasyMDE({
        element: contentField,
        spellChecker: false,
        autosave: {
            enabled: true,
            uniqueId: "note_editor_" + uniqueId,
            delay: 1000,
        },
        status: false,
        minHeight: "400px",
        placeholder: "Начните писать свою заметку...",
        renderingConfig: {
            singleLineBreaks: false,
            codeSyntaxHighlighting: true,
        },
        theme: "quartz"
    });
});
