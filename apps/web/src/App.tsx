/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { brand } from '@citenook/brand';
import { useEffect, useState } from 'react';
import { getHealth } from './api';

type ApiState = 'checking' | 'ready' | 'unavailable';

export default function App() {
  const [apiState, setApiState] = useState<ApiState>('checking');

  useEffect(() => {
    void getHealth().then(
      (health) => setApiState(health.status === 'ok' ? 'ready' : 'unavailable'),
      () => setApiState('unavailable'),
    );
  }, []);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <strong>{brand.productName}</strong>
          <span>{brand.description}</span>
        </div>
        <span className={`api-status ${apiState}`} role="status">
          API {apiState}
        </span>
      </header>

      <main className="welcome-panel">
        <p className="eyebrow">{brand.extendedName}</p>
        <h1>{brand.tagline}</h1>
        <p>
          The local stack is ready. Model selection and document workflows are introduced in
          the next stories.
        </p>
      </main>

      <footer>
        Built by{' '}
        <a href={brand.developer.website} rel="noreferrer">
          {brand.developer.name}
        </a>
      </footer>
    </div>
  );
}
