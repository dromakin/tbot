import { useState } from 'react';

import { type LectureOut } from '../api/types';

type Props = {
  lectures: LectureOut[];
  onToggleRegistration: (lectureId: number, next: boolean) => Promise<void>;
  onSaveMaterials: (lectureId: number, materialsUrl: string | null) => Promise<void>;
  onSaveStream: (lectureId: number, streamUrl: string | null) => Promise<void>;
  onSaveTopics: (lectureId: number, topics: string | null) => Promise<void>;
  onSelectForRegistrations: (lectureId: number) => void;
};

export function LectureList({
  lectures,
  onToggleRegistration,
  onSaveMaterials,
  onSaveStream,
  onSaveTopics,
  onSelectForRegistrations,
}: Props): JSX.Element {
  const [materialsDraft, setMaterialsDraft] = useState<Record<number, string>>({});
  const [streamDraft, setStreamDraft] = useState<Record<number, string>>({});
  const [topicsDraft, setTopicsDraft] = useState<Record<number, string>>({});

  if (!lectures.length) {
    return <div className="card">Лекций пока нет.</div>;
  }

  return (
    <div className="card">
      <h3>Лекции</h3>
      {lectures.map((lecture) => (
        <div key={lecture.id} className="card">
          <b>
            №{lecture.number} {lecture.title}
          </b>
          <div>Дата: {new Date(lecture.scheduled_at).toLocaleString()}</div>
          <div>Формат: {lecture.format}</div>
          <div className="row" style={{ marginTop: 8 }}>
            <button
              className={lecture.registration_open ? 'secondary' : undefined}
              onClick={() => void onToggleRegistration(lecture.id, !lecture.registration_open)}
            >
              {lecture.registration_open ? 'Закрыть регистрацию' : 'Открыть регистрацию'}
            </button>
            <button className="secondary" onClick={() => onSelectForRegistrations(lecture.id)}>
              Регистрации
            </button>
          </div>

          <div style={{ marginTop: 8 }}>
            <label>Ссылка на доп. материал</label>
            <div className="row">
              <input
                value={materialsDraft[lecture.id] ?? lecture.materials_url ?? ''}
                onChange={(e) =>
                  setMaterialsDraft((prev) => ({
                    ...prev,
                    [lecture.id]: e.target.value,
                  }))
                }
              />
              <button
                onClick={() =>
                  void onSaveMaterials(
                    lecture.id,
                    (materialsDraft[lecture.id] ?? lecture.materials_url ?? '') || null,
                  )
                }
              >
                Сохранить
              </button>
            </div>
          </div>

          <div style={{ marginTop: 8 }}>
            <label>Ссылка на онлайн-трансляцию</label>
            <div className="row">
              <input
                value={streamDraft[lecture.id] ?? lecture.stream_url ?? ''}
                onChange={(e) =>
                  setStreamDraft((prev) => ({
                    ...prev,
                    [lecture.id]: e.target.value,
                  }))
                }
              />
              <button
                onClick={() =>
                  void onSaveStream(
                    lecture.id,
                    (streamDraft[lecture.id] ?? lecture.stream_url ?? '') || null,
                  )
                }
              >
                Сохранить
              </button>
            </div>
          </div>

          <div style={{ marginTop: 8 }}>
            <label>Темы программы (1 строка = 1 тема)</label>
            <div>
              <textarea
                rows={5}
                style={{ width: '100%' }}
                value={topicsDraft[lecture.id] ?? lecture.topics ?? ''}
                onChange={(e) =>
                  setTopicsDraft((prev) => ({
                    ...prev,
                    [lecture.id]: e.target.value,
                  }))
                }
              />
            </div>
            <div className="row">
              <button
                onClick={() =>
                  void onSaveTopics(
                    lecture.id,
                    (topicsDraft[lecture.id] ?? lecture.topics ?? '').trim() || null,
                  )
                }
              >
                Сохранить темы
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
