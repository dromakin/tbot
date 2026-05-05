import { useEffect, useState } from 'react';

type Props = {
  generalMaterialsUrl: string | null;
  onSaveGeneralMaterials: (url: string | null) => Promise<void>;
};

export function AppSettingsPanel({ generalMaterialsUrl, onSaveGeneralMaterials }: Props): JSX.Element {
  const [draftUrl, setDraftUrl] = useState(generalMaterialsUrl ?? '');

  useEffect(() => {
    setDraftUrl(generalMaterialsUrl ?? '');
  }, [generalMaterialsUrl]);

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
    </div>
  );
}
