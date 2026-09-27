---
name: coros-fit-analyzer
description: >-
  Analyze COROS .fit activity files for marathon training workouts. Extracts distance,
  moving pace, heart rate, cadence, running power, ground contact time, vertical oscillation,
  pause detection, 1km splits, and lap breakdowns. Automatically updates parsed_activities.csv,
  training_data.json, index.html, and stages/commits to the GitHub repository so the user
  only needs to hit "Push to origin" in GitHub Desktop.
---

# COROS FIT File Analyzer & Marathon Training Syncer

This skill provides an automated, efficient workflow for processing COROS `.fit` workout files, generating coach insights, updating the Munich Marathon dashboard, and preparing the GitHub commit for one-click pushing.

## Quick Start / Command

When the user provides a `.fit` file path (e.g. `CorosData/<id>.fit`):

```bash
# 1. Run detailed biometric analysis and split extraction
python .agents/skills/coros-fit-analyzer/scripts/analyze_fit.py "<path_to_fit_file>"

# 2. Or run analysis AND sync to parsed_activities.csv, training_data.json, and GitHub repo
python .agents/skills/coros-fit-analyzer/scripts/analyze_fit.py "<path_to_fit_file>" --sync --commit-msg "Add <Workout Title> analysis, sync to <N> runs (<Days> days to Munich)"
```

## Standard Analysis & Site Update Workflow

1. **Parse the FIT File**:
   - Always use `fitdecode` (never `fitparse`, as Coros developer field definitions cause `FitParseError: Invalid field size`).
   - Run `analyze_fit.py` to extract:
     - Moving time vs. elapsed time
     - Moving pace and average/max heart rate
     - Cadence (spm) and Running Power (W)
     - Ground Contact Time (ms) and Vertical Oscillation (mm)
     - Lap breakdowns & 1 km splits
     - Pauses (>5s) with exact timestamps and kilometer markers

2. **Coach Analysis & Biometrics Review**:
   - Compare lap/split pace against Target Marathon Pace (5:34–5:38/km) and workout objectives.
   - Evaluate cardiac drift (HR vs. Pace progression).
   - Evaluate biomechanics (cadence maintenance, GCT changes under fatigue, vertical oscillation).
   - Correlate with user notes (fueling, hydration, shoe comfort, terrain, weather).

3. **Update Site Content (`index.html`)**:
   - **Language Policy**: Strictly 100% English across all cards, drawers, insights, and labels.
   - **Header & Hero**: Update total runs synced count, total running km, days to race countdown, and latest quality block.
   - **Biometrics & Readiness Tab**: Update readiness percentage, endurance/fueling bars, and embed a new `Coach Insight (<Date>):` block.
   - **Master Plan Tab**: Mark the day's workout box `completed`, check the checkbox (`checked`), update the week header status and mileage badge, and fill the 3 drawer cards (pacing/splits, biomechanics/gear, fueling/recovery).
   - **Interactive COROS Log**: Append the new activity to the embedded `activities` array in `<script>`, update `monthlyData`, and update `kpis`.

4. **GitHub Desktop Push-to-Origin Sync**:
   - The user's active GitHub repository tracked by GitHub Desktop is:
     `C:\Users\chaxyz\Documents\GitHub\munich-marathon-sub4`
   - Whenever `index.html` or `training_data.json` is updated in the workspace, **ALWAYS**:
     1. Copy `index.html` and `training_data.json` to `C:\Users\chaxyz\Documents\GitHub\munich-marathon-sub4`.
     2. Stage the changes: `git -C "C:\Users\chaxyz\Documents\GitHub\munich-marathon-sub4" add index.html training_data.json`
     3. Commit the changes: `git -C "C:\Users\chaxyz\Documents\GitHub\munich-marathon-sub4" commit -m "..."`
     4. Notify the user that the commit is staged and ready for them to hit **"Push to origin"** in GitHub Desktop.
