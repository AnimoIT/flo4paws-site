# W-series register index (flo4paws-site)

Ruling A (W6b, 5 Sep 2026): the website series keeps its own register here, under its own prefixes, so it cannot collide with the S-series in `animoit-infra`. The numbers were kept and the prefix changed: infra `BL-657` and site `WBL-657` are different items.

Prefixes: backlog `WBL-`, findings `WF-`. Entries live in `W<n>_BACKLOG_entries.md` and `W<n>_FINDINGS_entries.md`; this file only indexes them.

| Session | Backlog | Findings |
|---|---|---|
| W3 | WBL-643-654 | WF-82-87 |
| W4 | WBL-655-659 | WF-88-91 |
| W5 | WBL-660-677 | WF-92-100 |
| W6 | WBL-678-687 (was W6-BL1-10) | WF-101-105 (was W6-F1-5) |
| W6b | WBL-688-690 | WF-106-109 |

    NEXT_WBL: WBL-691
    NEXT_WF: WF-110

Census instruments: `grep -hoE '^### WBL-[0-9]+' docs/W*_entries.md | wc -l` and the same for `WF-`. A file existing is not registration; the heading count is.

History: W3-W5 allocated BL-643-677 and F-82-100 from the infra sequence without landing them in infra, while S217-S219 allocated BL-643-658 for API items. All sixteen of BL-643-658 had two owners with different titles when measured in W6b, not the five the W6 handover reported.
