"use client";

import {
  AreaSeries,
  CrosshairMode,
  type IChartApi,
  type UTCTimestamp,
  createChart,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

type PricePoint = { recorded_at: string; price: number };

// The six styling rules from docs/frontend-architecture/01.md, kept
// literal (values taken straight from the design reference, not
// approximated): conditional color, flat 8% fill opacity (not a
// gradient, lightweight-charts' AreaSeries top/bottom colors are set
// to the exact same value here for that reason), horizontal-only
// hairline grid, one emphasized endpoint dot, JetBrains Mono axis
// labels, static on load.
export function PriceChart({ points }: { points: PricePoint[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current || points.length === 0) return;

    const rootStyles = getComputedStyle(document.documentElement);
    const brand = rootStyles.getPropertyValue("--brand").trim();
    const down = rootStyles.getPropertyValue("--down").trim();
    const border = rootStyles.getPropertyValue("--border").trim();
    const muted = rootStyles.getPropertyValue("--muted").trim();

    const up = points[points.length - 1].price >= points[0].price;
    const color = up ? brand : down;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 160,
      layout: {
        background: { color: "transparent" },
        textColor: muted,
        fontFamily: "var(--font-jetbrains-mono), ui-monospace, monospace",
        fontSize: 10,
        // Left at its default (visible): lightweight-charts' license
        // requires either this attribution or a manual equivalent
        // elsewhere on the page, and no manual attribution exists
        // here yet.
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: border },
      },
      rightPriceScale: { borderVisible: false },
      timeScale: { borderVisible: false, timeVisible: true },
      crosshair: { mode: CrosshairMode.Normal },
      handleScroll: false,
      handleScale: false,
    });
    chartRef.current = chart;

    const series = chart.addSeries(AreaSeries, {
      lineColor: color,
      topColor: `${color}14`, // ~8% alpha, flat, no gradient
      bottomColor: `${color}14`,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });

    // Real seconds-since-epoch, not a day-truncated date string: this
    // product refreshes two to three times a day, per 01_product.md,
    // so same-calendar-day points are the normal case, not an edge
    // case, and lightweight-charts requires strictly ascending,
    // non-duplicate time values. Two cycles landing in the exact same
    // second (only plausible in a fast test run, not production) are
    // still de-duplicated defensively, keeping the later value.
    const byTimestamp = new Map<number, number>();
    for (const point of points) {
      byTimestamp.set(Math.floor(new Date(point.recorded_at).getTime() / 1000), point.price);
    }
    const data = [...byTimestamp.entries()]
      .sort(([a], [b]) => a - b)
      .map(([time, value]) => ({ time: time as UTCTimestamp, value }));
    series.setData(data);

    // The one deliberate emphasis point, per 01.md: a single filled
    // dot at the latest price, not a marker library, a second series
    // holding just the last point.
    const endpoint = chart.addSeries(AreaSeries, {
      // lineVisible: false hides the connecting line (lineWidth has
      // no 0 option, only 1-4) while keeping lineColor real, since
      // the point marker's fill follows it.
      lineColor: color,
      lineVisible: false,
      topColor: "transparent",
      bottomColor: "transparent",
      pointMarkersVisible: true,
      pointMarkersRadius: 4,
      lastValueVisible: false,
      priceLineVisible: false,
      crosshairMarkerVisible: false,
    });
    endpoint.setData([data[data.length - 1]]);

    chart.timeScale().fitContent();
    // Static on load, per 01.md: no animated draw-in either way,
    // lightweight-charts never animates initial setData, this branch
    // exists only to document that prefers-reduced-motion is already
    // satisfied, not to add a fade that would then need to respect it.
    void prefersReducedMotion;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
      chartRef.current = null;
    };
  }, [points]);

  if (points.length === 0) {
    return (
      <p className="py-8 text-center text-xs text-muted">
        Not enough refresh cycles yet to chart a trend.
      </p>
    );
  }

  return <div ref={containerRef} className="w-full" />;
}
