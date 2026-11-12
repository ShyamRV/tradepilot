"use client";

type Series = number[];

function normalize(values: Series, height: number, pad = 8) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return values.map((value, index) => {
    const x = (index / Math.max(values.length - 1, 1)) * 100;
    const y = pad + ((max - value) / span) * (height - pad * 2);
    return { x, y };
  });
}

function pathFrom(points: Array<{ x: number; y: number }>, smooth = true) {
  if (!points.length) return "";
  if (!smooth) {
    return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  }
  return points
    .map((point, index) => {
      if (index === 0) return `M ${point.x} ${point.y}`;
      const prev = points[index - 1];
      const cx = (prev.x + point.x) / 2;
      return `C ${cx} ${prev.y}, ${cx} ${point.y}, ${point.x} ${point.y}`;
    })
    .join(" ");
}

export function Sparkline({
  values,
  tone = "cyan",
  height = 42
}: {
  values: Series;
  tone?: "cyan" | "amber" | "magenta" | "lime";
  height?: number;
}) {
  const points = normalize(values, height);
  return (
    <svg className={`sparkline tone-${tone}`} viewBox={`0 0 100 ${height}`} preserveAspectRatio="none" aria-hidden="true">
      <path d={pathFrom(points)} fill="none" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

export function BarLineChart({
  bars,
  line,
  title,
  subtitle,
  medianAt
}: {
  bars: Series;
  line: Series;
  title: string;
  subtitle: string;
  medianAt?: number;
}) {
  const height = 160;
  const maxBar = Math.max(...bars, 1);
  const linePoints = normalize(line, height, 16);

  return (
    <section className="vizPanel">
      <header className="vizHeader">
        <div>
          <p className="vizEyebrow">{subtitle}</p>
          <h2>{title}</h2>
        </div>
      </header>
      <svg className="barLineChart" viewBox={`0 0 100 ${height}`} role="img" aria-label={title}>
        {[0.2, 0.4, 0.6, 0.8].map((ratio) => (
          <line key={ratio} className="gridLine" x1="0" x2="100" y1={height * ratio} y2={height * ratio} />
        ))}
        {bars.map((value, index) => {
          const width = 100 / bars.length;
          const barHeight = (value / maxBar) * (height - 20);
          const x = index * width + width * 0.2;
          return (
            <rect
              key={index}
              className="chartBar"
              x={x}
              y={height - barHeight}
              width={width * 0.55}
              height={barHeight}
              rx="0.8"
            />
          );
        })}
        {typeof medianAt === "number" && (
          <line className="medianLine" x1={medianAt} x2={medianAt} y1="8" y2={height - 4} />
        )}
        <path className="chartLine magenta" d={pathFrom(linePoints)} fill="none" vectorEffect="non-scaling-stroke" />
      </svg>
    </section>
  );
}

export function MultiLineChart({
  series,
  title,
  metrics
}: {
  series: Array<{ values: Series; tone: "cyan" | "magenta" | "lime" | "amber" }>;
  title: string;
  metrics: Array<{ label: string; value: string; tone: string }>;
}) {
  const height = 140;
  return (
    <section className="vizPanel">
      <header className="vizHeader">
        <div>
          <p className="vizEyebrow">{title}</p>
          <div className="heroMetrics">
            {metrics.map((metric) => (
              <div key={metric.label} className={`heroMetric tone-${metric.tone}`}>
                <strong>{metric.value}</strong>
                <span>{metric.label}</span>
              </div>
            ))}
          </div>
        </div>
      </header>
      <svg className="multiLineChart" viewBox={`0 0 100 ${height}`} role="img" aria-label={title}>
        {[0.25, 0.5, 0.75].map((ratio) => (
          <line key={ratio} className="gridLine" x1="0" x2="100" y1={height * ratio} y2={height * ratio} />
        ))}
        {series.map((item, index) => (
          <path
            key={index}
            className={`chartLine ${item.tone}`}
            d={pathFrom(normalize(item.values, height, 12))}
            fill="none"
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>
    </section>
  );
}

export function GhostCurveChart({
  title,
  values,
  ghosts
}: {
  title: string;
  values: Series;
  ghosts: Series[];
}) {
  const height = 150;
  return (
    <section className="vizPanel">
      <header className="vizHeader">
        <div>
          <p className="vizEyebrow">Signal behaviour</p>
          <h2>{title}</h2>
        </div>
      </header>
      <svg className="ghostChart" viewBox={`0 0 100 ${height}`} role="img" aria-label={title}>
        {ghosts.map((ghost, index) => (
          <path
            key={index}
            className="ghostLine"
            d={pathFrom(normalize(ghost, height, 14))}
            fill="none"
            vectorEffect="non-scaling-stroke"
          />
        ))}
        <path
          className="chartLine amber"
          d={pathFrom(normalize(values, height, 14))}
          fill="none"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    </section>
  );
}
