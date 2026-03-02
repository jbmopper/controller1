## Analysis subproject

This directory is now an Observable Framework + ECharts app for baseline analytics.
It replaces the previous Marimo notebook workflow.

### Setup

```bash
cd analysis
npm install
```

### Development

```bash
cd analysis
npm run dev
```

`npm run dev` automatically regenerates `src/data/baselines.json` from
`../results/baselines` before launching the Observable dev server.

### Build

```bash
cd analysis
npm run build
```

### Tests

```bash
cd analysis
npm run test
npm run test:smoke
```

### Data location

Source baseline artifacts remain in `../results/baselines`.
The Observable app consumes a generated snapshot in `src/data/baselines.json`.

