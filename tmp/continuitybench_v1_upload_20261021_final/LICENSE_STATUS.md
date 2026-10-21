# LICENSE_STATUS

## Current Evidence

The root repository contains an MIT license in `LICENSE`. The available evidence does not establish that this license applies to the benchmark dataset or to every associated artifact.

## Unresolved Scope

Licensing scope is unresolved for:

- The 84-case dataset and source conversations.
- Gold labels, provenance, and evaluator annotations.
- Human-review and reconciliation artifacts.
- Generated model outputs and retrieval evidence.
- Derived result and analysis files.

The intended policy is CC BY 4.0 for the original benchmark dataset, gold labels, schema, data dictionary, aggregate analysis, and per-case metric results, subject to explicit confirmation that the owner has the necessary rights to grant it. This is a planned license, not a completed grant. Generated model outputs and human-review artifacts may require separate permission checks.

The release candidate is **not cleared for public distribution** until these decisions are resolved. This file is a status notice, not a license grant. The MIT license must not be copied into the release candidate as if it applied to all included artifacts.

If the target release format requires a license file, the packaging manifest marks that requirement as a publication blocker. No CC BY 4.0 file is included until the owner explicitly authorizes the grant and the package scope is confirmed.

## Owner-Provided Provenance

The owner confirms that all 84 conversations were generated specifically for ContinuityBench using ChatGPT/Codex, manually reviewed by the owner, and, to the owner's knowledge, did not use third-party conversations or copied external material. This is owner-provided provenance, not independent verification or legal clearance.


## Additional Rights Checks

The included per-case results are derived from local Llama 3.1 and Qwen3 outputs. Available local repository documentation did not establish complete redistribution terms for those generated outputs. Do not assume model terms authorize publication of every generated response or derived artifact.

