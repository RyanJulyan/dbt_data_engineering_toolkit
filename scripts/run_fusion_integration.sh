#!/usr/bin/env bash
set -euo pipefail

target="${1:?usage: run_fusion_integration.sh TARGET}"

dbt deps --profiles-dir . --target "${target}"
dbt build \
  --profiles-dir . \
  --target "${target}" \
  --exclude package:dbt_project_evaluator \
  --full-refresh \
  --static-analysis=off \
  --no-manage-state \
  --vars '{deactivate_for_fusion: true}'

python ../scripts/dbt_coverage.py \
  --manifest target/manifest.json \
  --run-results target/run_results.json \
  --public-api ../macros/schema.yml \
  --macros-dir ../macros \
  --minimum 80 \
  --output target/dbt_coverage.json
