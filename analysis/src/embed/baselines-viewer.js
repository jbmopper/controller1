import {FileAttachment} from "observablehq:stdlib";
import {groupedBarPlot} from "../components/echart-plot.js";
import {
  buildComparison,
  createBaselineIndex,
  filterComparisonTasks,
  getDefaultSelection,
  getModelOptions,
  modelSummaryRows,
  unifiedDiff
} from "./baselines-data.js";

function clearNode(node) {
  while (node.firstChild) {
    const child = node.firstChild;
    if (typeof child.__cleanup === "function") {
      child.__cleanup();
    }
    node.removeChild(child);
  }
}

function el(tag, className = null, text = null) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

function labeledSelect(label, options, value = null) {
  const wrap = el("label", "baseline-label");
  const title = el("span", "baseline-label-title", label);
  const select = el("select", "baseline-select");
  for (const optionValue of options) {
    const option = el("option");
    option.value = optionValue;
    option.textContent = optionValue;
    select.append(option);
  }
  if (value != null) select.value = value;
  wrap.append(title, select);
  return {wrap, select};
}

function labeledCheckbox(label, checked = false) {
  const wrap = el("label", "baseline-checkbox");
  const input = el("input");
  input.type = "checkbox";
  input.checked = checked;
  wrap.append(input, document.createTextNode(label));
  return {wrap, input};
}

function issueList(runLabel, issues) {
  const block = el("div", "issue-list");
  block.append(el("h4", null, runLabel));
  if (!issues.length) {
    block.append(el("div", "issue-none", "No lint issues."));
    return block;
  }
  const list = el("ul");
  for (const issue of issues) {
    const item = el("li");
    item.textContent = `${issue.level.toUpperCase()}: ${issue.message}`;
    list.append(item);
  }
  block.append(list);
  return block;
}

function renderStyle(root) {
  const style = el("style");
  style.textContent = `
    .baseline-root { display: grid; gap: 1rem; }
    .baseline-controls { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: end; }
    .baseline-label { display: grid; gap: 0.35rem; min-width: 15rem; }
    .baseline-label-title { font-size: 0.85rem; opacity: 0.8; }
    .baseline-select { padding: 0.4rem 0.5rem; }
    .baseline-checkboxes { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; }
    .baseline-checkbox { display: inline-flex; gap: 0.4rem; align-items: center; }
    .baseline-grid { display: grid; gap: 1rem; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .baseline-card { border: 1px solid var(--theme-foreground-fainter, #444); border-radius: 8px; padding: 0.75rem; }
    .baseline-card h3 { margin: 0 0 0.45rem 0; font-size: 1rem; }
    .baseline-headline { margin: 0; padding-left: 1.1rem; }
    .baseline-compat { font-size: 0.9rem; }
    .baseline-task-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    .baseline-task-table th, .baseline-task-table td { text-align: left; border-bottom: 1px solid var(--theme-foreground-fainter, #444); padding: 0.4rem; vertical-align: top; }
    .baseline-task-table button { cursor: pointer; text-align: left; width: 100%; padding: 0.2rem 0; background: none; border: none; color: inherit; font: inherit; }
    .baseline-code-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
    .baseline-code-block { max-height: 26rem; overflow: auto; border: 1px solid var(--theme-foreground-fainter, #444); border-radius: 6px; margin: 0; padding: 0.5rem; font-size: 0.82rem; }
    .baseline-diff-block { max-height: 22rem; overflow: auto; border: 1px solid var(--theme-foreground-fainter, #444); border-radius: 6px; margin: 0; padding: 0.5rem; font-size: 0.78rem; }
    .baseline-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
    .issue-list ul { margin: 0; padding-left: 1.1rem; }
    .issue-none { opacity: 0.8; }
  `;
  root.append(style);
}

function passLabel(value) {
  if (typeof value !== "number") return "—";
  return `${(value * 100).toFixed(1)}%`;
}

export async function renderBaselinesViewer({dataset = null} = {}) {
  const loaded = dataset ?? (await FileAttachment("../data/baselines.json").json());
  const index = createBaselineIndex(loaded);

  const root = el("section", "baseline-root");
  renderStyle(root);

  if (index.runIds.length === 0) {
    root.append(el("p", null, "No baseline runs found. Run `npm run sync:baselines` after generating baseline outputs."));
    return root;
  }

  const state = {
    ...getDefaultSelection(index),
    selectedTaskId: null,
    lintFailOnly: false,
    passMismatchOnly: false,
    changedOnly: false
  };

  const controls = el("div", "baseline-controls");
  const runAInput = labeledSelect("Run A", index.runIds, state.runA);
  const runBInput = labeledSelect("Run B", index.runIds, state.runB);
  const modelInput = labeledSelect("Model", getModelOptions(index, state.runA, state.runB), state.modelId);

  const checks = el("div", "baseline-checkboxes");
  const lintCheck = labeledCheckbox("Lint issues only", false);
  const passCheck = labeledCheckbox("Pass mismatch only", false);
  const changeCheck = labeledCheckbox("Changed output only", false);
  checks.append(lintCheck.wrap, passCheck.wrap, changeCheck.wrap);
  controls.append(runAInput.wrap, runBInput.wrap, modelInput.wrap, checks);

  const compatibility = el("div", "baseline-card baseline-compat");
  const headline = el("div", "baseline-card");
  const charts = el("div", "baseline-grid");
  const chartSummary = el("div", "baseline-card");
  const chartCompare = el("div", "baseline-card");
  charts.append(chartSummary, chartCompare);

  const taskCard = el("div", "baseline-card");
  const detailCard = el("div", "baseline-card");

  root.append(controls, compatibility, headline, charts, taskCard, detailCard);

  const refreshModelOptions = () => {
    const options = getModelOptions(index, state.runA, state.runB);
    clearNode(modelInput.select);
    for (const optionValue of options) {
      const option = el("option");
      option.value = optionValue;
      option.textContent = optionValue;
      modelInput.select.append(option);
    }
    if (!options.includes(state.modelId)) {
      state.modelId = options[0] ?? null;
    }
    if (state.modelId != null) modelInput.select.value = state.modelId;
  };

  const renderCharts = (comparison, filteredTasks) => {
    clearNode(chartSummary);
    clearNode(chartCompare);
    chartSummary.append(el("h3", null, "Pass@1 by run/model"));
    chartCompare.append(el("h3", null, "Disagreements and lint issues"));

    const summaryRows = modelSummaryRows(index);
    if (summaryRows.length > 0) {
      chartSummary.append(
        groupedBarPlot(summaryRows, {
          title: "Pass@1",
          xKey: "runId",
          groupKey: "modelId",
          yKey: "passAt1",
          yPercent: true
        })
      );
    } else {
      chartSummary.append(el("p", null, "No summary rows available."));
    }

    const compareRows = [
      {
        metric: "Pass mismatches",
        run: `${comparison.runA} vs ${comparison.runB}`,
        value: filteredTasks.filter((task) => task.passMismatch).length
      },
      {
        metric: "Changed outputs",
        run: `${comparison.runA} vs ${comparison.runB}`,
        value: filteredTasks.filter((task) => task.changedOutput).length
      },
      {
        metric: "Linted tasks",
        run: `${comparison.runA} vs ${comparison.runB}`,
        value: filteredTasks.filter(
          (task) =>
            task.lintCountA.errorCount + task.lintCountA.warningCount + task.lintCountB.errorCount + task.lintCountB.warningCount >
            0
        ).length
      }
    ];

    chartCompare.append(
      groupedBarPlot(compareRows, {
        title: "Task comparison counts",
        xKey: "metric",
        groupKey: "run",
        yKey: "value",
        yPercent: false
      })
    );
  };

  const renderTaskTable = (tasks) => {
    clearNode(taskCard);
    taskCard.append(el("h3", null, `Tasks (${tasks.length})`));
    if (tasks.length === 0) {
      taskCard.append(el("p", null, "No tasks after filters."));
      return;
    }

    const table = el("table", "baseline-task-table");
    table.innerHTML = `
      <thead>
        <tr>
          <th>Task</th>
          <th>A pass</th>
          <th>B pass</th>
          <th>Changed</th>
          <th>Lint (A/B)</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;
    const tbody = table.querySelector("tbody");
    for (const task of tasks) {
      const row = el("tr");
      const taskCell = el("td");
      const button = el("button", null, task.taskId);
      button.addEventListener("click", () => {
        state.selectedTaskId = task.taskId;
        refresh();
      });
      taskCell.append(button);

      const lintA = task.lintCountA.errorCount + task.lintCountA.warningCount;
      const lintB = task.lintCountB.errorCount + task.lintCountB.warningCount;

      row.append(
        taskCell,
        el("td", null, String(task.a?.passAt1 ?? "—")),
        el("td", null, String(task.b?.passAt1 ?? "—")),
        el("td", null, task.changedOutput ? "yes" : "no"),
        el("td", null, `${lintA}/${lintB}`)
      );
      tbody.append(row);
    }

    taskCard.append(table);
  };

  const renderDetails = (comparison, tasks) => {
    clearNode(detailCard);
    detailCard.append(el("h3", null, "Selected task details"));
    if (tasks.length === 0) {
      detailCard.append(el("p", null, "No task available."));
      return;
    }

    const selected = tasks.find((task) => task.taskId === state.selectedTaskId) ?? tasks[0];
    state.selectedTaskId = selected.taskId;

    const promptBlock = el("pre", "baseline-code-block baseline-mono", selected.a?.prompt ?? "");
    const testBlock = el("pre", "baseline-code-block baseline-mono", selected.a?.test ?? "");
    const runACode = el("pre", "baseline-code-block baseline-mono", selected.a?.completion ?? "");
    const runBCode = el("pre", "baseline-code-block baseline-mono", selected.b?.completion ?? "");
    const diff = el(
      "pre",
      "baseline-diff-block baseline-mono",
      unifiedDiff(selected.a?.completion ?? "", selected.b?.completion ?? "", comparison.runA, comparison.runB) ||
        "(no differences)"
    );

    const meta = el("ul", "baseline-headline");
    meta.append(
      el("li", null, `Task: ${selected.taskId}`),
      el("li", null, `Run A pass@1: ${selected.a?.passAt1 ?? "—"} (${comparison.runA})`),
      el("li", null, `Run B pass@1: ${selected.b?.passAt1 ?? "—"} (${comparison.runB})`),
      el("li", null, `Prompt hash: ${selected.promptHashStatus}`),
      el("li", null, `Target hash: ${selected.targetHashStatus}`)
    );

    const codeGrid = el("div", "baseline-code-grid");
    const codeA = el("div");
    const codeB = el("div");
    codeA.append(el("h4", null, `Run A completion (${comparison.runA})`), runACode);
    codeB.append(el("h4", null, `Run B completion (${comparison.runB})`), runBCode);
    codeGrid.append(codeA, codeB);

    const lintGrid = el("div", "baseline-code-grid");
    lintGrid.append(issueList(`Lint A (${comparison.runA})`, selected.lintA), issueList(`Lint B (${comparison.runB})`, selected.lintB));

    detailCard.append(
      meta,
      el("h4", null, "Prompt"),
      promptBlock,
      el("h4", null, "Task test harness"),
      testBlock,
      el("h4", null, "Side-by-side completions"),
      codeGrid,
      el("h4", null, "Unified diff"),
      diff,
      el("h4", null, "Lint"),
      lintGrid
    );
  };

  const refresh = () => {
    const comparison = buildComparison(index, {
      runA: state.runA,
      runB: state.runB,
      modelId: state.modelId
    });

    const filtered = filterComparisonTasks(comparison.tasks, {
      lintFailOnly: state.lintFailOnly,
      passMismatchOnly: state.passMismatchOnly,
      changedOnly: state.changedOnly
    });

    clearNode(compatibility);
    compatibility.append(el("h3", null, "Compatibility checks"));
    compatibility.append(
      el("div", null, `Task hash compatibility: ${comparison.compatibility.taskHash}`),
      el("div", null, `Task rows in intersection: ${comparison.tasks.length}`),
      el("div", null, `Visible after filters: ${filtered.length}`)
    );

    clearNode(headline);
    headline.append(el("h3", null, "Headline"));
    const list = el("ul", "baseline-headline");
    list.append(
      el("li", null, `Run A (${comparison.runA}) pass@1: ${passLabel(comparison.modelA?.passAt1)}`),
      el("li", null, `Run B (${comparison.runB}) pass@1: ${passLabel(comparison.modelB?.passAt1)}`),
      el("li", null, `Delta (A - B): ${passLabel((comparison.modelA?.passAt1 ?? 0) - (comparison.modelB?.passAt1 ?? 0))}`)
    );
    headline.append(list);

    renderCharts(comparison, filtered);
    renderTaskTable(filtered);
    renderDetails(comparison, filtered);
  };

  runAInput.select.addEventListener("change", () => {
    state.runA = runAInput.select.value;
    refreshModelOptions();
    refresh();
  });
  runBInput.select.addEventListener("change", () => {
    state.runB = runBInput.select.value;
    refreshModelOptions();
    refresh();
  });
  modelInput.select.addEventListener("change", () => {
    state.modelId = modelInput.select.value;
    refresh();
  });
  lintCheck.input.addEventListener("change", () => {
    state.lintFailOnly = lintCheck.input.checked;
    refresh();
  });
  passCheck.input.addEventListener("change", () => {
    state.passMismatchOnly = passCheck.input.checked;
    refresh();
  });
  changeCheck.input.addEventListener("change", () => {
    state.changedOnly = changeCheck.input.checked;
    refresh();
  });

  refreshModelOptions();
  refresh();

  return root;
}
