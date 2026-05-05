import { type RegistrationRowOut } from '../api/types';

type Props = {
  rows: RegistrationRowOut[];
};

export function RegistrationsTable({ rows }: Props): JSX.Element {
  if (!rows.length) {
    return <div className="card">Регистраций нет.</div>;
  }

  return (
    <div className="card">
      <table className="table">
        <thead>
          <tr>
            <th>tg_user_id</th>
            <th>username</th>
            <th>full_name</th>
            <th>registered_at</th>
            <th>clicks</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.tg_user_id}>
              <td>{row.tg_user_id}</td>
              <td>{row.username_at || '-'}</td>
              <td>{row.full_name}</td>
              <td>{new Date(row.registered_at).toLocaleString()}</td>
              <td>{row.clicks_count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
