import { type ClickEventType, type ClickTopUserOut } from '../api/types';

type TopUsersFilter = ClickEventType | 'all';

type Props = {
  rows: ClickTopUserOut[];
  filter: TopUsersFilter;
  onFilterChange: (value: TopUsersFilter) => void;
};

export function ClickTopUsers({ rows, filter, onFilterChange }: Props): JSX.Element {
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>Top пользователей по кликам</h3>
        <select
          style={{ maxWidth: 260 }}
          value={filter}
          onChange={(event) => onFilterChange(event.target.value as TopUsersFilter)}
        >
          <option value="all">Все типы</option>
          <option value="stream_link">stream_link</option>
          <option value="materials_general">materials_general</option>
          <option value="materials_lecture">materials_lecture</option>
          <option value="registration_click">registration_click</option>
        </select>
      </div>

      {!rows.length ? (
        <div>Нет данных.</div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>tg_user_id</th>
              <th>username</th>
              <th>full_name</th>
              <th>clicks</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.tg_user_id}>
                <td>{row.tg_user_id}</td>
                <td>{row.username_at || '-'}</td>
                <td>{row.full_name}</td>
                <td>{row.clicks_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
