# Library Management System (Oracle 19c)

A relational schema for a library management system, built incrementally with a focus on data integrity: proper normalization, deliberate `CASCADE`/`RESTRICT` choices on every foreign key, and PL/SQL triggers enforcing rules Oracle's `CHECK` constraints can't express (e.g. anything involving `SYSDATE`, cross-table validation, or cross-table side effects).

## Structure

```
Tables/       -- CREATE TABLE statements, numbered in FK dependency order
Triggers/     -- CREATE OR REPLACE TRIGGER statements, numbered by table dependency
Seed/         -- sample INSERT scripts for manual/local testing
build.sql   -- master script: drop → create → verify, idempotent
```

## Requirements

- Oracle Database 19c (uses `GENERATED ALWAYS AS IDENTITY`, `FETCH FIRST`/`ROWNUM`, native `%TYPE`)
- SQL*Plus or SQL Developer

## Running the Build

```sql
SQL> @build.sql
```

This is a **full rebuild script** — it drops all ten tables (`CASCADE CONSTRAINTS`, safe to run on a fresh schema where nothing exists yet), recreates everything, compiles all triggers, and runs a verification block (table count, trigger status, invalid-object check). It is safe to re-run at any time; it's idempotent by design.

`SET DEFINE OFF` is set at the top — Oracle's SQL*Plus treats `&` as a substitution-variable prefix by default, which will silently corrupt or block any INSERT containing an ampersand (e.g. `'Secker & Warburg'`) unless this is off.

## Entity-Relationship Overview

```
publishers ──< books >── author authors (via book_authors, many-to-many)
                │
                └──< book_copies  (one catalog title → many physical copies)
                          │
                          └──< loans >── members
                                  │            │
                                  └──< fines   └──< reservations
                                                     │
                          members ──< member_status_history
```

- **`publishers` / `authors`** — independent reference data.
- **`books`** — the catalog record (title, ISBN, publisher). Not the physical item.
- **`book_authors`** — junction table resolving the many-to-many between books and authors.
- **`book_copies`** — the physical inventory. One `books` row can have N `book_copies` rows, each independently tracked (shelf location, status, acquisition date).
- **`members`** — library patrons.
- **`loans`** — the transactional core: links one `book_copies` row to one `member` for a date range.
- **`fines`** — penalties, anchored to the specific `loan` that caused them (not directly to `members`), so every fine is traceable to its originating transaction.
- **`reservations`** — a queue against a `books` title (not a specific copy), since you can't know in advance which physical copy will free up first.
- **`member_status_history`** — append-only audit log of every `members.member_status` transition, with a reason and timestamp. Exists because a flat status column can only ever say *what* a member's status is, never *why* it changed or *when*.

## Deliberate Design Decisions

**Catalog vs. physical copy split.** `books` and `book_copies` are separate tables, not one. A library can own multiple physical copies of the same title, and each copy has its own independent state (on shelf, on loan, lost, damaged). Collapsing this into a single table breaks the moment a library owns more than one copy of anything.

**`ON DELETE CASCADE` vs. `RESTRICT` (Oracle's default) — applied deliberately per relationship, not reflexively:**
| Relationship | Behavior | Reasoning |
|---|---|---|
| `book_authors → books`, `book_authors → authors` | `CASCADE` | A junction row has no independent meaning without both parents. |
| `books → publishers` | `RESTRICT` (default) | A book is a real catalog record; a publisher deletion should never silently wipe it. |
| `book_copies → books` | `RESTRICT` (default) | A copy is a real, physical, trackable object; it shouldn't vanish because a catalog record was removed. |
| `loans → book_copies`, `loans → members` | `RESTRICT` (default) | Loans are transactional/audit records — they should never be deletable-by-cascade. |

The rule: `CASCADE` only when the child row has no independent existence or meaning without its parent. Everything else defaults to `RESTRICT`.

**Surrogate keys via `GENERATED ALWAYS AS IDENTITY`.** Modern Oracle 12c+ syntax, not the legacy `SEQUENCE` + trigger pattern. `GENERATED ALWAYS` (not `BY DEFAULT`) deliberately forbids manual ID insertion — surrogate keys should never be user-supplied.

**`SYSDATE` cannot appear in a `CHECK` constraint** (Oracle requires `CHECK` expressions to be deterministic). Anywhere the original design called for a `SYSDATE`-based rule (e.g. "date of birth can't be in the future"), that logic lives in a `BEFORE INSERT OR UPDATE` trigger instead. `SYSDATE` *is* legal inside a `DEFAULT` clause — different mechanism, different rule.

**`member_status_history` exists instead of a single `suspension_reason` column** on `members`. A flat reason column can only hold the *current* reason, silently overwriting the previous one on every subsequent status change. A history table preserves the full transition record.

**Reservation fulfillment uses explicit row-locking (`SELECT ... FOR UPDATE`).** When a copy is returned and a reservation queue exists for that title, the trigger must find and lock the oldest `WAITING` reservation before assigning the copy — without the lock, two concurrent returns/reservations could race and double-assign a copy. Note: `FOR UPDATE` cannot be combined directly with `FETCH FIRST n ROWS ONLY` or an `ORDER BY` inside the same locked query (`ORA-02014`) — the trigger resolves this by first identifying the target row's ID (`ORDER BY` + `ROWNUM = 1`, no lock), then locking that specific row by primary key in a separate query.

## Triggers

| Trigger | Table | Fires On | Purpose |
|---|---|---|---|
| `trg_author_dob_check` | `authors` | `BEFORE INSERT/UPDATE` | Blocks future `date_of_birth` values (can't be a `CHECK`, needs `SYSDATE`). |
| `trg_prevent_sole_author_delete` | `authors` | `BEFORE DELETE` | Blocks deleting an author who is the *sole* author of any book, preventing silent orphaned catalog records. |
| `trg_loan_set_due_date` | `loans` | `BEFORE INSERT` | Auto-sets `due_date` to `checkout_date + 14` if not explicitly provided. |
| `trg_loan_copy_status` | `loans` | `AFTER INSERT/UPDATE OF return_date` | On checkout: flips the copy to `ON_LOAN`. On return: checks for a waiting reservation and either fulfills it (assigning the copy straight to the next member) or marks the copy `AVAILABLE`. |
| `trg_fine_suspend_member` | `fines` | `AFTER INSERT` | Sums a member's unpaid fines; suspends the member and logs the transition to `member_status_history` if the total crosses the threshold. |
| `trg_res_block_if_available` | `reservations` | `BEFORE INSERT` | Blocks a reservation if any copy of the title is currently `AVAILABLE` — reservations only make sense when nothing's on the shelf. |

## Known Gaps (Not Yet Solved — Deliberately)

These are documented, not accidental oversights. Flagged here so they aren't rediscovered the hard way:

- **No protection against double-loaning an already-`ON_LOAN` copy.** The FK on `loans.copy_id` only checks the copy exists, not that it's actually available.
- **`reservations.reservation_status` has no reason-tracking**, unlike `members` — a `CANCELLED` reservation doesn't record *why*.
- **`trg_loan_copy_status` fetches `v_reservation_member` but never uses it** — there is no notification mechanism yet telling a member their reservation was fulfilled.
- **Case/whitespace-fragile `UNIQUE` constraints** on `publishers.publisher_name`, `books.isbn`, `members.email`, `publishers.contact_email` — `'John@x.com'` and `'john@x.com'` are currently treated as distinct. Would need function-based unique indexes on `LOWER(TRIM(...))` to close.
- **No overdue-fine automation** — nothing currently compares `loans.due_date` to `SYSDATE` and auto-generates a `fines` row; this relies on manual staff action today.

## Testing Notes

- Ampersands in string literals (e.g. publisher names like `Secker & Warburg`) require `SET DEFINE OFF` in the session first, or SQL*Plus will interpret `&` as a substitution-variable prompt and silently abort the statement if cancelled.
- `SELECT ... INTO` in PL/SQL raises `NO_DATA_FOUND` on zero matching rows rather than returning an empty result — this is used deliberately as control flow in `trg_loan_copy_status` and `trg_fine_suspend_member`, not treated as an unexpected error.
- After running the build script, always check `SELECT * FROM user_objects WHERE status != 'VALID'` — a trigger can compile with a warning and end up `INVALID` without an obviously loud failure.

- **`generate_overdue_fines` requires manual recompilation after every full rebuild.** This procedure is intentionally *not* included in `00_run_full_build.sql` — a scheduled `DBMS_SCHEDULER` job calling it would fail mid-rebuild if it fired while tables are being dropped and recreated. Because it's excluded from the automated script, dropping and recreating `fines` (as Step 1 does) leaves the procedure `INVALID` — Oracle flags any object that depends on a dropped table this way, even after the table is recreated identically, since the compiled code no longer matches a known-valid definition. After any full rebuild, run:
```sql
  ALTER PROCEDURE generate_overdue_fines COMPILE;
```
  and re-check `SELECT * FROM user_objects WHERE status != 'VALID'` before assuming the schema is ready.

> **Note:** `trg_fine_suspend_member` is a **compound trigger**, not a plain row-level trigger. The original version queried `fines` — the table it's defined on — from within an `AFTER INSERT ... FOR EACH ROW` block, which raises `ORA-04091: table is mutating` at runtime (a row-level trigger cannot query its own table while the triggering statement is still in progress). The fix separates row-level work (`AFTER EACH ROW`: record which `loan_id`s were touched) from the actual suspension logic (`AFTER STATEMENT`: runs once, after the insert fully completes, when querying `fines` is legal again).

## Resolved Since Initial Build

- **Double-loan prevention** (`trg_prevent_double_loan`) — blocks creating a new loan against a copy that isn't currently `AVAILABLE`.
- **Overdue-fine automation** (`generate_overdue_fines` procedure + `DBMS_SCHEDULER` job, `Jobs/`) — scans nightly for loans past `due_date` with no `return_date`, generates a `LATE_RETURN` fine scaled by days overdue, guarded against duplicate fines on repeated runs.
- **`trg_fine_suspend_member` mutating-table bug** — discovered when `generate_overdue_fines` became the first code path all session to actually fire a real `INSERT INTO fines`; fixed via compound trigger (see note above).