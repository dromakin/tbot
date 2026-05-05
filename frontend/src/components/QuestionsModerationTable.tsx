import { useEffect, useState } from 'react';

import { type QuestionOut } from '../api/types';

type Props = {
  rows: QuestionOut[];
  onIgnore: (questionId: number) => Promise<void>;
  onAnswer: (questionId: number, answerText: string) => Promise<void>;
};

export function QuestionsModerationTable({ rows, onIgnore, onAnswer }: Props): JSX.Element {
  const [drafts, setDrafts] = useState<Record<number, string>>({});

  useEffect(() => {
    setDrafts((prev) => {
      const next = { ...prev };
      for (const row of rows) {
        if (next[row.id] === undefined) {
          next[row.id] = row.answer_text ?? '';
        }
      }
      return next;
    });
  }, [rows]);

  if (!rows.length) {
    return <div className="card">Вопросов нет.</div>;
  }

  return (
    <div className="card">
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Пользователь</th>
            <th>Вопрос</th>
            <th>Статус</th>
            <th>Ответ</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.id}</td>
              <td>
                <div>{row.full_name}</div>
                <div>{row.username_at || '-'}</div>
                <div>id: {row.tg_user_id}</div>
              </td>
              <td>{row.text}</td>
              <td>{row.status}</td>
              <td style={{ minWidth: 260 }}>
                <textarea
                  value={drafts[row.id] ?? ''}
                  onChange={(event) =>
                    setDrafts((prev) => ({
                      ...prev,
                      [row.id]: event.target.value,
                    }))
                  }
                />
                {row.answered_by_admin_id ? (
                  <div style={{ marginTop: 6, fontSize: 12 }}>
                    Последний ответ: admin_id={row.answered_by_admin_id}
                    {row.answered_by_admin_username ? ` (@${row.answered_by_admin_username})` : ''}
                  </div>
                ) : null}
              </td>
              <td>
                <div className="row">
                  <button
                    className="secondary"
                    onClick={() => {
                      void onIgnore(row.id);
                    }}
                  >
                    Ignore
                  </button>
                  <button
                    onClick={() => {
                      const text = (drafts[row.id] ?? '').trim();
                      if (!text) return;
                      void onAnswer(row.id, text);
                    }}
                  >
                    Ответить
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
