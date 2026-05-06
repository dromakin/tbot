import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { apiFetch, buildCsvExportUrl, buildZipExportUrl } from '../api/client';
import {
  type AutoCloseHoursOut,
  type ClickEventType,
  type ClickSummaryOut,
  type ClickTimeseriesPointOut,
  type ClickTopUserOut,
  type ClickTypeSettingOut,
  type ClickTypeStatsOut,
  type CourseOverviewOut,
  type GeneralMaterialsSettingOut,
  type LectureCreateIn,
  type LectureClickStatsOut,
  type LectureFunnelOut,
  type LectureHourBucketOut,
  type LectureOverviewRowOut,
  type LectureOut,
  type MeOut,
  type QuestionOut,
  type QuestionStatus,
  type RegistrationRowOut,
  type StatsRowOut,
} from '../api/types';
import { ClickFunnelPanel } from '../components/ClickFunnelPanel';
import { ClickHourlyDrilldown } from '../components/ClickHourlyDrilldown';
import { ClickKpiCards } from '../components/ClickKpiCards';
import { ClickStatsTable } from '../components/ClickStatsTable';
import { ClickStackedByLecture } from '../components/ClickStackedByLecture';
import { ClickTimeSeries } from '../components/ClickTimeSeries';
import { ClickTopUsers } from '../components/ClickTopUsers';
import { ClickTypeDonut } from '../components/ClickTypeDonut';
import { ClickTypesPanel } from '../components/ClickTypesPanel';
import { CourseKpiCards } from '../components/CourseKpiCards';
import { CourseLectureList } from '../components/CourseLectureList';
import { AppSettingsPanel } from '../components/AppSettingsPanel';
import { LectureForm } from '../components/LectureForm';
import { LectureList } from '../components/LectureList';
import { QuestionsModerationTable } from '../components/QuestionsModerationTable';
import { RegistrationsTable } from '../components/RegistrationsTable';
import { StatsTable } from '../components/StatsTable';
import { initTelegramWebApp } from '../hooks/useTelegram';
import { AccessDeniedPage } from './AccessDeniedPage';

type TabKey = 'stats' | 'lectures' | 'create' | 'registrations' | 'clicks' | 'questions' | 'settings';
type QuestionFilter = 'all' | QuestionStatus;
type TopUsersFilter = ClickEventType | 'all';
type OverviewPeriod = 7 | 30 | 0;
type OverviewSort = 'date' | 'registrations' | 'attendance';
type OverviewFilter = 'all' | 'open' | 'past';

export function AdminPage(): JSX.Element {
  const navigate = useNavigate();
  const [me, setMe] = useState<MeOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [tab, setTab] = useState<TabKey>('stats');
  const [lectures, setLectures] = useState<LectureOut[]>([]);
  const [stats, setStats] = useState<StatsRowOut[]>([]);
  const [courseOverview, setCourseOverview] = useState<CourseOverviewOut | null>(null);
  const [courseOverviewRows, setCourseOverviewRows] = useState<LectureOverviewRowOut[]>([]);
  const [overviewPeriodDays, setOverviewPeriodDays] = useState<OverviewPeriod>(7);
  const [overviewSort, setOverviewSort] = useState<OverviewSort>('date');
  const [overviewFilter, setOverviewFilter] = useState<OverviewFilter>('all');
  const [selectedLectureId, setSelectedLectureId] = useState<number | null>(null);
  const [registrations, setRegistrations] = useState<RegistrationRowOut[]>([]);
  const [clickTypeSettings, setClickTypeSettings] = useState<ClickTypeSettingOut[]>([]);
  const [clickStatsByType, setClickStatsByType] = useState<ClickTypeStatsOut[]>([]);
  const [clickStatsByLecture, setClickStatsByLecture] = useState<LectureClickStatsOut[]>([]);
  const [clickSummary, setClickSummary] = useState<ClickSummaryOut | null>(null);
  const [clickTimeseries, setClickTimeseries] = useState<ClickTimeseriesPointOut[]>([]);
  const [clickTimeseriesDays, setClickTimeseriesDays] = useState(7);
  const [topUsers, setTopUsers] = useState<ClickTopUserOut[]>([]);
  const [topUsersFilter, setTopUsersFilter] = useState<TopUsersFilter>('all');
  const [selectedClickLectureId, setSelectedClickLectureId] = useState<number | null>(null);
  const [hourlyRows, setHourlyRows] = useState<LectureHourBucketOut[]>([]);
  const [funnelLectureId, setFunnelLectureId] = useState<number | null>(null);
  const [funnelData, setFunnelData] = useState<LectureFunnelOut | null>(null);
  const [questions, setQuestions] = useState<QuestionOut[]>([]);
  const [questionFilter, setQuestionFilter] = useState<QuestionFilter>('pending');
  const [generalMaterialsUrl, setGeneralMaterialsUrl] = useState<string | null>(null);
  const [autoCloseHours, setAutoCloseHours] = useState(24);
  const [busy, setBusy] = useState(false);

  const selectedLecture = useMemo(
    () => lectures.find((lecture) => lecture.id === selectedLectureId) ?? null,
    [lectures, selectedLectureId],
  );
  const selectedClickLecture = useMemo(
    () => lectures.find((lecture) => lecture.id === selectedClickLectureId) ?? null,
    [lectures, selectedClickLectureId],
  );
  const filteredOverviewRows = useMemo(() => {
    const filtered = courseOverviewRows.filter((row) => {
      if (overviewFilter === 'all') {
        return true;
      }
      return row.status === overviewFilter;
    });
    if (overviewSort === 'registrations') {
      return [...filtered].sort((a, b) => b.registrations - a.registrations);
    }
    if (overviewSort === 'attendance') {
      return [...filtered].sort((a, b) => b.attendance_rate - a.attendance_rate);
    }
    return [...filtered].sort(
      (a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime(),
    );
  }, [courseOverviewRows, overviewFilter, overviewSort]);

  const loadMe = async () => {
    const data = await apiFetch<MeOut>('/api/me');
    setMe(data);
  };

  const loadLectures = async () => {
    const data = await apiFetch<LectureOut[]>('/api/lectures');
    setLectures(data);
    if (!selectedLectureId && data.length) {
      setSelectedLectureId(data[0].id);
    }
    if (!selectedClickLectureId && data.length) {
      setSelectedClickLectureId(data[0].id);
    }
    if (!funnelLectureId && data.length) {
      setFunnelLectureId(data[0].id);
    }
  };

  const loadStats = async () => {
    const data = await apiFetch<StatsRowOut[]>('/api/stats');
    setStats(data);
  };

  const loadCourseOverview = async (days: OverviewPeriod) => {
    const [overview, rows] = await Promise.all([
      apiFetch<CourseOverviewOut>(`/api/course-overview?days=${days}`),
      apiFetch<LectureOverviewRowOut[]>(`/api/course-overview/lectures?days=${days}`),
    ]);
    setCourseOverview(overview);
    setCourseOverviewRows(rows);
  };

  const loadClickTypes = async () => {
    const data = await apiFetch<ClickTypeSettingOut[]>('/api/click-types');
    setClickTypeSettings(data);
  };

  const loadClickStats = async () => {
    const [byType, byLecture] = await Promise.all([
      apiFetch<ClickTypeStatsOut[]>('/api/click-stats/types'),
      apiFetch<LectureClickStatsOut[]>('/api/click-stats/lectures'),
    ]);
    setClickStatsByType(byType);
    setClickStatsByLecture(byLecture);
  };

  const loadClickSummary = async () => {
    const data = await apiFetch<ClickSummaryOut>('/api/click-stats/summary');
    setClickSummary(data);
  };

  const loadClickTimeseries = async (days: number) => {
    const data = await apiFetch<ClickTimeseriesPointOut[]>(`/api/click-stats/timeseries?days=${days}`);
    setClickTimeseries(data);
  };

  const loadTopUsers = async (filter: TopUsersFilter) => {
    const qs = filter === 'all' ? '' : `?event_type=${filter}`;
    const data = await apiFetch<ClickTopUserOut[]>(`/api/click-stats/top-users${qs}`);
    setTopUsers(data);
  };

  const loadLectureHourly = async (lectureId: number) => {
    const data = await apiFetch<LectureHourBucketOut[]>(`/api/click-stats/lecture/${lectureId}/by-hour`);
    setHourlyRows(data);
  };

  const loadLectureFunnel = async (lectureId: number) => {
    const data = await apiFetch<LectureFunnelOut>(`/api/click-stats/funnel?lecture_id=${lectureId}`);
    setFunnelData(data);
  };

  const loadClickDashboard = async () => {
    await Promise.all([
      loadClickTypes(),
      loadClickStats(),
      loadClickSummary(),
      loadClickTimeseries(clickTimeseriesDays),
      loadTopUsers(topUsersFilter),
    ]);
    const lectureId = selectedClickLectureId ?? lectures[0]?.id ?? null;
    if (lectureId !== null) {
      await loadLectureHourly(lectureId);
      if (selectedClickLectureId === null) {
        setSelectedClickLectureId(lectureId);
      }
    } else {
      setHourlyRows([]);
    }

    const funnelId = funnelLectureId ?? lectureId;
    if (funnelId !== null) {
      await loadLectureFunnel(funnelId);
      if (funnelLectureId === null) {
        setFunnelLectureId(funnelId);
      }
    } else {
      setFunnelData(null);
    }
  };

  const loadQuestions = async (filter: QuestionFilter) => {
    const path = filter === 'all' ? '/api/questions' : `/api/questions?question_status=${filter}`;
    const data = await apiFetch<QuestionOut[]>(path);
    setQuestions(data);
  };

  const loadRegistrations = async (lectureId: number) => {
    const data = await apiFetch<RegistrationRowOut[]>(`/api/lectures/${lectureId}/registrations`);
    setRegistrations(data);
  };

  const loadGeneralMaterialsSetting = async () => {
    const data = await apiFetch<GeneralMaterialsSettingOut>('/api/app-settings/general-materials');
    setGeneralMaterialsUrl(data.url);
  };

  const loadAutoCloseHours = async () => {
    const data = await apiFetch<AutoCloseHoursOut>('/api/settings/auto-close-hours');
    setAutoCloseHours(data.hours);
  };

  useEffect(() => {
    initTelegramWebApp();
    Promise.all([
      loadMe(),
      loadLectures(),
      loadStats(),
      loadCourseOverview(7),
      loadClickTypes(),
      loadQuestions('pending'),
      loadGeneralMaterialsSetting(),
      loadAutoCloseHours(),
    ])
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Failed to initialize admin page'))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (tab !== 'clicks') {
      return;
    }
    void withBusy(async () => {
      await loadClickDashboard();
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  useEffect(() => {
    if (tab !== 'stats') {
      return;
    }
    void withBusy(async () => {
      await loadCourseOverview(overviewPeriodDays);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, overviewPeriodDays]);

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

  const handleCreateLecture = async (payload: LectureCreateIn) => {
    await withBusy(async () => {
      await apiFetch<LectureOut>('/api/lectures', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      await Promise.all([loadLectures(), loadStats()]);
      setTab('lectures');
    });
  };

  const handleToggleRegistration = async (lectureId: number, next: boolean) => {
    await withBusy(async () => {
      await apiFetch<LectureOut>(`/api/lectures/${lectureId}/registration`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ open: next }),
      });
      await Promise.all([loadLectures(), loadStats()]);
    });
  };

  const handleSaveMaterials = async (lectureId: number, materialsUrl: string | null) => {
    await withBusy(async () => {
      await apiFetch<LectureOut>(`/api/lectures/${lectureId}/materials`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ materials_url: materialsUrl }),
      });
      await loadLectures();
    });
  };

  const handleSaveStream = async (lectureId: number, streamUrl: string | null) => {
    await withBusy(async () => {
      await apiFetch<LectureOut>(`/api/lectures/${lectureId}/stream`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stream_url: streamUrl }),
      });
      await loadLectures();
    });
  };

  const handleSaveTopics = async (lectureId: number, topics: string | null) => {
    await withBusy(async () => {
      await apiFetch<LectureOut>(`/api/lectures/${lectureId}/topics`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topics }),
      });
      await loadLectures();
    });
  };

  const handleSaveGeneralMaterials = async (url: string | null) => {
    await withBusy(async () => {
      const payload = url && url.trim() ? url.trim() : null;
      const response = await apiFetch<GeneralMaterialsSettingOut>('/api/app-settings/general-materials', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: payload }),
      });
      setGeneralMaterialsUrl(response.url);
    });
  };

  const handleSaveAutoCloseHours = async (hours: number) => {
    await withBusy(async () => {
      const payload = Math.min(8760, Math.max(0, Math.round(hours)));
      const response = await apiFetch<AutoCloseHoursOut>('/api/settings/auto-close-hours', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hours: payload }),
      });
      setAutoCloseHours(response.hours);
    });
  };

  const handleSelectRegistrations = async (lectureId: number) => {
    setSelectedLectureId(lectureId);
    setTab('registrations');
    await withBusy(async () => {
      await loadRegistrations(lectureId);
    });
  };

  const handleToggleClickType = async (eventType: ClickEventType, enabled: boolean) => {
    await withBusy(async () => {
      await apiFetch(`/api/click-types/${eventType}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
      await loadClickDashboard();
    });
  };

  const handleClickTimeseriesWindowChange = async (days: number) => {
    setClickTimeseriesDays(days);
    await withBusy(async () => {
      await loadClickTimeseries(days);
    });
  };

  const handleTopUsersFilterChange = async (nextFilter: TopUsersFilter) => {
    setTopUsersFilter(nextFilter);
    await withBusy(async () => {
      await loadTopUsers(nextFilter);
    });
  };

  const handleClickLectureSelect = async (lectureId: number) => {
    setSelectedClickLectureId(lectureId);
    await withBusy(async () => {
      await loadLectureHourly(lectureId);
    });
  };

  const handleFunnelLectureSelect = async (lectureId: number) => {
    setFunnelLectureId(lectureId);
    await withBusy(async () => {
      await loadLectureFunnel(lectureId);
    });
  };

  const handleIgnoreQuestion = async (questionId: number) => {
    await withBusy(async () => {
      await apiFetch(`/api/questions/${questionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'ignored' }),
      });
      await loadQuestions(questionFilter);
    });
  };

  const handleAnswerQuestion = async (questionId: number, answerText: string) => {
    await withBusy(async () => {
      await apiFetch(`/api/questions/${questionId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'answered', answer_text: answerText }),
      });
      await loadQuestions(questionFilter);
    });
  };

  if (loading) {
    return <div className="page">Loading admin app...</div>;
  }

  if (error && !me) {
    return <div className="page">Error: {error}</div>;
  }

  if (!me?.is_admin) {
    return <AccessDeniedPage />;
  }

  return (
    <div className="page">
      <h2>Admin Mini App</h2>
      <div className="card">
        <div><b>{me.full_name}</b> ({me.username ? `@${me.username}` : '-'})</div>
        <div>tg_user_id: {me.tg_user_id}</div>
      </div>

      <div className="row" style={{ marginBottom: 12 }}>
        <button onClick={() => setTab('stats')}>Статистика</button>
        <button onClick={() => setTab('lectures')}>Лекции</button>
        <button onClick={() => setTab('create')}>Создание</button>
        <button onClick={() => setTab('registrations')}>Регистрации</button>
        <button onClick={() => setTab('clicks')}>Клики</button>
        <button onClick={() => setTab('questions')}>Вопросы</button>
        <button onClick={() => setTab('settings')}>Настройки</button>
        <button className="secondary" onClick={() => navigate('/')}>Пользовательский режим</button>
        <button className="secondary" onClick={() => window.open(buildCsvExportUrl(), '_blank')}>CSV</button>
        <button className="secondary" onClick={() => window.open(buildZipExportUrl(), '_blank')}>ZIP</button>
      </div>

      {error ? <div className="card">Error: {error}</div> : null}
      {busy ? <div className="card">Выполняется запрос...</div> : null}

      {tab === 'stats' ? (
        <>
          <div className="card">
            <div className="row">
              <select
                value={overviewPeriodDays}
                onChange={(event) => setOverviewPeriodDays(Number(event.target.value) as OverviewPeriod)}
              >
                <option value={7}>Период: 7 дней</option>
                <option value={30}>Период: 30 дней</option>
                <option value={0}>Период: все время</option>
              </select>
              <select
                value={overviewSort}
                onChange={(event) => setOverviewSort(event.target.value as OverviewSort)}
              >
                <option value="date">Сортировка: по дате</option>
                <option value="registrations">Сортировка: по регистрациям</option>
                <option value="attendance">Сортировка: по посещаемости</option>
              </select>
              <select
                value={overviewFilter}
                onChange={(event) => setOverviewFilter(event.target.value as OverviewFilter)}
              >
                <option value="all">Фильтр: все</option>
                <option value="open">Фильтр: открытые</option>
                <option value="past">Фильтр: прошедшие</option>
              </select>
              <button
                onClick={() => {
                  void withBusy(async () => {
                    await Promise.all([loadCourseOverview(overviewPeriodDays), loadStats()]);
                  });
                }}
              >
                Обновить
              </button>
            </div>
          </div>
          <CourseKpiCards overview={courseOverview} />
          <CourseLectureList
            rows={filteredOverviewRows}
            onOpenRegistrations={(lectureId) => {
              void handleSelectRegistrations(lectureId);
            }}
            onOpenClicks={(lectureId) => {
              setSelectedClickLectureId(lectureId);
              setFunnelLectureId(lectureId);
              setTab('clicks');
            }}
          />
          <details className="card">
            <summary>Показать fallback таблицу</summary>
            <StatsTable rows={stats} />
          </details>
        </>
      ) : null}

      {tab === 'lectures' ? (
        <LectureList
          lectures={lectures}
          onToggleRegistration={handleToggleRegistration}
          onSaveMaterials={handleSaveMaterials}
          onSaveStream={handleSaveStream}
          onSaveTopics={handleSaveTopics}
          onSelectForRegistrations={(lectureId) => {
            void handleSelectRegistrations(lectureId);
          }}
        />
      ) : null}

      {tab === 'create' ? <LectureForm onSubmit={handleCreateLecture} /> : null}

      {tab === 'registrations' ? (
        <>
          <div className="card">
            <label>Лекция</label>
            <div className="row">
              <select
                value={selectedLectureId ?? ''}
                onChange={(event) => setSelectedLectureId(Number(event.target.value))}
              >
                {lectures.map((lecture) => (
                  <option key={lecture.id} value={lecture.id}>
                    №{lecture.number} {lecture.title}
                  </option>
                ))}
              </select>
              <button
                onClick={() => {
                  if (selectedLectureId) {
                    void withBusy(async () => {
                      await loadRegistrations(selectedLectureId);
                    });
                  }
                }}
              >
                Обновить
              </button>
            </div>
            {selectedLecture ? (
              <div style={{ marginTop: 8 }}>
                Текущая лекция: №{selectedLecture.number} {selectedLecture.title}
              </div>
            ) : null}
          </div>
          <RegistrationsTable rows={registrations} />
        </>
      ) : null}

      {tab === 'clicks' ? (
        <>
          <ClickTypesPanel settings={clickTypeSettings} onToggle={handleToggleClickType} />
          <ClickKpiCards summary={clickSummary} />
          <div className="row">
            <div style={{ flex: 1, minWidth: 280 }}>
              <ClickTypeDonut rows={clickStatsByType} />
            </div>
            <div style={{ flex: 2, minWidth: 320 }}>
              <ClickTimeSeries
                rows={clickTimeseries}
                days={clickTimeseriesDays}
                onDaysChange={(days) => {
                  void handleClickTimeseriesWindowChange(days);
                }}
              />
            </div>
          </div>
          <ClickStackedByLecture
            rows={clickStatsByLecture}
            selectedLectureId={selectedClickLectureId}
            onSelectLecture={(lectureId) => {
              void handleClickLectureSelect(lectureId);
            }}
          />
          <ClickHourlyDrilldown
            lectureTitle={selectedClickLecture ? `№${selectedClickLecture.number} ${selectedClickLecture.title}` : null}
            rows={hourlyRows}
          />
          <ClickFunnelPanel
            lectures={lectures}
            selectedLectureId={funnelLectureId}
            data={funnelData}
            onLectureChange={(lectureId) => {
              void handleFunnelLectureSelect(lectureId);
            }}
          />
          <ClickTopUsers
            rows={topUsers}
            filter={topUsersFilter}
            onFilterChange={(nextFilter) => {
              void handleTopUsersFilterChange(nextFilter);
            }}
          />
          <details className="card">
            <summary>Показать raw таблицы</summary>
            <ClickStatsTable byType={clickStatsByType} byLecture={clickStatsByLecture} />
          </details>
        </>
      ) : null}

      {tab === 'questions' ? (
        <>
          <div className="card">
            <div className="row">
              <select
                value={questionFilter}
                onChange={(event) => setQuestionFilter(event.target.value as QuestionFilter)}
              >
                <option value="all">Все</option>
                <option value="pending">pending</option>
                <option value="ignored">ignored</option>
                <option value="answered">answered</option>
              </select>
              <button
                onClick={() => {
                  void withBusy(async () => {
                    await loadQuestions(questionFilter);
                  });
                }}
              >
                Обновить
              </button>
            </div>
          </div>
          <QuestionsModerationTable
            rows={questions}
            onIgnore={handleIgnoreQuestion}
            onAnswer={handleAnswerQuestion}
          />
        </>
      ) : null}

      {tab === 'settings' ? (
        <AppSettingsPanel
          generalMaterialsUrl={generalMaterialsUrl}
          autoCloseHours={autoCloseHours}
          onSaveGeneralMaterials={handleSaveGeneralMaterials}
          onSaveAutoCloseHours={handleSaveAutoCloseHours}
        />
      ) : null}
    </div>
  );
}
