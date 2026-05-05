export function AccessDeniedPage(): JSX.Element {
  return (
    <div className="page">
      <h2>Доступ ограничен</h2>
      <div className="card">Эта страница доступна только администраторам.</div>
    </div>
  );
}
