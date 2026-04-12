# Pipeline Audit Trail

**Run ID**: [RUN_ID]
**Started**: [TIMESTAMP]
**Spec**: [SPEC_ID]-[FEATURE_NAME]

<!--
  This is an append-only document. Each pipeline event appends a new section below.
  Never truncate or modify existing entries.

  Entry types:
  - Phase Start: When a phase begins execution
  - Phase Complete: When a phase passes its gate check
  - Decision: When any decision is made (auto-resolved or human-resolved)
  - Retry: When a retry is initiated after a gate failure
  - Pause: When the pipeline pauses for human input
  - Resume: When the pipeline resumes after a pause
  - Score: When the final scoring completes

  Format for each entry:

  ## Phase N: [Phase Name]
  - **Started**: [ISO 8601 timestamp]
  - **Completed**: [ISO 8601 timestamp]
  - **Duration**: [MM:SS]
  - **Gate**: [PASS|FAIL|PAUSE]
  - **Retry Count**: [N]
  - **Artifacts**: [comma-separated list of files produced]
  - **Decisions**:
    - [Auto-resolved|Human-resolved]: "[question]" → "[answer]" (evidence: [file:line])

  ### Retry [N] (if applicable)
  - **Timestamp**: [ISO 8601]
  - **Failure Diagnosis**: [root cause identified]
  - **Strategy**: [fix approach — must differ from previous attempts]
  - **Outcome**: [resolved|failed]

  ### Pause (if applicable)
  - **Timestamp**: [ISO 8601]
  - **Reason**: [clarification|constitution_conflict|timeout|retry_exhausted|destructive_op]
  - **Question**: [the specific question surfaced]
  - **Options**: [list of resolution options]

  ### Resume (if applicable)
  - **Timestamp**: [ISO 8601]
  - **Answer**: [user's response]
  - **Encoded Into**: [artifact updated with the answer]
-->
