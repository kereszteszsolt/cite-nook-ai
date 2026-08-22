/*
 * SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
 * SPDX-License-Identifier: Apache-2.0
 */

import brandData from '../brand.json';

export interface BrandConfig {
  productName: string;
  extendedName: string;
  description: string;
  tagline: string;
  developer: {
    name: string;
    website: string;
  };
  technical: {
    repository: string;
    packageScope: string;
    appId: string;
    dockerProject: string;
    storyPrefix: string;
  };
  theme: Record<string, string>;
}

export const brand = brandData satisfies BrandConfig;
