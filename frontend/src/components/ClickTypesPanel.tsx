import { type ClickEventType, type ClickTypeSettingOut } from '../api/types';

type Props = {
  settings: ClickTypeSettingOut[];
  onToggle: (eventType: ClickEventType, enabled: boolean) => Promise<void>;
};

const EVENT_LABELS: Record<ClickEventType, string> = {
  stream_link: 'Ссылка на подключение к лекции',
  materials_general: 'Основные материалы курса',
  materials_lecture: 'Доп. материалы по лекции',
  registration_click: 'Нажатие регистрации на лекцию',
};

export function ClickTypesPanel({ settings, onToggle }: Props): JSX.Element {
  if (!settings.length) {
    return <div className="card">Настройки типов кликов не найдены.</div>;
  }

  return (
    <div className="card">
      <h3>Типы кликов</h3>
      <table className="table">
        <thead>
          <tr>
            <th>Тип</th>
            <th>Сохранение</th>
            <th>Действие</th>
          </tr>
        </thead>
        <tbody>
          {settings.map((row) => (
            <tr key={row.event_type}>
              <td>{EVENT_LABELS[row.event_type]}</td>
              <td>{row.enabled ? 'включено' : 'отключено'}</td>
              <td>
                <button
                  className={row.enabled ? 'secondary' : ''}
                  onClick={() => {
                    void onToggle(row.event_type, !row.enabled);
                  }}
                >
                  {row.enabled ? 'Отключить' : 'Включить'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
