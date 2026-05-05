import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { apiFetch } from '../api/client';
import { type MeOut, type UserActionOut, type UserLectureOut, type UserRegistrationOut, type UserStaticOut } from '../api/types';
import { initTelegramWebApp } from '../hooks/useTelegram';

type UserTab = 'schedule' | 'registrations' | 'program' | 'contact';
type ProgramSection = { lectureTitle: string; topics: string[] };

function normalizeSpaces(value: string): string {
  return value.replace(/\s+/g, ' ').trim();
}

function parseProgramSections(rawHtml: string): ProgramSection[] {
  const plain = rawHtml
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/\r/g, '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .join('\n');

  const lectureRegex = /Лекция №\d+/g;
  const lectureMatches = [...plain.matchAll(lectureRegex)];
  if (!lectureMatches.length) {
    return [];
  }

  const sections: ProgramSection[] = [];
  for (let index = 0; index < lectureMatches.length; index += 1) {
    const match = lectureMatches[index];
    const start = match.index ?? 0;
    const end = lectureMatches[index + 1]?.index ?? plain.length;
    const lectureTitle = match[0];
    const lectureBody = plain.slice(start + lectureTitle.length, end).trim();
    const topics = lectureBody
      .split(/\n|(?=\d+\.\s*)/g)
      .map((part) => normalizeSpaces(part))
      .filter((part) => part.length > 0 && /\d+\.\s*/.test(part));

    sections.push({ lectureTitle, topics });
  }
  return sections;
}

export function UserPage(): JSX.Element {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<UserTab>('schedule');
  const [me, setMe] = useState<MeOut | null>(null);
  const [lectures, setLectures] = useState<UserLectureOut[]>([]);
  const [registrations, setRegistrations] = useState<UserRegistrationOut[]>([]);
  const [staticData, setStaticData] = useState<UserStaticOut | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const programSections = useMemo(
    () => (staticData?.program_text ? parseProgramSections(staticData.program_text) : []),
    [staticData?.program_text],
  );

  const loadMe = async () => {
    const data = await apiFetch<MeOut>('/api/me');
    setMe(data);
    return data;
  };

  const loadLectures = async () => {
    const data = await apiFetch<UserLectureOut[]>('/api/user/lectures');
    setLectures(data);
  };

  const loadRegistrations = async () => {
    const data = await apiFetch<UserRegistrationOut[]>('/api/user/registrations');
    setRegistrations(data);
  };

  const loadStatic = async () => {
    const data = await apiFetch<UserStaticOut>('/api/user/static');
    setStaticData(data);
  };

  const withBusy = async (action: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setBusy(false);
    }
  };

  const handleAction = async (path: string, method: 'GET' | 'POST' = 'GET') => {
    await withBusy(async () => {
      const response = await apiFetch<UserActionOut>(path, { method });
      if (response.url) {
        window.open(response.url, '_blank');
        setActionMessage('Ссылка открыта в новой вкладке.');
      } else {
        setActionMessage(response.message);
      }
      await Promise.all([loadLectures(), loadRegistrations()]);
    });
  };

  useEffect(() => {
    initTelegramWebApp();
    void (async () => {
      try {
        await loadMe();
        await Promise.all([loadLectures(), loadRegistrations(), loadStatic()]);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to initialize user page');
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return <div className="page">Loading user app...</div>;
  }

  return (
    <div className="page">
      <h2>Mini App для студентов</h2>
      {me ? (
        <div className="card">
          <div><b>{me.full_name}</b> ({me.username ? `@${me.username}` : '-'})</div>
          <div>tg_user_id: {me.tg_user_id}</div>
          {me.is_admin ? (
            <div style={{ marginTop: 8 }}>
              <button className="secondary" onClick={() => navigate('/admin')}>
                Открыть админ-панель
              </button>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="row" style={{ marginBottom: 12 }}>
        <button onClick={() => setTab('schedule')}>Расписание</button>
        <button onClick={() => setTab('registrations')}>Мои регистрации</button>
        <button onClick={() => setTab('program')}>Программа курса</button>
        <button onClick={() => setTab('contact')}>Контакты</button>
      </div>

      {error ? <div className="card">Error: {error}</div> : null}
      {busy ? <div className="card">Выполняется запрос...</div> : null}
      {actionMessage ? <div className="card">{actionMessage}</div> : null}

      {tab === 'schedule' ? (
        <>
          <div className="card">
            <button
              className="secondary"
              onClick={() => {
                void handleAction('/api/user/materials/general');
              }}
            >
              Основные материалы курса
            </button>
          </div>
          {lectures.length ? (
            lectures.map((lecture) => (
              <div className="card" key={lecture.lecture_id}>
                <div>
                  <b>№{lecture.lecture_number} {lecture.lecture_title}</b>
                </div>
                <div>{new Date(lecture.scheduled_at).toLocaleString('ru-RU')}</div>
                <div>Формат: {lecture.format === 'online' ? 'Онлайн' : 'Очно'}</div>
                {lecture.description ? <div style={{ marginTop: 8 }}>{lecture.description}</div> : null}
                <div className="row" style={{ marginTop: 8 }}>
                  <button
                    disabled={!lecture.registration_open || lecture.is_registered}
                    onClick={() => {
                      void handleAction(`/api/user/lectures/${lecture.lecture_id}/register`, 'POST');
                    }}
                  >
                    {lecture.is_registered ? 'Уже зарегистрирован' : 'Зарегистрироваться'}
                  </button>
                  <button
                    className="secondary"
                    disabled={!lecture.has_stream}
                    onClick={() => {
                      void handleAction(`/api/user/lectures/${lecture.lecture_id}/stream`);
                    }}
                  >
                    Получить ссылку
                  </button>
                  <button
                    className="secondary"
                    disabled={!lecture.has_materials}
                    onClick={() => {
                      void handleAction(`/api/user/lectures/${lecture.lecture_id}/materials`);
                    }}
                  >
                    Материалы
                  </button>
                </div>
              </div>
            ))
          ) : (
            <div className="card">Лекции пока отсутствуют.</div>
          )}
        </>
      ) : null}

      {tab === 'registrations' ? (
        <div className="card">
          {registrations.length ? (
            <ul style={{ margin: 0, paddingLeft: 18 }}>
              {registrations.map((row) => (
                <li key={`${row.lecture_id}-${row.registered_at}`} style={{ marginBottom: 8 }}>
                  <b>№{row.lecture_number} {row.lecture_title}</b><br />
                  Лекция: {new Date(row.scheduled_at).toLocaleString('ru-RU')}<br />
                  Зарегистрирован: {new Date(row.registered_at).toLocaleString('ru-RU')}
                </li>
              ))}
            </ul>
          ) : (
            <div>Вы пока не зарегистрированы ни на одну лекцию.</div>
          )}
        </div>
      ) : null}

      {tab === 'program' ? (
        <div className="card">
          {!staticData?.program_text ? <div>Загрузка...</div> : null}
          {staticData?.program_text && !programSections.length ? (
            <div style={{ whiteSpace: 'pre-line' }}>{staticData.program_text.replace(/<[^>]+>/g, '')}</div>
          ) : null}
          {programSections.map((section) => (
            <div key={section.lectureTitle} style={{ marginBottom: 12 }}>
              <b>{section.lectureTitle}</b>
              <ul style={{ margin: '6px 0 0 18px' }}>
                {section.topics.map((topic) => (
                  <li key={`${section.lectureTitle}-${topic}`}>{topic}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : null}

      {tab === 'contact' ? (
        <div className="card" dangerouslySetInnerHTML={{ __html: staticData?.contact_text ?? 'Загрузка...' }} />
      ) : null}
    </div>
  );
}
