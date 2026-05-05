import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { type ClickTimeseriesPointOut } from '../api/types';

type Props = {
  rows: ClickTimeseriesPointOut[];
  days: number;
  onDaysChange: (days: number) => void;
};

export function ClickTimeSeries({ rows, days, onDaysChange }: Props): JSX.Element {
  const grouped = new Map<
    string,
    {
      date: string;
      stream_link: number;
      materials_general: number;
      materials_lecture: number;
      registration_click: number;
    }
  >();
  for (const row of rows) {
    const current = grouped.get(row.date) ?? {
      date: row.date,
      stream_link: 0,
      materials_general: 0,
      materials_lecture: 0,
      registration_click: 0,
    };
    current[row.event_type] = row.count;
    grouped.set(row.date, current);
  }
  const chartData = Array.from(grouped.values()).sort((a, b) => a.date.localeCompare(b.date));

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>Клики по дням</h3>
        <div className="row">
          <button className={days === 7 ? '' : 'secondary'} onClick={() => onDaysChange(7)}>
            7 дней
          </button>
          <button className={days === 30 ? '' : 'secondary'} onClick={() => onDaysChange(30)}>
            30 дней
          </button>
        </div>
      </div>

      {!chartData.length ? (
        <div style={{ marginTop: 8 }}>Нет данных.</div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="stream_link" stroke="#2563eb" strokeWidth={2} />
            <Line type="monotone" dataKey="materials_general" stroke="#16a34a" strokeWidth={2} />
            <Line type="monotone" dataKey="materials_lecture" stroke="#f59e0b" strokeWidth={2} />
            <Line type="monotone" dataKey="registration_click" stroke="#db2777" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
