import {readFile} from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {describe, expect, it} from "vitest";
import {
  buildComparison,
  createBaselineIndex,
  filterComparisonTasks,
  getDefaultSelection,
  lintPythonResponse
} from "../src/embed/baselines-data.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const analysisRoot = path.resolve(__dirname, "..");
const datasetPath = path.join(analysisRoot, "src/data/baselines.json");
const baselinesRoot = path.resolve(analysisRoot, "../results/baselines");

async function loadDataset() {
  const raw = await readFile(datasetPath, "utf8");
  return JSON.parse(raw);
}

function nestedFirst(value, fallback = "") {
  if (typeof value === "string") return value;
  if (Array.isArray(value) && value.length > 0) return nestedFirst(value[0], fallback);
  return fallback;
}

describe("baselines dataset parity", () => {
  it("keeps pass@1 parity with latest results files", async () => {
    const dataset = await loadDataset();
    for (const run of dataset.runs) {
      for (const model of run.models) {
        const resultsPath = path.join(baselinesRoot, run.runId, model.modelId, model.resultsFile);
        const rawResults = await readFile(resultsPath, "utf8");
        const parsed = JSON.parse(rawResults);
        const expected = parsed?.results?.humaneval?.["pass@1,create_test"] ?? null;
        expect(model.passAt1).toBe(expected);
      }
    }
  });

  it("preserves prompt and completion from sample rows", async () => {
    const dataset = await loadDataset();
    const run = dataset.runs[0];
    const model = run.models[0];
    const sourcePath = path.join(baselinesRoot, run.runId, model.modelId, model.samplesFile);
    const firstLine = (await readFile(sourcePath, "utf8")).split("\n").find((line) => line.trim().length > 0);
    const sample = JSON.parse(firstLine);

    const taskId = sample.doc.task_id;
    const task = model.tasks.find((entry) => entry.taskId === taskId);
    expect(task).toBeDefined();
    expect(task.prompt).toBe(sample.doc.prompt);
    expect(task.completion).toBe(nestedFirst(sample.filtered_resps, nestedFirst(sample.resps, "")));
  });
});

describe("comparison selector flow", () => {
  it("builds default comparison and supports filters", async () => {
    const dataset = await loadDataset();
    const index = createBaselineIndex(dataset);
    const selection = getDefaultSelection(index);
    const comparison = buildComparison(index, selection);
    expect(comparison.tasks.length).toBeGreaterThan(0);

    const changed = filterComparisonTasks(comparison.tasks, {changedOnly: true});
    expect(changed.length).toBeLessThanOrEqual(comparison.tasks.length);

    const passMismatch = filterComparisonTasks(comparison.tasks, {passMismatchOnly: true});
    expect(passMismatch.length).toBeLessThanOrEqual(comparison.tasks.length);
  });
});

describe("ui lint checks", () => {
  it("flags missing entrypoint and placeholders", () => {
    const issues = lintPythonResponse("def helper():\n    pass\n# TODO", "target_func");
    const issueCodes = new Set(issues.map((issue) => issue.code));
    expect(issueCodes.has("MISSING_ENTRYPOINT")).toBe(true);
    expect(issueCodes.has("PASS_PLACEHOLDER")).toBe(true);
    expect(issueCodes.has("PLACEHOLDER")).toBe(true);
  });
});
