# MRA-001: Run the branded local monorepo

## Status

Implemented

## User story

As a local user, I want one command to start CiteNook so I can use it with no account.

## Goal

Run the full app on one PC. Keep its data and brand.

## Dependencies

None.

## Acceptance criteria

- [x] The repository is an npm-workspace Turborepo containing React, Python API, and brand workspaces.
- [x] The default Compose stack runs web, API, worker, and PostgreSQL/pgvector while using a configurable external Ollama instance.
- [x] An optional Compose override runs Ollama as a separate service without installing it in an application container.
- [x] PostgreSQL records, uploaded files, and optional container-managed Ollama models use named persistent volumes.
- [x] The display identity comes from one replaceable brand JSON file and matches the documented CiteNook identities.
- [x] The developer metadata is Keresztes Zsolt and https://kereszteszsolt.hu.
- [x] Hand-authored project source files keep the short Apache-2.0 SPDX header, while standard and configuration files do not receive it.

## Out of scope

Features outside the Release 0.1 boundary documented in the release README.
