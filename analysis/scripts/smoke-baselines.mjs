import {readFile} from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {buildComparison, createBaselineIndex, getDefaultSelection} from "../src/embed/baselines-data.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const analysisRoot = path.resolve(__dirname, "..");
const datasetPath = path.join(analysisRoot, "src/data/baselines.json");

const raw = await readFile(datasetPath, "utf8");
const dataset = JSON.parse(raw);
const index = createBaselineIndex(dataset);

if (index.runIds.length < 1) {
  throw new Error("No runs found in baselines dataset.");
}

const selection = getDefaultSelection(index);
if (!selection.runA || !selection.runB || !selection.modelId) {
  throw new Error("Could not derive default run/model selection.");
}

const comparison = buildComparison(index, selection);
if (comparison.tasks.length < 1) {
  throw new Error("Comparison produced zero tasks.");
}

console.log(
  [
    `runs=${index.runIds.length}`,
    `defaultRunA=${selection.runA}`,
    `defaultRunB=${selection.runB}`,
    `model=${selection.modelId}`,
    `tasks=${comparison.tasks.length}`
  ].join(" ")
);
