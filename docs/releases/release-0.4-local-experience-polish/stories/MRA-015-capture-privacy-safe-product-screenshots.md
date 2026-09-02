# MRA-015: Capture privacy-safe product screenshots

## Status

Implemented

## User story

As a visitor, I want to see the app without seeing private user data.

## Goal

Keep a safe set of real app shots. Make each shot easy to remake.

## Dependencies

`MRA-014`.

## Acceptance criteria

- [x] A dev-only Playwright workflow captures the real React application at deterministic desktop and mobile viewports.
- [x] Every application API request is intercepted with invented fixture data; the workflow does not read or seed PostgreSQL, uploaded files, Ollama, or the running Compose stack.
- [x] The checked gallery shows grounded chat with a citation, the document-management states, and the responsive mobile chat layout.
- [x] The root README and documentation index link to the screenshots, and the testing guide documents repeatable host and WSL-container commands.
- [x] The dependency and browser image use the same pinned Playwright version.

## Out of scope

End-to-end RAG validation, fixture persistence, a production demo mode, installing Playwright in application images, visual-regression baselines, marketing imagery, or copying any live application record is out of scope.
