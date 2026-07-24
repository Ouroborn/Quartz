function sortTable(n) {
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.getElementById("notesTable");
    switching = true;
    dir = "asc";
    while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];

            var xVal = x.getAttribute("data-value") || x.innerText.toLowerCase();
            var yVal = y.getAttribute("data-value") || y.innerText.toLowerCase();

            var xNum = parseFloat(xVal.replace(/[^\d.-]/g, ''));
            var yNum = parseFloat(yVal.replace(/[^\d.-]/g, ''));

            if (!isNaN(xNum) && !isNaN(yNum) && n !== 0) { // Колонка 0 (название) — текст
                if (dir == "asc") {
                    if (xNum > yNum) { shouldSwitch = true; break; }
                } else if (dir == "desc") {
                    if (xNum < yNum) { shouldSwitch = true; break; }
                }
            } else {
                if (dir == "asc") {
                    if (xVal > yVal) { shouldSwitch = true; break; }
                } else if (dir == "desc") {
                    if (xVal < yVal) { shouldSwitch = true; break; }
                }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount++;
        } else {
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('#notesTable th[data-sort-col]').forEach(th => {
        th.addEventListener('click', () => sortTable(parseInt(th.dataset.sortCol, 10)));
    });
});
