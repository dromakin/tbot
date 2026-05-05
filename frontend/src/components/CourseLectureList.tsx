import { type LectureOverviewRowOut } from '../api/types';
import { RowSparkline } from './RowSparkline';

type Props = {
  rows: LectureOverviewRowOut[];
  onOpenRegistrations: (lectureId: number) => void;
  onOpenClicks: (lectureId: number) => void;
};

const STATUS_LABELS: Record<LectureOverviewRowOut['status'], string> = {
  open: 'Открыта',
  closed_upcoming: 'Скоро',
  past: 'Прошла',
};

const formatDateTime = (value: string) =>
  new Date(value).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });

export function CourseLectureList({ rows, onOpenRegistrations, onOpenClicks }: Props): JSX.Element {
  if (!rows.length) {
    return <div className="card">Лекции для обзора пока отсутствуют.</div>;
  }

  return (
    <div className="card">
      <div className="overview-table-wrapper">
        <table className="table">
          <thead>
            <tr>
              <th>№</th>
              <th>Лекция</th>
              <th>Регистраций</th>
              <th>Stream unique</th>
              <th>Materials unique</th>
              <th>Посещаемость</th>
              <th>Sparkline</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.lecture_id}>
                <td>{row.lecture_number}</td>
                <td>
                  <div>
                    <b>{row.lecture_title}</b>
                  </div>
                  <div style={{ opacity: 0.8 }}>{formatDateTime(row.scheduled_at)}</div>
                  <span className={`status-badge status-${row.status}`}>{STATUS_LABELS[row.status]}</span>
                </td>
                <td>{row.registrations}</td>
                <td>{row.stream_link_unique}</td>
                <td>{row.materials_lecture_unique}</td>
                <td>
                  <div>{row.attendance_rate.toFixed(1)}%</div>
                  <div className="attendance-bar">
                    <div
                      className="attendance-bar-fill"
                      style={{ width: `${Math.max(0, Math.min(100, row.attendance_rate))}%` }}
                    />
                  </div>
                </td>
                <td>
                  <RowSparkline points={row.sparkline} />
                </td>
                <td>
                  <div className="row">
                    <button className="secondary" onClick={() => onOpenRegistrations(row.lecture_id)}>
                      Регистрации
                    </button>
                    <button className="secondary" onClick={() => onOpenClicks(row.lecture_id)}>
                      Клики
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="overview-mobile-list">
        {rows.map((row) => (
          <div key={row.lecture_id} className="overview-row card">
            <div>
              <b>
                №{row.lecture_number} {row.lecture_title}
              </b>
            </div>
            <div>{formatDateTime(row.scheduled_at)}</div>
            <span className={`status-badge status-${row.status}`}>{STATUS_LABELS[row.status]}</span>
            <div>Регистраций: {row.registrations}</div>
            <div>Stream unique: {row.stream_link_unique}</div>
            <div>Materials unique: {row.materials_lecture_unique}</div>
            <div>{row.attendance_rate.toFixed(1)}%</div>
            <div className="attendance-bar">
              <div
                className="attendance-bar-fill"
                style={{ width: `${Math.max(0, Math.min(100, row.attendance_rate))}%` }}
              />
            </div>
            <RowSparkline points={row.sparkline} />
            <div className="row">
              <button className="secondary" onClick={() => onOpenRegistrations(row.lecture_id)}>
                Регистрации
              </button>
              <button className="secondary" onClick={() => onOpenClicks(row.lecture_id)}>
                Клики
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
