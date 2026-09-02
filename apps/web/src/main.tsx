/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import { brand } from '@citenook/brand';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './styles.css';

for (const [name, value] of Object.entries(brand.theme)) {
  document.documentElement.style.setProperty(`--brand-${toKebabCase(name)}`, value);
}
document.title = brand.productName;
document.querySelector('meta[name="description"]')?.setAttribute('content', brand.description);
document.querySelector<HTMLLinkElement>('link[rel="icon"]')?.setAttribute('href', brand.assets.favicon);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

function toKebabCase(value: string): string {
  return value.replace(/[A-Z]/g, (character) => `-${character.toLowerCase()}`);
}
