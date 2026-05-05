import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { type LectureHourBucketOut } from '../api/types';

type Props = {
  lectureTitle: string | null;
  rows: LectureHourBucketOut[];
};

export function ClickHourlyDrilldown({ lectureTitle, rows }: Props): JSX.Element {
  if (!lectureTitle) {
    return <div className="card">Выберите лекцию для детализации по часам.</div>;
  }

  const grouped = new Map<
    string,
    {
      bucket_start: string;
      stream_link: number;
      materials_general: number;
      materials_lecture: number;
      registration_click: number;
    }
  >();
  for (const row of rows) {
    const bucket = new Date(row.bucket_start).toLocaleString();
    const current = grouped.get(bucket) ?? {
      bucket_start: bucket,
      stream_link: 0,
      materials_general: 0,
      materials_lecture: 0,
      registration_click: 0,
    };
    current[row.event_type] = row.count;
    grouped.set(bucket, current);
  }
  const chartData = Array.from(grouped.values());

  return (
    <div className="card">
      <h3>Drill-down по часам: {lectureTitle}</h3>
      {!chartData.length ? (
        <div>По выбранной лекции кликов пока нет.</div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="bucket_start" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="stream_link" stackId="clicks" fill="#2563eb" />
            <Bar dataKey="materials_general" stackId="clicks" fill="#16a34a" />
            <Bar dataKey="materials_lecture" stackId="clicks" fill="#f59e0b" />
            <Bar dataKey="registration_click" stackId="clicks" fill="#db2777" />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
