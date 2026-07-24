/**
 * Получает значение CSS-переменной из корневого элемента :root
 * @param {string} name - Имя переменной (например, '--accent')
 * @param {string} fallback - Значение по умолчанию
 */
function cssVar(name, fallback = '#9d66b8') {
    if (typeof window === 'undefined') return fallback;
    const val = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return val || fallback;
}

/**
 * Преобразует HEX-цвет в RGB объект для расчёта градиента
 * @param {string} hex - Цвет в формате #RRGGBB или #RGB
 */
function hexToRgb(hex) {
    if (!hex) return null;
    let cleanHex = hex.trim().replace('#', '');
    if (cleanHex.length === 3) {
        cleanHex = cleanHex.split('').map(c => c + c).join('');
    }
    const match = cleanHex.match(/^([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
    if (!match) return null;
    return {
        r: parseInt(match[1], 16),
        g: parseInt(match[2], 16),
        b: parseInt(match[3], 16)
    };
}

/**
 * Переключает видимость панели настроек графа
 */
function toggleSettings() {
    const content = document.getElementById('settings-content');
    const icon = document.getElementById('toggle-icon');
    if (!content || !icon) return;

    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.innerText = '▼';
    } else {
        content.style.display = 'none';
        icon.innerText = '◀';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('mynetwork');
    if (!container) return;

    const dataUrl = container.dataset.graphDataUrl;
    const noteUrlBase = container.dataset.noteUrlBase || '/notes/';

    // Безопасное получение цветов из CSS-переменных темы
    const accentColor = cssVar('--accent', '#9d66b8');
    const canvasBg = cssVar('--bg-canvas', '#121212');
    const textMain = cssVar('--text-main', '#e0e0e0');
    const edgeColor = '#333333';
    const edgeHoverColor = cssVar('--text-dim', '#666666');

    fetch(dataUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Ошибка загрузки графа: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // 1. АНАЛИЗ СВЯЗЕЙ (Расчет степеней узлов)
            const degrees = {};
            data.nodes.forEach(n => degrees[n.id] = 0);
            data.edges.forEach(e => {
                if (degrees[e.from] !== undefined) degrees[e.from]++;
                if (degrees[e.to] !== undefined) degrees[e.to]++;
            });

            let maxDegree = 1;
            Object.values(degrees).forEach(d => { if (d > maxDegree) maxDegree = d; });

            // Градиент цвета от базового темно-фиолетового к акцентному цвету темы
            const startRgb = { r: 120, g: 100, b: 135 };
            const endRgb = hexToRgb(accentColor) || { r: 217, g: 162, b: 244 };

            function getColorForDegree(degree, max) {
                const ratio = max > 0 ? (degree / max) : 0;
                const r = Math.round(startRgb.r + ratio * (endRgb.r - startRgb.r));
                const g = Math.round(startRgb.g + ratio * (endRgb.g - startRgb.g));
                const b = Math.round(startRgb.b + ratio * (endRgb.b - startRgb.b));

                return {
                    hex: `rgb(${r}, ${g}, ${b})`,
                    rgba: `rgba(${r}, ${g}, ${b}, 0.5)`
                };
            }

            // 2. ПОДГОТОВКА УЗЛОВ И ИХ ВНЕШНЕГО ВИДА
            const rangeNodeSizeEl = document.getElementById('range-node-size');
            const checkGlowEl = document.getElementById('check-glow');

            let initialBaseSize = rangeNodeSizeEl ? parseInt(rangeNodeSizeEl.value) : -10;
            const glowEnabled = checkGlowEl ? checkGlowEl.checked : true;

            data.nodes.forEach(node => {
                const degree = degrees[node.id];
                const colors = getColorForDegree(degree, maxDegree);

                node.size = initialBaseSize + (degree * 2);
                node.color = {
                    background: colors.hex,
                    border: colors.hex,
                    highlight: { background: '#ffffff', border: colors.hex }
                };
                node.shadow = {
                    enabled: glowEnabled,
                    color: colors.rgba,
                    size: 4 + (degree * 2),
                    x: 0,
                    y: 0
                };
                node.font = { size: 14, color: textMain, strokeWidth: 4, strokeColor: canvasBg };
            });

            const nodesDataSet = new vis.DataSet(data.nodes);
            const edgesDataSet = new vis.DataSet(data.edges);

            let currentOptions = {
                nodes: { borderWidth: 0 },
                edges: {
                    width: 1,
                    color: { color: edgeColor, highlight: accentColor, hover: edgeHoverColor },
                    smooth: false,
                    selectionWidth: 2,
                    hoverWidth: 1.5
                },
                physics: {
                    enabled: true,
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {
                        gravitationalConstant: -120,
                        centralGravity: 0.005,
                        springLength: 150,
                        springConstant: 0.2,
                        damping: 0.6
                    },
                    minVelocity: 0.75,
                    stabilization: { iterations: 50, fit: true }
                },
                interaction: { hover: true, hoverConnectedEdges: true, zoomView: true }
            };

            const network = new vis.Network(container, { nodes: nodesDataSet, edges: edgesDataSet }, currentOptions);

            // 3. УПРАВЛЕНИЕ РЕЖИМАМИ ОТОБРАЖЕНИЯ
            function applyGraphMode(mode) {
                if (mode === 'quartz') {
                    network.setOptions({ nodes: { shape: 'diamond' }, edges: { smooth: false } });
                } else {
                    network.setOptions({ nodes: { shape: 'dot' }, edges: { smooth: { type: 'dynamic' } } });
                }
            }

            const uiGraphMode = document.getElementById('select-graph-mode');
            if (uiGraphMode) {
                applyGraphMode(uiGraphMode.value);
                uiGraphMode.addEventListener('change', function () { applyGraphMode(this.value); });
            }

            if (checkGlowEl) {
                checkGlowEl.addEventListener('change', function () {
                    const isGlow = this.checked;
                    const updatedNodes = data.nodes.map(node => ({
                        id: node.id,
                        shadow: { enabled: isGlow }
                    }));
                    nodesDataSet.update(updatedNodes);
                });
            }

            // Переход к заметке при клике на узел
            network.on("click", function (params) {
                if (params.nodes.length > 0) {
                    window.location.href = noteUrlBase + params.nodes[0] + '/';
                }
            });
            network.on("hoverNode", () => container.style.cursor = 'pointer');
            network.on("blurNode", () => container.style.cursor = 'default');

            const uiRepel = document.getElementById('range-repel');
            const uiGravity = document.getElementById('range-gravity');
            const uiLinkLen = document.getElementById('range-link-length');
            const uiNodeSize = document.getElementById('range-node-size');

            function updateGraphPhysics() {
                if (uiRepel) document.getElementById('val-repel').innerText = uiRepel.value;
                if (uiGravity) document.getElementById('val-gravity').innerText = uiGravity.value;
                if (uiLinkLen) document.getElementById('val-link-length').innerText = uiLinkLen.value;
                if (uiNodeSize) document.getElementById('val-node-size').innerText = uiNodeSize.value;

                if (uiNodeSize) {
                    const newBaseSize = parseInt(uiNodeSize.value);
                    const updatedNodes = data.nodes.map(node => ({
                        id: node.id,
                        size: newBaseSize + (degrees[node.id] * 2)
                    }));
                    nodesDataSet.update(updatedNodes);
                }

                network.setOptions({
                    physics: {
                        forceAtlas2Based: {
                            gravitationalConstant: uiRepel ? -parseInt(uiRepel.value) : -120,
                            centralGravity: uiGravity ? parseFloat(uiGravity.value) : 0.005,
                            springLength: uiLinkLen ? parseInt(uiLinkLen.value) : 150
                        }
                    }
                });
            }

            [uiRepel, uiGravity, uiLinkLen, uiNodeSize].forEach(slider => {
                if (slider) slider.addEventListener('input', updateGraphPhysics);
            });
        })
        .catch(err => {
            console.error('Ошибка при отображении графа:', err);
        });
});