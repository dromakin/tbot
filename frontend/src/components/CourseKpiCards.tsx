import { type CourseOverviewOut } from '../api/types';

type Props = {
  overview: CourseOverviewOut | null;
};

const formatNumber = (value: number) => value.toLocaleString('ru-RU');

export function CourseKpiCards({ overview }: Props): JSX.Element {
  if (!overview) {
    return <div className="card">KPI пока недоступны.</div>;
  }

  return (
    <div className="overview-grid card">
      <div className="card" style={{ marginBottom: 0 }}>
        <b>Лекции</b>
        <div>Всего: {formatNumber(overview.lectures_total)}</div>
        <div>Открыто: {formatNumber(overview.lectures_open)}</div>
        <div>Прошло: {formatNumber(overview.lectures_past)}</div>
      </div>
      <div className="card" style={{ marginBottom: 0 }}>
        <b>Регистрации</b>
        <div>{formatNumber(overview.registrations_total)}</div>
      </div>
      <div className="card" style={{ marginBottom: 0 }}>
        <b>Студенты курса</b>
        <div>{formatNumber(overview.unique_students)}</div>
      </div>
      <div className="card" style={{ marginBottom: 0 }}>
        <b>Среднее регистраций</b>
        <div>{overview.avg_registrations_per_lecture.toFixed(2)}</div>
      </div>
      <div className="card" style={{ marginBottom: 0 }}>
        <b>Посещаемость</b>
        <div>{overview.attendance_rate.toFixed(1)}%</div>
      </div>
      <div className="card" style={{ marginBottom: 0 }}>
        <b>Pending вопросов</b>
        <div>{formatNumber(overview.questions_pending_total)}</div>
      </div>
      <div className="card" style={{ marginBottom: 0 }}>
        <b>Клики за период</b>
        <div>{formatNumber(overview.period_clicks_total)}</div>
      </div>
    </div>
  );
}
