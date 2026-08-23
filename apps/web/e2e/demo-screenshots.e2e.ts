/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import path from 'node:path';
import { expect, test, type Locator, type Page, type Route } from '@playwright/test';

const SCREENSHOT_DIRECTORY = path.resolve(process.cwd(), '../../docs/screenshots');

const models = {
  chatModels: [
    { name: 'qwen3.5:9b', installed: true },
    { name: 'llama3.1:8b', installed: true },
  ],
  embeddingModels: [
    { name: 'qwen3-embedding:0.6b', installed: true },
    { name: 'embeddinggemma', installed: true },
  ],
  defaultChatModel: 'qwen3.5:9b',
  defaultEmbeddingModel: 'qwen3-embedding:0.6b',
  ollamaAvailable: true,
};

const conversations = [
  {
    id: 'demo-energy',
    title: 'Neighborhood energy brief',
    chatModel: 'qwen3.5:9b',
    embeddingModel: 'qwen3-embedding:0.6b',
    createdAt: '2026-08-20T09:00:00Z',
    updatedAt: '2026-08-20T09:12:00Z',
  },
  {
    id: 'demo-garden',
    title: 'Community garden handbook',
    chatModel: 'llama3.1:8b',
    embeddingModel: 'qwen3-embedding:0.6b',
    createdAt: '2026-08-19T14:30:00Z',
    updatedAt: '2026-08-19T14:30:00Z',
  },
  {
    id: 'demo-transit',
    title: 'Local transit survey',
    chatModel: 'qwen3.5:9b',
    embeddingModel: 'embeddinggemma',
    createdAt: '2026-08-18T11:15:00Z',
    updatedAt: '2026-08-18T11:15:00Z',
  },
];

const documents = [
  {
    id: 'demo-document-energy',
    fileName: 'neighborhood-energy-brief.pdf',
    contentType: 'application/pdf',
    sizeBytes: 864_320,
    sha256: 'demo-energy-sha256',
    embeddingModel: 'qwen3-embedding:0.6b',
    status: 'ready',
    errorMessage: null,
    chunkCount: 18,
    isActive: true,
    createdAt: '2026-08-20T08:45:00Z',
  },
  {
    id: 'demo-document-garden',
    fileName: 'pollinator-garden-field-notes.md',
    contentType: 'text/markdown',
    sizeBytes: 32_768,
    sha256: 'demo-garden-sha256',
    embeddingModel: 'qwen3-embedding:0.6b',
    status: 'ready',
    errorMessage: null,
    chunkCount: 9,
    isActive: true,
    createdAt: '2026-08-19T14:10:00Z',
  },
  {
    id: 'demo-document-transit',
    fileName: 'weekend-transit-survey.docx',
    contentType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    sizeBytes: 147_456,
    sha256: 'demo-transit-sha256',
    embeddingModel: 'embeddinggemma',
    status: 'ready',
    errorMessage: null,
    chunkCount: 12,
    isActive: false,
    createdAt: '2026-08-18T11:00:00Z',
  },
  {
    id: 'demo-document-workshop',
    fileName: 'repair-workshop-checklist.txt',
    contentType: 'text/plain',
    sizeBytes: 5_120,
    sha256: 'demo-workshop-sha256',
    embeddingModel: 'qwen3-embedding:0.6b',
    status: 'failed',
    errorMessage: 'The sample file contains no extractable text.',
    chunkCount: 0,
    isActive: true,
    createdAt: '2026-08-17T16:20:00Z',
  },
];

const messages = [
  {
    id: 'demo-message-1',
    conversationId: 'demo-energy',
    ordinal: 1,
    role: 'user',
    content: 'What reduces evening grid demand?',
    chatModel: null,
    citations: [],
    responseDurationMs: null,
    createdAt: '2026-08-20T09:10:00Z',
  },
  {
    id: 'demo-message-2',
    conversationId: 'demo-energy',
    ordinal: 2,
    role: 'assistant',
    content:
      'The brief recommends shifting water heating and vehicle charging to midday, when rooftop solar output is highest. Battery storage then covers the early-evening peak [S1].',
    chatModel: 'qwen3.5:9b',
    citations: [
      {
        sourceId: 'S1',
        documentId: 'demo-document-energy',
        documentName: 'neighborhood-energy-brief.pdf',
        pageNumber: 4,
        chunkId: 'demo-chunk-energy-4',
        snippet:
          'Flexible loads should move to the midday solar window, preserving stored energy for demand between 17:00 and 20:00.',
        score: 0.892,
      },
    ],
    responseDurationMs: 1840,
    createdAt: '2026-08-20T09:10:02Z',
  },
];

test.beforeEach(async ({ page }) => {
  await page.route('**/api/**', route => fulfillDemoApi(route));
  await page.goto('/');
  await expect(page.locator('.ollama-status')).toContainText('Ollama connected');
  await expect(page.getByText('Battery storage then covers')).toBeVisible();
});

test('captures privacy-safe product screenshots', async ({ page }) => {
  await capture(page, 'citenook-chat-desktop.png');

  await page.getByRole('tab', { name: 'Documents' }).click();
  await expect(page.getByRole('heading', { name: 'Stored documents' })).toBeVisible();
  await expect(page.getByText('neighborhood-energy-brief.pdf')).toBeVisible();
  await captureElement(page.locator('.document-list-panel'), 'citenook-documents-desktop.png');

  await page.setViewportSize({ width: 430, height: 932 });
  await page.getByRole('tab', { name: 'Chat' }).click();
  await expect(page.getByRole('heading', { name: 'Neighborhood energy brief' })).toBeVisible();
  await capture(page, 'citenook-chat-mobile.png', true);
});

async function fulfillDemoApi(route: Route) {
  const request = route.request();
  const pathname = new URL(request.url()).pathname;

  if (request.method() === 'GET' && pathname === '/api/models') {
    await route.fulfill({ json: models });
    return;
  }
  if (request.method() === 'GET' && pathname === '/api/conversations') {
    await route.fulfill({ json: conversations });
    return;
  }
  if (request.method() === 'GET' && pathname === '/api/documents') {
    await route.fulfill({ json: documents });
    return;
  }
  if (
    request.method() === 'GET' &&
    pathname === '/api/conversations/demo-energy/messages'
  ) {
    await route.fulfill({ json: messages });
    return;
  }

  await route.fulfill({
    status: 404,
    contentType: 'application/json',
    body: JSON.stringify({ detail: `No demo response for ${request.method()} ${pathname}` }),
  });
}

async function capture(page: Page, fileName: string, fullPage = false) {
  await page.screenshot({
    path: path.join(SCREENSHOT_DIRECTORY, fileName),
    animations: 'disabled',
    fullPage,
  });
}

async function captureElement(locator: Locator, fileName: string) {
  await locator.screenshot({
    path: path.join(SCREENSHOT_DIRECTORY, fileName),
    animations: 'disabled',
  });
}
