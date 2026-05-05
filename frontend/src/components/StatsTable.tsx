import { type StatsRowOut } from '../api/types';

type Props = {
  rows: StatsRowOut[];
};

export function StatsTable({ rows }: Props): JSX.Element {
  if (!rows.length) {
    return <div className="card">Нет данных для отображения.</div>;
  }

  return (
    <div className="card">
      <table className="table">
        <thead>
          <tr>
            <th>Лекция</th>
            <th>Регистраций</th>
            <th>Уникальных кликов</th>
            <th>Всего кликов</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.lecture_id}>
              <td>
                №{row.lecture_number} {row.lecture_title}
              </td>
              <td>{row.registrations_count}</td>
              <td>{row.unique_clicks_count}</td>
              <td>{row.total_clicks_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
