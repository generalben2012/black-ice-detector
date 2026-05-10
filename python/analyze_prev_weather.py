import json
from pathlib import Path
from datetime import datetime, timedelta

def load_weather_data(date_str):
    weather_file = Path(f'/mnt/c/proprojet/black-ice-detector/python/weather/kma_data_{date_str}.json')
    if not weather_file.exists():
        return None
    
    with open(weather_file, 'r', encoding='utf-8') as f:
        weather_json = json.load(f)
    
    time_data = {}
    for point_data in weather_json['collected_data']:
        data_str = point_data['data']
        lines = data_str.split('\n')
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 6:
                dt_str = parts[0]
                ta = float(parts[1])
                hm = float(parts[2])
                td = float(parts[3])
                ws = float(parts[4])
                rn = float(parts[5])
                
                if dt_str not in time_data:
                    time_data[dt_str] = []
                time_data[dt_str].append({'ta': ta, 'hm': hm, 'td': td, 'ws': ws, 'rn': rn})
                
    avg_time_data = {}
    for dt_str, records in time_data.items():
        avg_time_data[dt_str] = {
            'ta': sum(r['ta'] for r in records) / len(records),
            'hm': sum(r['hm'] for r in records) / len(records),
            'td': sum(r['td'] for r in records) / len(records),
            'ws': sum(r['ws'] for r in records) / len(records),
            'rn': sum(r['rn'] for r in records) / len(records)
        }
    return avg_time_data

def get_max_rn_day(weather_dict):
    if not weather_dict:
        return 0.0
    return max(w['rn'] for w in weather_dict.values())

def get_temp_range(weather_dict):
    if not weather_dict:
        return 0.0, 0.0
    min_ta = min(w['ta'] for w in weather_dict.values())
    max_ta = max(w['ta'] for w in weather_dict.values())
    return min_ta, max_ta

def main():
    target_dates = ['2026-02-10', '2026-02-12']
    
    for date_str in target_dates:
        print(f"=== Analysis for Black Ice Day: {date_str} ===")
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        prev_dt = dt - timedelta(days=1)
        prev_date_str = prev_dt.strftime('%Y-%m-%d')
        
        wd_day = load_weather_data(date_str)
        wd_prev = load_weather_data(prev_date_str)
        
        rn_prev = get_max_rn_day(wd_prev)
        rn_day = get_max_rn_day(wd_day)
        
        min_ta_prev, max_ta_prev = get_temp_range(wd_prev)
        min_ta_day, max_ta_day = get_temp_range(wd_day)
        
        print(f"[Previous Day ({prev_date_str})]")
        print(f"  Max Rain: {rn_prev:.2f} mm")
        print(f"  Temp Range: {min_ta_prev:.1f} to {max_ta_prev:.1f}")
        
        print(f"[Occurrence Day ({date_str})]")
        print(f"  Max Rain: {rn_day:.2f} mm")
        print(f"  Temp Range: {min_ta_day:.1f} to {max_ta_day:.1f}")
        print()

if __name__ == '__main__':
    main()
