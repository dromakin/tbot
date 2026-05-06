import { useEffect, useState } from 'react';

type Props = {
  generalMaterialsUrl: string | null;
  autoCloseHours: number;
  onSaveGeneralMaterials: (url: string | null) => Promise<void>;
  onSaveAutoCloseHours: (hours: number) => Promise<void>;
};

export function AppSettingsPanel({
  generalMaterialsUrl,
  autoCloseHours,
  onSaveGeneralMaterials,
  onSaveAutoCloseHours,
}: Props): JSX.Element {
  const [draftUrl, setDraftUrl] = useState(generalMaterialsUrl ?? '');
  const [draftHours, setDraftHours] = useState(String(autoCloseHours));

  useEffect(() => {
    setDraftUrl(generalMaterialsUrl ?? '');
  }, [generalMaterialsUrl]);

  useEffect(() => {
    setDraftHours(String(autoCloseHours));
  }, [autoCloseHours]);

  return (
    <div className="card">
      <h3>Настройки Mini App</h3>
      <div style={{ marginTop: 8 }}>
        <label>Основные материалы курса (общая ссылка)</label>
        <div className="row">
          <input value={draftUrl} onChange={(event) => setDraftUrl(event.target.value)} />
          <button onClick={() => void onSaveGeneralMaterials(draftUrl || null)}>Сохранить</button>
        </div>
      </div>
      <div style={{ marginTop: 12 }}>
        <label>Авто-закрытие регистрации (часы, 0 = отключено)</label>
        <div className="row">
          <input
            type="number"
            min={0}
            max={8760}
            step={1}
            value={draftHours}
            onChange={(event) => setDraftHours(event.target.value)}
          />
          <button
            onClick={() => {
              const nextHours = Number(draftHours);
              if (!Number.isFinite(nextHours)) {
                return;
              }
              const normalizedHours = Math.min(8760, Math.max(0, Math.round(nextHours)));
              void onSaveAutoCloseHours(normalizedHours);
            }}
          >
            Сохранить
          </button>
        </div>
        <small>Глобальная настройка для всех лекций. Отсчет идет от момента открытия регистрации.</small>
      </div>
    </div>
  );
}
