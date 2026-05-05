import { type ClickEventType, type ClickSummaryOut } from '../api/types';

type Props = {
  summary: ClickSummaryOut | null;
};

const EVENT_LABELS: Record<ClickEventType, string> = {
  stream_link: 'Подключение',
  materials_general: 'Основные материалы',
  materials_lecture: 'Доп. материалы',
  registration_click: 'Клик регистрации',
};

export function ClickKpiCards({ summary }: Props): JSX.Element {
  if (!summary) {
    return <div className="card">KPI пока недоступны.</div>;
  }

  return (
    <div
      className="card"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
        gap: 8,
      }}
    >
      <div className="card" style={{ marginBottom: 0 }}>
        <b>Итого</b>
        <div>Сегодня: {summary.totals.today}</div>
        <div>7 дней: {summary.totals.week}</div>
        <div>Все время: {summary.totals.all_time}</div>
      </div>
      {summary.items.map((item) => (
        <div key={item.event_type} className="card" style={{ marginBottom: 0 }}>
          <b>{EVENT_LABELS[item.event_type]}</b>
          <div>Сегодня: {item.today}</div>
          <div>7 дней: {item.week}</div>
          <div>Все время: {item.all_time}</div>
        </div>
      ))}
    </div>
  );
}
