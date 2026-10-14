# Image audit rules — v0.8

Pinned source: `generation-policy-lock.json`. Pixel and supplied observation checks are separate from actual human inspection and channel eligibility.

| Rule | Check |
| --- | --- |
| IMG-GALLERY-001/002 | Live gallery MAIN + PT01–PT08 coverage; review missing slots |
| IMG-TECH-001/002/003/005 | Supported static formats; longest edge 500–10,000; below 1,000 is zoom REVIEW; no animation |
| IMG-MAIN-001/002 | White-border and subject-extent heuristics; require visual confirmation |
| IMG-MAIN-003 | Explicit reported added overlay; OCR alone can be authentic chassis text |
| IMG-GALLERY-003 | Perceptual near-duplicate heuristic |
| IMG-VISUAL-001/002/003 | Observations present, each captured slot covered, actual 100% and 200px reviews recorded |
| IMG-EVIDENCE-003 | Observation SHA-256 matches current downloaded bytes and slot exists |
| IMG-IDENTITY/CLAIM/CONTENT/RIGHTS | Product identity, mapped claims, promotional flags, asset provenance |
| IMG-PRODUCT-001 | Reported peripherals, geometry mismatch or removal of authentic factory marks |
| IMG-PORTS-001 | PT08 physical connector views/types/counts verified |
| IMG-SEMANTIC-001/002 | Canonical primary fact IDs; overlap >20% requires review |

Square shape and fixed 2000px output are retired. Do not resize merely to satisfy historical settings. The live gallery has nine publication slots; the generation project's two enhanced MAIN candidates are additional production assets, not two required live Amazon images. Enhanced MAIN eligibility remains separate.

Observations are scoped under `listings.<ASIN>.images`; legacy single-listing input remains readable. Each record uses explicit `slot`, `sha256`, `visual_review_100pct`, `visual_review_200px`, observed flags, exact-model identity, claims and licensed provenance. Hashes bind bytes, not truthfulness: only record actual manual reviews. Missing/stale records stay REVIEW; reported problems are retained for inspection. `physical_port_map_verified` is required for PT08.

PT observations provide nonempty `primary_fact_ids`, based on manual semantic review. Equivalent claims share one ID. Exclude only OEM/model/navigation labels. Pairwise overlap is intersection size divided by the smaller fact count. Empty/unavailable mappings get REVIEW and no invented percentage. Repetition is a review item, not automatic image rejection.

Generation slot ownership: PT01 purchase reason; PT02 use scene; PT03 sole full base configuration; PT04 display/form; PT05 task flow; PT06 input details on white; PT07 unused verified value without warranty/service advertising; PT08 physical port map/connectivity. Review ownership manually; the auditor does not infer it from OCR. Computer-only imagery includes no extra devices/accessories. Authorized faithful AI reproduction is allowed only with exact-model fidelity evidence, genuine factory marks and rights; AI use alone is not a failure or a PASS.

Remaining manual controls include schema-3 logo asset/master/final hashes and actual visible bounds, style lock, native clarity, DPI metadata, faithful keyboard/ports, synthetic performer metadata, slot ownership, and applicable marketplace rules. A basic observation record does not establish production full-gallery QA, remote delivery or Amazon acceptance.
