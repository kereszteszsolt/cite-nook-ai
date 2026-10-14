# MRA-030: Run existing checks in CI

## Status

Planned

## User story

As a maintainer, I want each code change to run the same basic checks.

## Goal

Catch a bad change with one small CI job.

## Dependencies

`MRA-029`.

## Acceptance criteria

- [ ] One GitHub Actions workflow runs on pull requests and pushes to the default branch.
- [ ] The job uses supported Node.js and Python versions and installs locked npm and uv dependencies.
- [ ] The job runs repository verification plus the existing lint, test, and build commands.
- [ ] CI tests run with mocked services and need no live PostgreSQL, Ollama, or model download.
- [ ] A failed command fails the job, and the local equivalent commands are listed in `docs/testing.md`.
- [ ] The workflow result is checked on GitHub and its URL is recorded in `verification.md`.

## Out of scope

This story does not add cloud deployment, secrets, a container registry, scheduled jobs, or live model evaluation in CI.
