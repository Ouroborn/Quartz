document.addEventListener('DOMContentLoaded', function () {
    const root = document.getElementById('settings-form-root');
    const providerSelect = document.getElementById('id_provider');
    const modelSelect = document.getElementById('id_model_name');
    const apiKeyInput = document.getElementById('id_api_key');
    const loadingLabel = document.getElementById('models-loading');
    const errorLabel = document.getElementById('models-error');

    if (!providerSelect || !modelSelect) return;

    const modelsUrl = root.dataset.modelsUrl;
    const currentModel = root.dataset.currentModel || '';

    let debounceTimer = null;

    function fetchModels() {
        const provider = providerSelect.value;
        if (!provider) {
            modelSelect.innerHTML = '';
            return;
        }

        loadingLabel.style.display = 'inline';
        errorLabel.style.display = 'none';
        modelSelect.disabled = true;

        const params = new URLSearchParams({ provider: provider });
        const apiKey = apiKeyInput ? apiKeyInput.value.trim() : '';
        if (apiKey) {
            params.set('api_key', apiKey);
        }

        fetch(modelsUrl + '?' + params.toString(), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(resp => resp.json())
            .then(data => {
                modelSelect.innerHTML = '';
                const models = data.models || [];

                if (models.length === 0) {
                    errorLabel.style.display = 'inline';
                }

                models.forEach(modelId => {
                    const opt = document.createElement('option');
                    opt.value = modelId;
                    opt.textContent = modelId;
                    if (modelId === currentModel) {
                        opt.selected = true;
                    }
                    modelSelect.appendChild(opt);
                });
            })
            .catch(() => {
                errorLabel.style.display = 'inline';
            })
            .finally(() => {
                loadingLabel.style.display = 'none';
                modelSelect.disabled = false;
            });
    }

    providerSelect.addEventListener('change', fetchModels);

    if (apiKeyInput) {
        apiKeyInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(fetchModels, 600);
        });
    }

    if (providerSelect.value) {
        fetchModels();
    }
});
