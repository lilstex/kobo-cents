// The gradient-lit 3D market render from docs/frontend-architecture/
// 08-design-reference.md: a dimensional bar cluster in this system's
// own brand green and coral, not a borrowed style. Inline SVG, not a
// static image, so it inherits the page's real self-hosted fonts and
// CSS custom properties directly instead of needing its own asset
// pipeline. Pseudo-3D (front/top/side faces per bar, shared light
// direction), not a true rendered 3D scene, matching the "static
// asset, never a live WebGL scene" constraint from the same document.

type Bar = { kind: "up" | "down"; heightFrac: number };

const BARS: Bar[] = [
  { kind: "up", heightFrac: 0.42 },
  { kind: "up", heightFrac: 0.55 },
  { kind: "down", heightFrac: 0.38 },
  { kind: "up", heightFrac: 0.68 },
  { kind: "up", heightFrac: 0.8 },
  { kind: "down", heightFrac: 0.6 },
  { kind: "up", heightFrac: 0.92 },
  { kind: "up", heightFrac: 1.0 },
];

const BAR_W = 34;
const BAR_GAP = 12;
const MAX_H = 220;
const BASE_Y = 340;
const DEPTH: [number, number] = [18, -14];
const START_X = 40;

export function HeroVisual() {
  return (
    <svg viewBox="0 0 480 380" className="h-auto w-full max-w-lg" aria-hidden="true">
      <defs>
        <radialGradient id="hero-glow" cx="60%" cy="55%" r="60%">
          <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.22" />
          <stop offset="45%" stopColor="var(--brand)" stopOpacity="0.08" />
          <stop offset="100%" stopColor="var(--brand)" stopOpacity="0" />
        </radialGradient>
      </defs>

      <rect width="480" height="380" fill="url(#hero-glow)" />
      <line
        x1={START_X - 20}
        y1={BASE_Y}
        x2={START_X + BARS.length * (BAR_W + BAR_GAP) + DEPTH[0] + 10}
        y2={BASE_Y}
        stroke="var(--border)"
        strokeWidth="1"
      />

      {BARS.map((bar, i) => {
        const x = START_X + i * (BAR_W + BAR_GAP);
        const h = MAX_H * bar.heightFrac;
        const yTop = BASE_Y - h;
        const front = bar.kind === "up" ? "var(--brand)" : "var(--down)";
        const [dx, dy] = DEPTH;
        return (
          <g key={i}>
            <polygon
              points={`${x},${BASE_Y} ${x + BAR_W},${BASE_Y} ${x + BAR_W},${yTop} ${x},${yTop}`}
              fill={front}
            />
            <polygon
              points={`${x + BAR_W},${BASE_Y} ${x + BAR_W + dx},${BASE_Y + dy} ${x + BAR_W + dx},${yTop + dy} ${x + BAR_W},${yTop}`}
              fill={front}
              opacity="0.55"
            />
            <polygon
              points={`${x},${yTop} ${x + BAR_W},${yTop} ${x + BAR_W + dx},${yTop + dy} ${x + dx},${yTop + dy}`}
              fill={front}
              opacity="0.8"
            />
          </g>
        );
      })}

      <text
        x={START_X + 6 * (BAR_W + BAR_GAP) - 6}
        y={BASE_Y - MAX_H * 1.0 - 16}
        className="font-mono"
        fontSize="15"
        fill="var(--brand)"
      >
        +11.2%
      </text>
      <text
        x={START_X + 2 * (BAR_W + BAR_GAP) - 6}
        y={BASE_Y - MAX_H * 0.68 - 34}
        className="font-mono"
        fontSize="15"
        fill="var(--down)"
      >
        -4.6%
      </text>
    </svg>
  );
}
