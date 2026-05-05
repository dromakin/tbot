import { type LectureOverviewSparklinePointOut } from '../api/types';

type Props = {
  points: LectureOverviewSparklinePointOut[];
  width?: number;
  height?: number;
};

export function RowSparkline({ points, width = 120, height = 28 }: Props): JSX.Element {
  if (!points.length) {
    return <span style={{ opacity: 0.7 }}>-</span>;
  }

  const minCount = Math.min(...points.map((point) => point.count));
  const maxCount = Math.max(...points.map((point) => point.count));
  const countRange = Math.max(1, maxCount - minCount);
  const xStep = points.length > 1 ? width / (points.length - 1) : 0;

  const toX = (index: number) => index * xStep;
  const toY = (value: number) => {
    const normalized = (value - minCount) / countRange;
    return height - normalized * height;
  };

  const line = points.map((point, index) => `${toX(index)},${toY(point.count)}`).join(' ');
  const lastPoint = points[points.length - 1];
  const lastX = toX(points.length - 1);
  const lastY = toY(lastPoint.count);

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Clicks sparkline"
    >
      <polyline points={line} fill="none" stroke="currentColor" strokeWidth={1.8} opacity={0.9} />
      <circle cx={lastX} cy={lastY} r={2.4} fill="currentColor" />
    </svg>
  );
}
