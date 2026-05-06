import { useState } from 'react';

import { type LectureCreateIn } from '../api/types';

type Props = {
  onSubmit: (payload: LectureCreateIn) => Promise<void>;
};

export function LectureForm({ onSubmit }: Props): JSX.Element {
  const [form, setForm] = useState<LectureCreateIn>({
    number: 1,
    title: '',
    description: '',
    topics: null,
    scheduled_at: new Date().toISOString().slice(0, 16),
    format: 'online',
    stream_url: null,
    materials_url: null,
    registration_open: true,
  });
  const [saving, setSaving] = useState(false);

  const update = <K extends keyof LectureCreateIn>(key: K, value: LectureCreateIn[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    try {
      await onSubmit({
        ...form,
        topics: form.topics || null,
        stream_url: form.stream_url || null,
        materials_url: form.materials_url || null,
      });
      setForm((prev) => ({
        ...prev,
        title: '',
        description: '',
        topics: null,
        stream_url: null,
        materials_url: null,
      }));
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h3>Создать лекцию</h3>
      <div className="row">
        <div style={{ flex: 1 }}>
          <label>Номер</label>
          <input
            type="number"
            value={form.number}
            onChange={(e) => update('number', Number(e.target.value))}
            required
          />
        </div>
        <div style={{ flex: 3 }}>
          <label>Название</label>
          <input value={form.title} onChange={(e) => update('title', e.target.value)} required />
        </div>
      </div>

      <div>
        <label>Описание</label>
        <textarea rows={3} value={form.description} onChange={(e) => update('description', e.target.value)} />
      </div>

      <div>
        <label>Темы программы (1 строка = 1 тема)</label>
        <textarea
          rows={4}
          value={form.topics ?? ''}
          onChange={(e) => update('topics', e.target.value || null)}
        />
      </div>

      <div className="row">
        <div style={{ flex: 2 }}>
          <label>Дата/время (ISO)</label>
          <input value={form.scheduled_at} onChange={(e) => update('scheduled_at', e.target.value)} required />
        </div>
        <div style={{ flex: 1 }}>
          <label>Формат</label>
          <select value={form.format} onChange={(e) => update('format', e.target.value as 'online' | 'offline')}>
            <option value="online">online</option>
            <option value="offline">offline</option>
          </select>
        </div>
      </div>

      <div className="row">
        <div style={{ flex: 1 }}>
          <label>Stream URL</label>
          <input value={form.stream_url ?? ''} onChange={(e) => update('stream_url', e.target.value || null)} />
        </div>
        <div style={{ flex: 1 }}>
          <label>Materials URL</label>
          <input value={form.materials_url ?? ''} onChange={(e) => update('materials_url', e.target.value || null)} />
        </div>
      </div>

      <div className="row" style={{ marginTop: 10 }}>
        <button type="submit" disabled={saving}>{saving ? 'Сохранение...' : 'Создать'}</button>
      </div>
    </form>
  );
}
