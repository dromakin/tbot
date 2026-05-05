import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import { type ClickEventType, type ClickTypeStatsOut } from '../api/types';

type Props = {
  rows: ClickTypeStatsOut[];
};

const EVENT_LABELS: Record<ClickEventType, string> = {
  stream_link: 'Подключение',
  materials_general: 'Основные материалы',
  materials_lecture: 'Доп. материалы',
  registration_click: 'Клик регистрации',
};

const EVENT_COLORS: Record<ClickEventType, string> = {
  stream_link: '#2563eb',
  materials_general: '#16a34a',
  materials_lecture: '#f59e0b',
  registration_click: '#db2777',
};

export function ClickTypeDonut({ rows }: Props): JSX.Element {
  if (!rows.length) {
    return <div className="card">Нет данных для donut графика.</div>;
  }

  const data = rows.map((row) => ({
    name: EVENT_LABELS[row.event_type],
    value: row.total_clicks,
    event_type: row.event_type,
  }));
  const total = rows.reduce((acc, row) => acc + row.total_clicks, 0);

  return (
    <div className="card">
      <h3>Распределение кликов по типам</h3>
      <div style={{ marginBottom: 8 }}>Всего кликов: {total}</div>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={60} outerRadius={95}>
            {data.map((entry) => (
              <Cell key={entry.event_type} fill={EVENT_COLORS[entry.event_type]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
