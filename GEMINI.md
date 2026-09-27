# Munich Marathon Sub-4 Training Project Rules

## 🌐 Language Policy
- **The Dashboard (`index.html`) MUST ALWAYS be strictly in English.**
- All UI elements, titles, subtitles, badges, coach insights, drawer descriptions, metric labels, and exercise routines must remain 100% in English.
- Do NOT mix German and English on the site.
- Even if the user submits training notes or requests in German, the site content, workout descriptions, and coach insights on `index.html` must be written exclusively in English.
- Proper German nouns for locations (e.g. Leopoldstraße, Englischer Garten, Olympiastadion) or the official event name (Generali München Marathon) are permitted.

## 🚀 GitHub Desktop Push-to-Origin Workflow (MANDATORY)
- **The user uses GitHub Desktop to publish updates.**
- The local Git repository tracked by GitHub Desktop is located at:
  `C:\Users\chaxyz\Documents\GitHub\munich-marathon-sub4`
- Whenever site files (`index.html`, `training_data.json`, etc.) are updated in `C:\Users\chaxyz\.gemini\antigravity\scratch\MarathonTraining`, the assistant **MUST ALWAYS**:
  1. Copy the updated files to `C:\Users\chaxyz\Documents\GitHub\munich-marathon-sub4`.
  2. Stage the changes: `git -C "C:\Users\chaxyz\Documents\GitHub\munich-marathon-sub4" add .`
  3. Commit the changes: `git -C "C:\Users\chaxyz\Documents\GitHub\munich-marathon-sub4" commit -m "..."`
  4. Inform the user that the commit is created and ready for them to hit **"Push to origin"** in GitHub Desktop.
- **NEVER** leave the repository uncommitted or forget to copy files over. The user must always find the blue "Push to origin" button ready when they open GitHub Desktop.

## 🏃 COROS FIT File Analysis Workflow
- When the user provides a `.fit` file path (e.g. `CorosData/<id>.fit`):
  - Always use `fitdecode` (never `fitparse`, which crashes on Coros uint32 developer fields).
  - Run the automated analyzer script:
    `python .agents/skills/coros-fit-analyzer/scripts/analyze_fit.py "<path_to_fit>" --sync`
  - This automatically extracts moving pace, heart rate, cadence, power, stance time (GCT), vertical oscillation, 1km splits, pauses, updates `parsed_activities.csv`, `training_data.json`, updates KPIs/monthly stats, and stages/commits to the GitHub repository.
  - Update `index.html` with workout completion, coach insight, drawer cards, and readiness bars.
  - Sync and commit `index.html` and `training_data.json` to `munich-marathon-sub4`.
