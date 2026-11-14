QuerySage Supplementary Extraction Table
=========================================

This is the extraction table referenced in the manuscript's Data Availability
declaration, underlying the counts and quality scores reported in Sections 6
and 7. It accompanies QuerySage_AIR_Springer_submission_Final.docx.

SCOPE

56 rows total. 36 of these form the reviewed corpus that Sections 5-7 discuss
and score (screening_status = "included (cited)"). The remaining 20 rows are
kept for transparency and fall into three groups:

  - excluded (various reasons): screened and found out of scope, duplicate,
    or otherwise not a fit, with the reasoning recorded in `notes`
  - background citations ("DONE - cited in 2.2"): pre-LLM lineage papers
    cited in Section 2 for historical context, not reviewed as tuning
    systems
  - future-work candidates ("included - recommended, pending extraction"):
    screened as in-scope, with factual methodology data already extracted,
    but not yet drafted into the manuscript body or given a reference-list
    entry. They do not count toward any number reported in the paper.

COLUMNS

Bibliographic: system_name, citation_key, year, venue, venue_type
Classification: task (T1-T6, see Section 4), role (R1-R5, see Section 4)
Method: model_used, model_version_stated, temperature_stated,
  weights_updated, retrieval_used, retrieval_source, search_algorithm,
  safety_checks, equivalence_verified
Experimental setup: engines, engine_versions_stated, benchmarks,
  scale_factor, hardware_stated, repetitions, variance_reported
Results: baseline_type, gain_reported, gain_baseline, cost_reported,
  artifact_released
Additional fields tracked but not yet populated for most rows: output_schema,
  reversible_only, inverse_recorded, tokens_reported, transfer_tested
Quality rubric (Table 2 of the manuscript, each scored 0/1/2):
  c1_live_execution, c2_protocol, c3_statistical_reporting, c4_baselines,
  c5_workload_validity, c6_correctness, c7_cost, c8_reproducibility,
  total_score
notes: evidence and reasoning for the classification, extraction, and
  rubric scores above. Each verified claim names its source (an arXiv ID,
  a DOI, or "per abstract" where a detail is stated without an external
  source to check against). Where a value could not be verified, the note
  says so explicitly rather than the cell being silently left blank with
  no explanation.

HOW TO READ A ROW

Each row's `notes` typically has three parts, separated by " | ":
  1. A short tag or summary of what makes the system relevant.
  2. What was verified, how, and what remains unconfirmed.
  3. "Rubric basis: ..." -- a one-line reason for each of the eight
     quality-criterion scores, so a reader can check the scoring in
     Table 2 / Fig. 2 against the stated evidence rather than taking it
     on trust.

LIMITATIONS, STATED PLAINLY

The quality-rubric scores (c1-c8) were assigned from abstracts, not full
text, except where a row's notes say otherwise. They are the authors'
assessment, drafted with AI assistance and subject to author review before
the figures and counts derived from them are treated as final.
