import * as echarts from "npm:echarts@5.6.0";

const STATE = new WeakMap();

export function disposeChart(host) {
  const state = STATE.get(host);
  if (!state) return;
  if (state.resizeObserver) state.resizeObserver.disconnect();
  if (state.chart) state.chart.dispose();
  STATE.delete(host);
}

export function chart(option, {height = 320} = {}) {
  const host = document.createElement("div");
  host.style.width = "100%";
  host.style.height = `${height}px`;
  host.style.minHeight = `${height}px`;

  const state = {
    chart: null,
    resizeObserver: null
  };

  const mount = () => {
    if (state.chart || !host.isConnected) return;
    state.chart = echarts.init(host);
    state.chart.setOption(option ?? {});
  };

  state.resizeObserver =
    typeof ResizeObserver === "function"
      ? new ResizeObserver(() => {
          if (state.chart) state.chart.resize();
        })
      : null;

  if (state.resizeObserver) state.resizeObserver.observe(host);
  requestAnimationFrame(mount);

  STATE.set(host, state);

  host.__cleanup = () => {
    disposeChart(host);
  };

  return host;
}

export {echarts};
