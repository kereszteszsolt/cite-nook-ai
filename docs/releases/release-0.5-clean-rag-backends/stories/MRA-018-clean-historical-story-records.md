# MRA-018: Clean the historical story records

## Status

Implemented

## User story

As a maintainer, I want short and clear story files so each past change is easy to review.

## Goal

Keep each story small. Move long proof to release files and keep the shipped facts.

## Dependencies

None.

## Acceptance criteria

- [x] Stories `MRA-001` through `MRA-017` use the current story sections and keep their implemented status.
- [x] Each old story has four to eight short, checked criteria that preserve its shipped result.
- [x] Long commands, test totals, and proof move to a `verification.md` file for the matching release.
- [x] Issue and limitation sections are removed from every story file.
- [x] Useful future work moves to the roadmap without changing the scope of a past release.
- [x] Each release map links to its stories and its verification file.
- [x] The repository check applies the same format and reading rules to every story.

## Out of scope

This story does not change app code, product behavior, or the result of any past release.
