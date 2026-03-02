import {mkdir, readdir, readFile, writeFile} from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const analysisRoot = path.resolve(__dirname, "..");
const baselinesRoot = path.resolve(analysisRoot, "../results/baselines");
const outputPath = path.resolve(analysisRoot, "src/data/baselines.json");

function isDirectory(entry) {
  return entry?.isDirectory?.() === true;
}

function latestByName(paths) {
  if (paths.length === 0) return null;
  return paths.slice().sort((a, b) => a.localeCompare(b)).at(-1) ?? null;
}

async function readJsonOrNull(filePath) {
  try {
    const raw = await readFile(filePath, "utf8");
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function firstNestedString(value, fallback = "") {
  if (typeof value === "string") return value;
  if (Array.isArray(value) && value.length > 0) return firstNestedString(value[0], fallback);
  return fallback;
}

function extractTaskRecord(sample) {
  const doc = sample?.doc ?? {};
  const taskId = doc.task_id ?? sample.doc_id ?? null;
  if (taskId == null) return null;

  const completion = firstNestedString(sample?.filtered_resps, firstNestedString(sample?.resps, ""));

  return {
    taskId: String(taskId),
    docId: sample?.doc_id ?? null,
    entryPoint: doc?.entry_point ?? null,
    prompt: doc?.prompt ?? "",
    test: doc?.test ?? "",
    target: sample?.target ?? "",
    completion,
    rawCompletion: firstNestedString(sample?.resps, ""),
    passAt1: typeof sample?.["pass@1"] === "number" ? sample["pass@1"] : null,
    promptHash: sample?.prompt_hash ?? null,
    targetHash: sample?.target_hash ?? null,
    docHash: sample?.doc_hash ?? null
  };
}

async function readSamplesJsonl(filePath) {
  const text = await readFile(filePath, "utf8");
  const records = [];
  for (const line of text.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    try {
      const sample = JSON.parse(trimmed);
      const record = extractTaskRecord(sample);
      if (record) records.push(record);
    } catch {
      // Skip malformed rows; source files are expected to be NDJSON.
    }
  }
  return records;
}

function pickConfigSubset(resultsBlob) {
  const config = resultsBlob?.config ?? {};
  return {
    modelDtype: config.model_dtype ?? null,
    device: config.device ?? null,
    modelNumParameters: config.model_num_parameters ?? null,
    modelRevision: config.model_revision ?? null,
    randomSeed: config.random_seed ?? null,
    torchSeed: config.torch_seed ?? null,
    numpySeed: config.numpy_seed ?? null
  };
}

function pickMetrics(resultsBlob) {
  const humaneval = resultsBlob?.results?.humaneval ?? {};
  return {
    passAt1: typeof humaneval?.["pass@1,create_test"] === "number" ? humaneval["pass@1,create_test"] : null,
    passAt1Stderr:
      typeof humaneval?.["pass@1_stderr,create_test"] === "number" ? humaneval["pass@1_stderr,create_test"] : null,
    taskHash: resultsBlob?.task_hashes?.humaneval ?? null
  };
}

async function loadModelRun(runDirPath, modelDirName) {
  const modelDirPath = path.join(runDirPath, modelDirName);
  const modelEntries = await readdir(modelDirPath);

  const resultsFiles = modelEntries
    .filter((name) => /^results_.*\.json$/u.test(name))
    .map((name) => path.join(modelDirPath, name));
  const samplesFiles = modelEntries
    .filter((name) => /^samples_.*\.jsonl$/u.test(name))
    .map((name) => path.join(modelDirPath, name));

  const latestResultsFile = latestByName(resultsFiles);
  const latestSamplesFile = latestByName(samplesFiles);
  if (!latestResultsFile || !latestSamplesFile) return null;

  const resultsBlob = await readJsonOrNull(latestResultsFile);
  if (!resultsBlob) return null;

  const tasks = await readSamplesJsonl(latestSamplesFile);
  const metrics = pickMetrics(resultsBlob);

  return {
    modelId: modelDirName,
    modelName: resultsBlob?.model_name ?? modelDirName,
    resultsFile: path.basename(latestResultsFile),
    samplesFile: path.basename(latestSamplesFile),
    taskCount: tasks.length,
    ...metrics,
    config: pickConfigSubset(resultsBlob),
    tasks
  };
}

async function loadRun(runDirName) {
  const runDirPath = path.join(baselinesRoot, runDirName);
  const runEntries = await readdir(runDirPath, {withFileTypes: true});
  const metadata = await readJsonOrNull(path.join(runDirPath, "run_metadata.json"));
  const modelDirs = runEntries.filter(isDirectory).map((entry) => entry.name).sort((a, b) => a.localeCompare(b));

  const models = [];
  for (const modelDirName of modelDirs) {
    const loaded = await loadModelRun(runDirPath, modelDirName);
    if (loaded) models.push(loaded);
  }

  return {
    runId: runDirName,
    metadata,
    models
  };
}

function buildSummary(runs) {
  const rows = [];
  for (const run of runs) {
    for (const model of run.models) {
      rows.push({
        runId: run.runId,
        modelId: model.modelId,
        passAt1: model.passAt1,
        passAt1Stderr: model.passAt1Stderr,
        taskCount: model.taskCount,
        taskHash: model.taskHash
      });
    }
  }
  return rows;
}

async function main() {
  let runs = [];
  try {
    const entries = await readdir(baselinesRoot, {withFileTypes: true});
    const runDirs = entries.filter(isDirectory).map((entry) => entry.name).sort((a, b) => a.localeCompare(b));
    runs = await Promise.all(runDirs.map((runDir) => loadRun(runDir)));
  } catch {
    runs = [];
  }

  const output = {
    generatedAt: new Date().toISOString(),
    sourceRoot: path.relative(analysisRoot, baselinesRoot),
    runs,
    summary: buildSummary(runs)
  };

  await mkdir(path.dirname(outputPath), {recursive: true});
  await writeFile(outputPath, `${JSON.stringify(output, null, 2)}\n`, "utf8");
  console.log(`Wrote ${outputPath}`);
}

await main();
