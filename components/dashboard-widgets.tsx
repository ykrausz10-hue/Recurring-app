'use client';

import { useMemo, useState } from 'react';

const defaultWidgets = {
  pipeline: true,
  interviews: true,
  licenses: true,
  onboarding: true
};

export function DashboardWidgets({ stats }: { stats: Record<string, number> }) {
  const [widgets, setWidgets] = useState(defaultWidgets);

  const visible = useMemo(
    () => Object.entries(widgets).filter(([, enabled]) => enabled).map(([name]) => name),
    [widgets]
  );

  return (
    <>
      <div className="card">
        <h3>Configure Dashboard</h3>
        <div style={{ display: 'grid', gap: 8 }}>
          {Object.keys(defaultWidgets).map((key) => (
            <label key={key}>
              <input
                type="checkbox"
                checked={widgets[key as keyof typeof defaultWidgets]}
                onChange={(event) => setWidgets((prev) => ({ ...prev, [key]: event.target.checked }))}
              />{' '}
              Show {key}
            </label>
          ))}
        </div>
      </div>
      <div className="grid tile-grid" style={{ marginTop: 16 }}>
        {visible.includes('pipeline') && <div className="card"><h3>Applications</h3><p>{stats.applications}</p></div>}
        {visible.includes('interviews') && <div className="card"><h3>Interviews</h3><p>{stats.interviews}</p></div>}
        {visible.includes('licenses') && <div className="card"><h3>Expiring Licenses (30 days)</h3><p>{stats.licensesDue}</p></div>}
        {visible.includes('onboarding') && <div className="card"><h3>Open Onboarding Tasks</h3><p>{stats.tasks}</p></div>}
      </div>
    </>
  );
}
