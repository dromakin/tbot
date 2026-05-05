import { type LectureFunnelOut, type LectureOut } from '../api/types';

type Props = {
  lectures: LectureOut[];
  selectedLectureId: number | null;
  data: LectureFunnelOut | null;
  onLectureChange: (lectureId: number) => void;
};

export function ClickFunnelPanel({ lectures, selectedLectureId, data, onLectureChange }: Props): JSX.Element {
  const steps = data
    ? [
        { label: 'registration_clicks', value: data.registration_clicks },
        { label: 'registrations', value: data.registrations },
        { label: 'stream_link_unique', value: data.stream_link_unique },
        { label: 'materials_lecture_unique', value: data.materials_lecture_unique },
      ]
    : [];
  const maxValue = Math.max(1, ...steps.map((item) => item.value));

  return (
    <div className="card">
      <h3>Воронка по лекции</h3>
      {!lectures.length ? (
        <div>Лекций пока нет.</div>
      ) : (
        <div className="row" style={{ marginBottom: 10 }}>
          <select
            value={selectedLectureId ?? ''}
            onChange={(event) => onLectureChange(Number(event.target.value))}
          >
            {lectures.map((lecture) => (
              <option key={lecture.id} value={lecture.id}>
                №{lecture.number} {lecture.title}
              </option>
            ))}
          </select>
        </div>
      )}

      {!data ? (
        <div>Выберите лекцию для воронки.</div>
      ) : (
        <div>
          {steps.map((step, idx) => {
            const prev = idx === 0 ? step.value : steps[idx - 1].value;
            const conversion = prev > 0 ? Math.round((step.value / prev) * 100) : 0;
            return (
              <div key={step.label} style={{ marginBottom: 8 }}>
                <div className="row" style={{ justifyContent: 'space-between' }}>
                  <span>{step.label}</span>
                  <span>
                    {step.value} ({conversion}%)
                  </span>
                </div>
                <div
                  style={{
                    width: '100%',
                    height: 12,
                    borderRadius: 8,
                    background: '#334155',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${Math.round((step.value / maxValue) * 100)}%`,
                      height: '100%',
                      background: '#2563eb',
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
