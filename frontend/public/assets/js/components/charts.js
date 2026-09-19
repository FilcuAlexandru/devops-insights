/**
 * Thin wrappers around Chart.js (loaded as a global from /assets/vendor).
 * Colors are read from the CSS custom properties so charts follow the light/dark theme.
 */

const active = new Set();

const cssVariable = (name) =>
    getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function theme() {
    return {
        text: cssVariable("--muted"),
        grid: cssVariable("--border"),
        series: [1, 2, 3, 4, 5, 6, 7, 8].map((index) => cssVariable(`--series-${index}`)),
    };
}

function create(canvas, config) {
    if (!canvas || typeof Chart === "undefined") {
        return null;
    }

    const chart = new Chart(canvas, config);
    active.add(chart);

    return chart;
}

/** Destroy every chart created since the last call. Run it when leaving a page. */
export function destroyCharts() {
    active.forEach((chart) => chart.destroy());
    active.clear();
}

function axes(colors, { horizontal = false } = {}) {
    const valueAxis = {
        beginAtZero: true,
        grid: { color: colors.grid },
        border: { display: false },
        ticks: { color: colors.text, precision: 0 },
    };
    const categoryAxis = {
        grid: { display: false },
        border: { display: false },
        ticks: { color: colors.text, maxRotation: 45, autoSkip: !horizontal },
    };

    return horizontal ? { x: valueAxis, y: categoryAxis } : { x: categoryAxis, y: valueAxis };
}

export function barChart(canvas, { labels, values, label, horizontal = false }) {
    const colors = theme();

    return create(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label,
                    data: values,
                    backgroundColor: colors.series[0],
                    borderRadius: 4,
                    maxBarThickness: 28,
                },
            ],
        },
        options: {
            indexAxis: horizontal ? "y" : "x",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: axes(colors, { horizontal }),
        },
    });
}

export function doughnutChart(canvas, { labels, values }) {
    const colors = theme();

    return create(canvas, {
        type: "doughnut",
        data: {
            labels,
            datasets: [
                {
                    data: values,
                    backgroundColor: labels.map(
                        (_, index) => colors.series[index % colors.series.length],
                    ),
                    borderColor: cssVariable("--surface"),
                    borderWidth: 2,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "62%",
            plugins: {
                legend: {
                    position: "right",
                    labels: { color: colors.text, boxWidth: 12, usePointStyle: true },
                },
            },
        },
    });
}

export function lineChart(canvas, { labels, values, label, seriesIndex = 0 }) {
    const colors = theme();
    const color = colors.series[seriesIndex];

    return create(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label,
                    data: values,
                    borderColor: color,
                    backgroundColor: `${color}22`,
                    fill: true,
                    tension: 0.25,
                    pointRadius: values.length > 30 ? 0 : 3,
                    pointHoverRadius: 5,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: { legend: { display: false } },
            scales: {
                ...axes(colors),
                y: { ...axes(colors).y, beginAtZero: false },
            },
        },
    });
}
