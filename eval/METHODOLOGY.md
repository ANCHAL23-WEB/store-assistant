# Evaluation Methodology

## Overview
This document describes how search relevance was evaluated for the Store Assistant project, including query selection, judgment criteria, and known limitations.

## Query Set
- **Total queries tested:** 30
- **Scored (relevance-judged):** 24
- **Skipped:** 6 — returned no results from any retrieval method, so no relevance judgment was possible

## Relevance Judging Process
1. Each of the 24 scorable queries was run against the search system.
2. Returned products were manually inspected and labeled relevant / not relevant to the query intent.
3. Labels were assigned by a single reviewer (project author), not crowd-sourced or independently verified.

## Known Bias / Limitation
Judgment labels were created by inspecting **live FAISS (semantic) search results only**. This introduces a self-fulfilling bias: products FAISS didn't surface were never seen or considered for labeling, even if they were actually relevant.

**Mitigation (not yet done):** candidate products from keyword/TF-IDF search should also be pulled in and judged before finalizing labels, so relevance judgments aren't circularly dependent on the system being evaluated. This is a known gap, documented here for transparency.

## Result Interpretation
Given the above, current relevance scores should be read as "FAISS's self-assessment," not an independent ground truth. Future work: rebuild the judgment set using pooled candidates from both retrieval methods.
