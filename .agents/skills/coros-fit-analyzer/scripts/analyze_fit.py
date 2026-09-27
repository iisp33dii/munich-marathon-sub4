#!/usr/bin/env python3
"""
COROS FIT File Analyzer & Marathon Training Syncer
Analyzes Coros .fit files using fitdecode, outputs biometric breakdowns,
and optionally syncs training_data.json, parsed_activities.csv, and GitHub repo.
"""

import sys
import os
import argparse
import datetime
import json
import subprocess
import shutil
import pandas as pd
import fitdecode

# Set stdout to UTF-8 to prevent Windows terminal charmap encoding errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# Default paths
WORKSPACE_DIR = r"C:\Users\chaxyz\.gemini\antigravity\scratch\MarathonTraining"
REPO_DIR = r"C:\Users\chaxyz\Documents\GitHub\munich-marathon-sub4"
CSV_PATH = os.path.join(WORKSPACE_DIR, "parsed_activities.csv")
JSON_PATH = os.path.join(WORKSPACE_DIR, "training_data.json")
INDEX_PATH = os.path.join(WORKSPACE_DIR, "index.html")
RACE_DATE = datetime.date(2026, 10, 11)


def parse_fit_file(fit_path):
    if not os.path.exists(fit_path):
        raise FileNotFoundError(f"FIT file not found: {fit_path}")

    sessions = []
    laps = []
    records = []
    events = []

    with fitdecode.FitReader(fit_path) as fit:
        for frame in fit:
            if isinstance(frame, fitdecode.FitDataMessage):
                if frame.name == 'session':
                    sessions.append({f.name: f.value for f in frame.fields})
                elif frame.name == 'lap':
                    laps.append({f.name: f.value for f in frame.fields})
                elif frame.name == 'record':
                    records.append({f.name: f.value for f in frame.fields})
                elif frame.name == 'event':
                    events.append({f.name: f.value for f in frame.fields})

    session = sessions[0] if sessions else {}
    df_rec = pd.DataFrame(records)
    if not df_rec.empty and 'timestamp' in df_rec.columns:
        df_rec['timestamp'] = pd.to_datetime(df_rec['timestamp'])
        if 'distance' in df_rec.columns:
            df_rec['distance_km'] = df_rec['distance'] / 1000.0
        if 'cadence' in df_rec.columns:
            df_rec['cadence_spm'] = df_rec['cadence'] * 2

    return session, laps, df_rec, events


def print_analysis(session, laps, df_rec, events, fit_filename):
    print("=" * 65)
    print(f"🏃 COROS RUN ANALYSIS: {fit_filename}")
    print("=" * 65)

    dist_km = (session.get('total_distance') or 0) / 1000.0
    timer_sec = session.get('total_timer_time') or 0
    elapsed_sec = session.get('total_elapsed_time') or 0
    avg_hr = session.get('avg_heart_rate') or 0
    max_hr = session.get('max_heart_rate') or 0
    cad_spm = (session.get('avg_running_cadence') or 0) * 2
    avg_pwr = session.get('avg_power') or 0
    gct = session.get('avg_stance_time') or 0
    vo = session.get('avg_vertical_oscillation') or 0
    temp = session.get('avg_temperature') or 0
    calories = session.get('total_calories') or 0
    ascent = session.get('total_ascent') or 0
    descent = session.get('total_descent') or 0
    start_time = session.get('start_time')

    mov_m, mov_s = divmod(int(timer_sec), 60)
    mov_h, mov_m = divmod(mov_m, 60)
    pace_sec = (timer_sec / dist_km) if dist_km > 0 else 0
    pm, ps = divmod(int(pace_sec), 60)

    print(f"📅 Start Time:   {start_time}")
    print(f"📏 Distance:     {dist_km:.2f} km")
    print(f"⏱️ Moving Time:  {mov_h}h {mov_m:02d}m {mov_s:02d}s (Elapsed: {int(elapsed_sec//60)}m {int(elapsed_sec%60):02d}s)")
    print(f"⚡ Moving Pace:  {pm}:{ps:02d} /km")
    print(f"❤️ Heart Rate:   Avg {avg_hr} bpm | Max {max_hr} bpm")
    print(f"🦶 Cadence:      {cad_spm} spm")
    print(f"⚡ Power:        {avg_pwr} W")
    print(f"⏱️ Ground Contact: {gct} ms | Vert Osc: {vo} mm")
    print(f"🌡️ Temperature:  {temp} °C | Calories: {calories} kcal | Elev: +{ascent}m / -{descent}m")

    # Laps
    print("\n--- LAPS BREAKDOWN ---")
    for i, l in enumerate(laps):
        l_dist = (l.get('total_distance') or 0) / 1000.0
        l_dur = (l.get('total_timer_time') or 0) / 60.0
        l_hr = l.get('avg_heart_rate') or 0
        l_max_hr = l.get('max_heart_rate') or 0
        l_cad = (l.get('avg_running_cadence') or 0) * 2
        l_pwr = l.get('avg_power') or 0
        l_gct = l.get('avg_stance_time') or 0
        l_spd = l.get('enhanced_avg_speed') or l.get('avg_speed') or 0
        l_pace_sec = (1000.0 / l_spd) if l_spd > 0 else 0
        l_pm, l_ps = divmod(int(l_pace_sec), 60)
        print(f"Lap {i+1:2d}: {l_dist:5.2f} km | {l_dur:5.2f} min | Pace {l_pm}:{l_ps:02d}/km | HR {l_hr:3d} (max {l_max_hr:3d}) | Cad {l_cad:3d} | Pwr {l_pwr:3d}W | GCT {l_gct:.0f}ms")

    # Pauses (>5s)
    if not df_rec.empty and 'timestamp' in df_rec.columns and 'distance_km' in df_rec.columns:
        df_rec['time_diff'] = df_rec['timestamp'].diff().dt.total_seconds()
        pauses = df_rec[df_rec['time_diff'] > 5]
        if not pauses.empty:
            print("\n--- NOTABLE PAUSES (>5s) ---")
            for _, r in pauses.iterrows():
                print(f"At {r['distance_km']:.2f} km: {r['time_diff']:.0f}s pause at {r['timestamp']}")

    # 1km Splits
    if not df_rec.empty and 'distance_km' in df_rec.columns:
        print("\n--- 1 KM SPLITS ---")
        df_rec['km_bin'] = df_rec['distance_km'].astype(int) + 1
        splits = []
        for km, grp in df_rec.groupby('km_bin'):
            if len(grp) < 3:
                continue
            dur_sec = (grp['timestamp'].iloc[-1] - grp['timestamp'].iloc[0]).total_seconds()
            avg_hr_split = grp['heart_rate'].mean() if 'heart_rate' in grp else 0
            cad_split = grp['cadence_spm'].mean() if 'cadence_spm' in grp else 0
            pwr_split = grp['power'].mean() if 'power' in grp else 0
            if 'speed' in grp:
                mov_spd = grp[grp['speed'] > 1.0]['speed'].mean()
                s_pace = (1000.0 / mov_spd) if mov_spd > 0 else 0
                spm, sps = divmod(int(s_pace), 60)
                pace_str = f"{spm}:{sps:02d}"
            else:
                pace_str = "N/A"
            splits.append({
                'KM': km,
                'Moving Pace': pace_str,
                'Elapsed (s)': f"{dur_sec:.0f}",
                'Avg HR': f"{avg_hr_split:.1f}",
                'Cadence': f"{cad_split:.1f}",
                'Power': f"{pwr_split:.1f}W"
            })
        print(pd.DataFrame(splits).to_string(index=False))

    print("=" * 65)


def sync_all(session, fit_filename, custom_title=None):
    """Sync activity into parsed_activities.csv, training_data.json, and GitHub repo."""
    dist_m = session.get('total_distance') or 0
    dist_km = round(dist_m / 1000.0, 2)
    timer_sec = session.get('total_timer_time') or 0
    dur_min = round(timer_sec / 60.0, 1)
    pace_sec = (timer_sec / (dist_m / 1000.0)) if dist_m > 0 else 0
    pm, ps = divmod(int(pace_sec), 60)
    pace_str = f"{pm}:{ps:02d}/km"
    pace_min_km = round(pace_sec / 60.0, 2)

    start_time_dt = session.get('start_time') # UTC datetime
    if isinstance(start_time_dt, datetime.datetime):
        # Convert to local CEST (UTC+2) for display
        local_time_dt = start_time_dt + datetime.timedelta(hours=2)
        date_str = local_time_dt.strftime('%Y-%m-%d')
        datetime_str = local_time_dt.strftime('%Y-%m-%d %H:%M')
        ts = int(start_time_dt.timestamp())
    else:
        date_str = str(start_time_dt)[:10]
        datetime_str = str(start_time_dt)[:16]
        ts = int(datetime.datetime.now().timestamp())

    act_id = os.path.splitext(fit_filename)[0]

    # 1. Update parsed_activities.csv
    if os.path.exists(CSV_PATH):
        df_csv = pd.read_csv(CSV_PATH)
        if fit_filename not in df_csv['filename'].values:
            new_csv_row = {
                'filename': fit_filename,
                'sport': 'running',
                'start_time': str(session.get('start_time')),
                'timestamp': str(session.get('timestamp')),
                'total_elapsed_time': session.get('total_elapsed_time'),
                'total_timer_time': session.get('total_timer_time'),
                'total_distance': session.get('total_distance'),
                'total_calories': session.get('total_calories'),
                'max_heart_rate': session.get('max_heart_rate'),
                'min_heart_rate': session.get('min_heart_rate'),
                'avg_heart_rate': session.get('avg_heart_rate'),
                'avg_temperature': session.get('avg_temperature'),
                'total_ascent': session.get('total_ascent'),
                'total_descent': session.get('total_descent'),
                'total_strides': session.get('total_strides'),
                'max_running_cadence': session.get('max_running_cadence'),
                'avg_running_cadence': session.get('avg_running_cadence'),
                'avg_step_length': session.get('avg_step_length'),
                'enhanced_max_speed': session.get('enhanced_max_speed'),
                'max_speed': session.get('max_speed'),
                'enhanced_avg_speed': session.get('enhanced_avg_speed'),
                'avg_speed': session.get('avg_speed'),
                'avg_power': session.get('avg_power'),
                'avg_stance_time': session.get('avg_stance_time'),
                'avg_stance_time_balance': session.get('avg_stance_time_balance', 0.0),
                'avg_vertical_oscillation': session.get('avg_vertical_oscillation'),
                'avg_vertical_ratio': session.get('avg_vertical_ratio'),
                'Effort Pace': session.get('Effort Pace'),
                'sub_sport': float('nan'),
                'max_cadence': float('nan'),
                'avg_cadence': float('nan'),
                'max_power': float('nan'),
                'total_work': float('nan'),
                'normalized_power': float('nan'),
                'pool_length': float('nan'),
                'total_moving_time': float('nan'),
                'distance_km': dist_km,
                'duration_min': dur_min,
                'pace_sec_km': pace_sec,
                'pace_min_km': pace_min_km,
                'pace_str': pace_str
            }
            df_csv = pd.concat([df_csv, pd.DataFrame([new_csv_row])], ignore_index=True)
            df_csv.to_csv(CSV_PATH, index=False)
            print(f"✅ Appended to parsed_activities.csv ({len(df_csv)} total rows)")
        else:
            print("ℹ️ Activity already in parsed_activities.csv")

    # 2. Update training_data.json
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        existing_ids = [a['id'] for a in data['activities']]
        if act_id not in existing_ids:
            new_act = {
                'id': act_id,
                'date': date_str,
                'datetime': datetime_str,
                'timestamp': ts,
                'distance_km': dist_km,
                'duration_min': dur_min,
                'pace_str': pace_str,
                'pace_min_km': pace_min_km,
                'avg_hr': session.get('avg_heart_rate') or 0,
                'max_hr': session.get('max_heart_rate') or 0,
                'cadence': (session.get('avg_running_cadence') or 0) * 2,
                'elevation_m': int(session.get('total_ascent') or 0),
                'calories': int(session.get('total_calories') or 0)
            }
            data['activities'].append(new_act)

            # Recalculate monthly
            month_key = date_str[:7]
            month_runs = [a for a in data['activities'] if a['date'].startswith(month_key)]
            m_km = round(sum(a['distance_km'] for a in month_runs), 1)
            m_dur = sum(a['duration_min'] for a in month_runs)
            m_hr = round(sum(a['avg_hr'] for a in month_runs) / len(month_runs), 1)
            m_pace = round(m_dur / m_km, 2) if m_km > 0 else 0

            month_entry = next((m for m in data['monthly'] if m['month'] == month_key), None)
            if month_entry:
                month_entry['total_km'] = m_km
                month_entry['runs'] = len(month_runs)
                month_entry['avg_hr'] = m_hr
                month_entry['avg_pace'] = m_pace
            else:
                data['monthly'].append({
                    'month': month_key,
                    'total_km': m_km,
                    'runs': len(month_runs),
                    'avg_hr': m_hr,
                    'avg_pace': m_pace
                })

            # Recalculate KPIs
            total_km = round(sum(a['distance_km'] for a in data['activities']), 1)
            today_date = datetime.date.today()
            days_left = (RACE_DATE - today_date).days

            data['kpis']['total_runs'] = len(data['activities'])
            data['kpis']['total_running_km'] = total_km
            data['kpis']['days_to_race'] = days_left
            if dist_km > data['kpis'].get('longest_run_2026', 0):
                data['kpis']['longest_run_2026'] = dist_km

            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Synced training_data.json ({len(data['activities'])} activities, {total_km} total km)")
        else:
            print("ℹ️ Activity already in training_data.json")

    # 3. Copy to GitHub repo and commit
    if os.path.exists(REPO_DIR):
        dst_html = os.path.join(REPO_DIR, 'index.html')
        dst_json = os.path.join(REPO_DIR, 'training_data.json')

        if os.path.exists(INDEX_PATH):
            shutil.copy2(INDEX_PATH, dst_html)
        if os.path.exists(JSON_PATH):
            shutil.copy2(JSON_PATH, dst_json)
        print("✅ Copied updated index.html & training_data.json to GitHub repository")

        # Git status check
        res = subprocess.run(['git', '-C', REPO_DIR, 'status', '--porcelain'], capture_output=True, text=True)
        if res.stdout.strip():
            subprocess.run(['git', '-C', REPO_DIR, 'add', 'index.html', 'training_data.json'], check=True)
            msg = custom_title or f"Sync run {date_str} ({dist_km} km @ {pace_str}) to site ({data['kpis']['total_runs']} runs)"
            subprocess.run(['git', '-C', REPO_DIR, 'commit', '-m', msg], check=True)
            print(f"🚀 Created commit: '{msg}'")
            print("👉 GitHub Desktop is ready: Click 'Push to origin'!")
        else:
            print("ℹ️ Git working tree in GitHub repo is already clean")


def main():
    parser = argparse.ArgumentParser(description="Analyze Coros FIT file and sync to Munich Marathon Sub-4 site")
    parser.add_argument("fit_path", help="Path to .fit file")
    parser.add_argument("--sync", action="store_true", help="Sync to training_data.json, parsed_activities.csv, and commit to GitHub repo")
    parser.add_argument("--commit-msg", help="Custom git commit message", default=None)

    args = parser.parse_args()

    fit_filename = os.path.basename(args.fit_path)
    session, laps, df_rec, events = parse_fit_file(args.fit_path)

    print_analysis(session, laps, df_rec, events, fit_filename)

    if args.sync:
        sync_all(session, fit_filename, args.commit_msg)


if __name__ == '__main__':
    main()
