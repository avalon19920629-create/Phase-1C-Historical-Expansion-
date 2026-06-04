# Historical Membership Engine Report — Phase 1C

## 1. Phase 1C objective

Phase 1C expands `data/processed/membership_changes.csv` backward so the engine has real S&P 500 change events before 2020 and can no longer silently treat the current S&P 500 membership as the historical universe for pre-2020 requests.

## 2. Sources investigated

| Source | Outcome | Limitation |
| --- | --- | --- |
| Wikipedia `List of S&P 500 companies` current constituent table | Investigated for current anchor context only. | Current-only anchor is not sufficient for unbiased 2018 reconstruction. |
| Wikipedia selected changes table | Ingested as bundled seed rows. | Wikipedia labels the table as selected changes; it is not a complete official event tape. |
| fja05680/sp500 GitHub historical datasets | Investigated, recorded in manifest, not ingested by default. | MIT repo, but README says early history derives from third-party/book-associated data and Wikipedia is not complete; provenance is mixed. |
| hanshof/sp500_constituents GitHub historical snapshots | Investigated, recorded in manifest, not ingested by default. | Snapshot provenance relies on project code/data and was not row-level audited here. |
| S&P DJI methodology and public announcements | Investigated as sanity-check context. | Useful for methodology and official announcements, but not practical as a single public CSV source. |

## 3. Sources successfully ingested

The default build ingests bundled, manually reviewed seed rows from Wikipedia's selected component changes table plus any rows placed in `data/raw/manual/membership_changes_manual.csv`.

## 4. Rows extracted per source

See `artifacts/source_manifest.csv`. The current default build extracted 230 rows from the bundled Wikipedia selected-changes seed, 120 ticker-level rows from the public fja05680 GitHub changes file, and 0 rows from the empty manual override file.

## 5. Earliest effective date

`2009-03-03`.

## 6. Latest effective date

`2026-01-14` after adding the public fja05680 compact changes source for post-2020 ticker-level events. The adapter layer supports adding later sources or manual rows without changing the schema.

## 7. Number of change events by year

See `artifacts/membership_change_coverage_by_year.csv` and `reports/reconstruction_validation.md` for the generated counts.

## 8. Supported date range after expansion

Change-event coverage now starts before `2010-01-01`, satisfying the event-history date target. Full constituent-list reconstruction remains unavailable unless a verified full snapshot anchor is supplied.

## 9. Confidence by period

| Period | Quality flag | Rationale |
| --- | --- | --- |
| Before 2009-03-03 | unavailable | No event coverage. |
| 2009-03-03 to 2020-05-22 | medium_for_event_history_only | Real selected-change rows exist, but the source is not guaranteed complete and no full anchor snapshot is bundled. |
| 2020-06-22 to 2026-01-14 | medium_for_event_history_only | Ticker-level public GitHub changes supplement the selected-change seed; no full anchor snapshot is bundled. |
| After 2026-01-14 | not fully covered by bundled data | Add updated public/manual sources for current coverage. |

## 10. Remaining gaps

1. Wikipedia selected changes are not a complete official event history.
2. A full point-in-time 2018 constituent snapshot is not bundled.
3. Public GitHub historical snapshot datasets were not ingested by default because their provenance and licensing chain were not audited to the same row-level standard requested for Phase 1C.
4. The API intentionally refuses to reconstruct member lists from a current-only anchor.

## 11. Example API results

`get_sp500_members("2018-12-31")` does **not** silently return a current-biased 2026 list. With the default bundled data it raises `InsufficientCoverageError` because no verified full constituent snapshot anchor is present. Returned member count is therefore `not_available`; quality flag is `insufficient`.

## 12. Whether the engine now satisfies the 2010-present target

The change-event dataset satisfies the date target because real rows start on `2009-03-03`, before `2010-01-01`, and extend through `2026-01-14`. The full-membership API target is partially satisfied: the request is safe because it refuses biased output, but it does not yet return a 500-member 2018 list without adding a verified snapshot source.

## 13. Next recommendation

Audit and ingest a full historical snapshot dataset (or licensed official constituent history) as a separate source with explicit license/provenance documentation. Once a vetted snapshot anchor is available, enable `get_sp500_members("2018-12-31")` to return a full list with a medium/high quality flag.
