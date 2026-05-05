import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { type LectureClickStatsOut } from '../api/types';

type Props = {
  rows: LectureClickStatsOut[];
  selectedLectureId: number | null;
  onSelectLecture: (lectureId: number) => void;
};

export function ClickStackedByLecture({ rows, selectedLectureId, onSelectLecture }: Props): JSX.Element {
  const handleSelect = (row: LectureClickStatsOut | undefined) => {
    if (!row) {
      return;
    }
    onSelectLecture(row.lecture_id);
  };

  return (
    <div className="card">
      <h3>Клики по лекциям</h3>
      {!rows.length ? (
        <div>Нет данных.</div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="lecture_number" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar
                dataKey="stream_link_clicks"
                stackId="clicks"
                fill="#2563eb"
                onClick={(entry: unknown) =>
                  handleSelect((entry as { payload?: LectureClickStatsOut } | undefined)?.payload)
                }
              />
              <Bar
                dataKey="materials_lecture_clicks"
                stackId="clicks"
                fill="#f59e0b"
                onClick={(entry: unknown) =>
                  handleSelect((entry as { payload?: LectureClickStatsOut } | undefined)?.payload)
                }
              />
              <Bar
                dataKey="registration_clicks"
                stackId="clicks"
                fill="#db2777"
                onClick={(entry: unknown) =>
                  handleSelect((entry as { payload?: LectureClickStatsOut } | undefined)?.payload)
                }
              />
            </BarChart>
          </ResponsiveContainer>
          <div className="row">
            {rows.map((row) => (
              <button
                key={row.lecture_id}
                className={selectedLectureId === row.lecture_id ? '' : 'secondary'}
                onClick={() => onSelectLecture(row.lecture_id)}
              >
                №{row.lecture_number}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
