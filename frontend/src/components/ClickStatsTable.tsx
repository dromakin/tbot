import { type ClickTypeStatsOut, type LectureClickStatsOut } from '../api/types';

type Props = {
  byType: ClickTypeStatsOut[];
  byLecture: LectureClickStatsOut[];
};

export function ClickStatsTable({ byType, byLecture }: Props): JSX.Element {
  return (
    <>
      <div className="card">
        <h3>Клики по типам</h3>
        {!byType.length ? (
          <div>Нет данных.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Тип</th>
                <th>Всего</th>
                <th>Уникальных пользователей</th>
              </tr>
            </thead>
            <tbody>
              {byType.map((row) => (
                <tr key={row.event_type}>
                  <td>{row.event_type}</td>
                  <td>{row.total_clicks}</td>
                  <td>{row.unique_users}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h3>Клики по лекциям</h3>
        {!byLecture.length ? (
          <div>Нет данных.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Лекция</th>
                <th>stream_link</th>
                <th>materials_lecture</th>
                <th>registration_click</th>
                <th>Итого</th>
              </tr>
            </thead>
            <tbody>
              {byLecture.map((row) => (
                <tr key={row.lecture_id}>
                  <td>
                    №{row.lecture_number} {row.lecture_title}
                  </td>
                  <td>{row.stream_link_clicks}</td>
                  <td>{row.materials_lecture_clicks}</td>
                  <td>{row.registration_clicks}</td>
                  <td>{row.total_clicks}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
