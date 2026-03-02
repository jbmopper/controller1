import {chart} from "./echart.js";

function uniqueValues(values) {
  return Array.from(new Set(values.map((value) => String(value))));
}

export function groupedBarPlot(rows, {title, xKey, groupKey, yKey, yPercent = false} = {}) {
  const xValues = uniqueValues(rows.map((row) => row[xKey]));
  const groups = uniqueValues(rows.map((row) => row[groupKey]));

  const series = groups.map((group) => ({
    type: "bar",
    name: group,
    data: xValues.map((x) => {
      const row = rows.find((entry) => String(entry[xKey]) === x && String(entry[groupKey]) === group);
      return row ? Number(row[yKey] ?? 0) : 0;
    })
  }));

  return chart(
    {
      animation: false,
      title: title ? {text: title, left: "left"} : undefined,
      tooltip: {
        trigger: "axis",
        axisPointer: {type: "shadow"},
        valueFormatter: yPercent ? (value) => `${(Number(value) * 100).toFixed(2)}%` : undefined
      },
      legend: {top: 0},
      grid: {left: 52, right: 24, top: 48, bottom: 48, containLabel: true},
      xAxis: {type: "category", data: xValues},
      yAxis: {
        type: "value",
        axisLabel: yPercent ? {formatter: (value) => `${Math.round(Number(value) * 100)}%`} : undefined
      },
      series
    },
    {height: 300}
  );
}
