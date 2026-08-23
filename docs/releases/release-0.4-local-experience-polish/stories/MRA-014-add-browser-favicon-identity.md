# MRA-014: Add browser favicon identity

## Status

Implemented

## User story

As a local CiteNook user, I want the browser tab to carry the same restrained visual identity as the application so that CiteNook is recognizable among other local tools.

## Acceptance criteria

- [x] The web application serves a project-owned vector favicon with an accessible title and the established CiteNook palette.
- [x] The favicon's public path is declared in `packages/brand/brand.json` and represented by the typed brand contract.
- [x] The HTML supplies the favicon before React loads, and the browser entrypoint applies the configured brand path without changing the technical app ID or package names.
- [x] Frontend and backend brand tests cover the asset contract, and the production web build includes the static SVG.

## Out of scope

Changing the wordmark, product name, technical identifiers, app icons for native platforms, a dark-mode icon set, or a broader visual redesign is out of scope.

## Implementation evidence

- `apps/web/public/favicon.svg` combines an open-book silhouette with a citation mark using the existing accent, surface, and soft-accent colors.
- `packages/brand/brand.json` declares `assets.favicon`; the TypeScript brand interface and both brand test suites cover it.
- `apps/web/index.html` supplies the initial SVG favicon link, and `apps/web/src/main.tsx` updates that link from the central brand configuration.
- `docs/brand-configuration.md` documents the source asset and its public brand path.

## Verification

Run the API and brand tests, the web lint/build, the repository audit, and `git diff --check`. Inspect `apps/web/dist/favicon.svg` after the production build and load the app once in Chromium to confirm the linked SVG returns successfully.

## Verification evidence

- The focused API brand test passed, and Ruff passed for the changed API brand files.
- The brand package test passed; web TypeScript lint and the Vite production build passed in the Linux Node project image.
- The production build contained `dist/favicon.svg`.
- The repository audit passed with 14 stories, and the MRA-014 staged diff passed `git diff --check`.
