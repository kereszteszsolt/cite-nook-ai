# MRA-014: Add browser favicon identity

## Status

Implemented

## User story

As a local user, I want to spot CiteNook by its browser icon.

## Goal

Use the same small mark in the app and browser tab.

## Dependencies

`MRA-013`.

## Acceptance criteria

- [x] The web application serves a project-owned vector favicon with an accessible title and the established CiteNook palette.
- [x] The favicon's public path is declared in `packages/brand/brand.json` and represented by the typed brand contract.
- [x] The HTML supplies the favicon before React loads, and the browser entrypoint applies the configured brand path without changing the technical app ID or package names.
- [x] Frontend and backend brand tests cover the asset contract, and the production web build includes the static SVG.

## Out of scope

Changing the wordmark, product name, technical identifiers, app icons for native platforms, a dark-mode icon set, or a broader visual redesign is out of scope.
