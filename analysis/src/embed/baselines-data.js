import {createTwoFilesPatch} from "diff";

function makeRunModelKey(runId, modelId) {
  return `${runId}::${modelId}`;
}

function sortRunIds(runIds) {
  return runIds.slice().sort((a, b) => a.localeCompare(b));
}

function sortTaskIds(taskIds) {
  return taskIds.slice().sort((a, b) => a.localeCompare(b, "en", {numeric: true}));
}

export function createBaselineIndex(dataset) {
  const runs = Array.isArray(dataset?.runs) ? dataset.runs : [];
  const runIds = sortRunIds(runs.map((run) => run.runId).filter(Boolean));
  const runsById = new Map(runs.map((run) => [run.runId, run]));
  const modelsByRun = new Map();
  const runModelMap = new Map();

  for (const run of runs) {
    const modelIds = (run.models ?? []).map((model) => model.modelId).filter(Boolean).sort((a, b) => a.localeCompare(b));
    modelsByRun.set(run.runId, modelIds);
    for (const model of run.models ?? []) {
      runModelMap.set(makeRunModelKey(run.runId, model.modelId), model);
    }
  }

  return {
    runIds,
    runsById,
    modelsByRun,
    runModelMap,
    summary: Array.isArray(dataset?.summary) ? dataset.summary : []
  };
}

export function getDefaultSelection(index) {
  const runIds = index?.runIds ?? [];
  const runA = runIds.at(-1) ?? null;
  const runB = runIds.at(-2) ?? runA;
  const modelOptions = getModelOptions(index, runA, runB);
  return {
    runA,
    runB,
    modelId: modelOptions[0] ?? null
  };
}

export function getModelOptions(index, runA, runB) {
  const modelsA = new Set(index?.modelsByRun?.get(runA) ?? []);
  const modelsB = new Set(index?.modelsByRun?.get(runB) ?? []);
  if (modelsA.size === 0) return Array.from(modelsB).sort((a, b) => a.localeCompare(b));
  if (modelsB.size === 0) return Array.from(modelsA).sort((a, b) => a.localeCompare(b));
  return Array.from(modelsA).filter((modelId) => modelsB.has(modelId)).sort((a, b) => a.localeCompare(b));
}

function readModel(index, runId, modelId) {
  return index?.runModelMap?.get(makeRunModelKey(runId, modelId)) ?? null;
}

function taskMap(model) {
  const map = new Map();
  for (const task of model?.tasks ?? []) {
    if (!task?.taskId) continue;
    map.set(task.taskId, task);
  }
  return map;
}

function compareHash(a, b) {
  if (!a || !b) return "missing";
  return a === b ? "match" : "mismatch";
}

function isProbablyBalancedPython(code) {
  const pairs = new Map([
    ["(", ")"],
    ["[", "]"],
    ["{", "}"]
  ]);
  const openings = new Set(pairs.keys());
  const closings = new Set(pairs.values());
  const stack = [];

  let inSingle = false;
  let inDouble = false;
  let escaped = false;

  for (const ch of code) {
    if (escaped) {
      escaped = false;
      continue;
    }
    if (ch === "\\") {
      escaped = true;
      continue;
    }
    if (!inDouble && ch === "'") {
      inSingle = !inSingle;
      continue;
    }
    if (!inSingle && ch === "\"") {
      inDouble = !inDouble;
      continue;
    }
    if (inSingle || inDouble) continue;
    if (openings.has(ch)) {
      stack.push(ch);
      continue;
    }
    if (closings.has(ch)) {
      const last = stack.pop();
      if (!last || pairs.get(last) !== ch) return false;
    }
  }
  return stack.length === 0 && !inSingle && !inDouble;
}

function importPresent(code, moduleName) {
  const directImport = new RegExp(`(^|\\n)\\s*import\\s+${moduleName}(\\s|\\n|$)`, "m");
  const fromImport = new RegExp(`(^|\\n)\\s*from\\s+${moduleName}\\s+import\\s+`, "m");
  return directImport.test(code) || fromImport.test(code);
}

export function lintPythonResponse(code, entryPoint = null) {
  const text = String(code ?? "");
  const issues = [];
  if (!text.trim()) {
    issues.push({level: "error", code: "EMPTY", message: "Completion is empty."});
    return issues;
  }

  if (entryPoint && !new RegExp(`\\bdef\\s+${entryPoint}\\s*\\(`).test(text)) {
    issues.push({
      level: "error",
      code: "MISSING_ENTRYPOINT",
      message: `Missing function definition for expected entry point "${entryPoint}".`
    });
  }

  if (!isProbablyBalancedPython(text)) {
    issues.push({
      level: "error",
      code: "UNBALANCED_DELIMITERS",
      message: "Bracket/quote structure appears unbalanced."
    });
  }

  if (/\bTODO\b/i.test(text) || /\bNotImplementedError\b/.test(text)) {
    issues.push({
      level: "warn",
      code: "PLACEHOLDER",
      message: "Contains TODO or NotImplementedError placeholder text."
    });
  }

  if (/^\s*pass\s*$/m.test(text)) {
    issues.push({
      level: "warn",
      code: "PASS_PLACEHOLDER",
      message: "Contains bare `pass` statements."
    });
  }

  const importsToCheck = ["decimal", "math", "re", "itertools", "collections"];
  for (const moduleName of importsToCheck) {
    const usesModule = new RegExp(`\\b${moduleName}\\.`).test(text);
    if (usesModule && !importPresent(text, moduleName)) {
      issues.push({
        level: "warn",
        code: "POTENTIAL_UNDEFINED_IMPORT",
        message: `Uses ${moduleName}.* without an explicit import.`
      });
    }
  }

  const longLines = text.split("\n").filter((line) => line.length > 120).length;
  if (longLines > 0) {
    issues.push({
      level: "warn",
      code: "LONG_LINES",
      message: `Contains ${longLines} lines longer than 120 characters.`
    });
  }

  return issues;
}

function lintSummary(issues) {
  return {
    errorCount: issues.filter((issue) => issue.level === "error").length,
    warningCount: issues.filter((issue) => issue.level === "warn").length
  };
}

export function unifiedDiff(aCode, bCode, runA, runB) {
  const patch = createTwoFilesPatch(
    `A:${runA}`,
    `B:${runB}`,
    String(aCode ?? ""),
    String(bCode ?? ""),
    "",
    "",
    {context: 3}
  );
  return patch.trim();
}

export function buildComparison(index, {runA, runB, modelId}) {
  const modelA = readModel(index, runA, modelId);
  const modelB = readModel(index, runB, modelId);
  if (!modelA || !modelB) {
    return {
      runA,
      runB,
      modelId,
      modelA,
      modelB,
      tasks: [],
      taskIds: [],
      compatibility: {
        taskHash: compareHash(modelA?.taskHash, modelB?.taskHash)
      }
    };
  }

  const aMap = taskMap(modelA);
  const bMap = taskMap(modelB);
  const taskIds = sortTaskIds(Array.from(aMap.keys()).filter((taskId) => bMap.has(taskId)));

  const tasks = taskIds.map((taskId) => {
    const a = aMap.get(taskId);
    const b = bMap.get(taskId);
    const lintA = lintPythonResponse(a?.completion, a?.entryPoint);
    const lintB = lintPythonResponse(b?.completion, b?.entryPoint);
    const lintCountA = lintSummary(lintA);
    const lintCountB = lintSummary(lintB);
    const changedOutput = String(a?.completion ?? "") !== String(b?.completion ?? "");
    const passMismatch = Number(a?.passAt1 ?? NaN) !== Number(b?.passAt1 ?? NaN);
    const promptHashStatus = compareHash(a?.promptHash, b?.promptHash);
    const targetHashStatus = compareHash(a?.targetHash, b?.targetHash);

    return {
      taskId,
      a,
      b,
      changedOutput,
      passMismatch,
      promptHashStatus,
      targetHashStatus,
      lintA,
      lintB,
      lintCountA,
      lintCountB
    };
  });

  return {
    runA,
    runB,
    modelId,
    modelA,
    modelB,
    tasks,
    taskIds,
    compatibility: {
      taskHash: compareHash(modelA?.taskHash, modelB?.taskHash)
    }
  };
}

export function filterComparisonTasks(tasks, {lintFailOnly = false, passMismatchOnly = false, changedOnly = false} = {}) {
  return tasks.filter((task) => {
    if (lintFailOnly) {
      const hasLint =
        task?.lintCountA?.errorCount > 0 ||
        task?.lintCountA?.warningCount > 0 ||
        task?.lintCountB?.errorCount > 0 ||
        task?.lintCountB?.warningCount > 0;
      if (!hasLint) return false;
    }
    if (passMismatchOnly && !task?.passMismatch) return false;
    if (changedOnly && !task?.changedOutput) return false;
    return true;
  });
}

export function modelSummaryRows(index) {
  return (index?.summary ?? []).map((row) => ({
    runId: row.runId,
    modelId: row.modelId,
    passAt1: typeof row.passAt1 === "number" ? row.passAt1 : null,
    taskCount: row.taskCount ?? null
  }));
}
