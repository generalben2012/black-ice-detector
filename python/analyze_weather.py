import json
import csv
from pathlib import Path
from datetime import datetime, timedelta

def load_weather_data(date_str):
    weather_file = Path(f'/mnt/c/proprojet/black-ice-detector/python/weather/kma_data_{date_str}.json')
    if not weather_file.exists():
        return None
    
    with open(weather_file, 'r', encoding='utf-8') as f:
        weather_json = json.load(f)
    
    # Aggregate data by time
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
                
    # Calculate average across all grid points for each time
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

def find_closest_weather(weather_dict, target_dt):
    # Find the closest 30-min interval
    closest_dt_str = None
    min_diff = timedelta(days=999)
    
    for dt_str in weather_dict.keys():
        try:
            dt = datetime.strptime(dt_str, '%Y%m%d%H%M')
            # Remove timezone for comparison
            target_naive = target_dt.replace(tzinfo=None)
            diff = abs(target_naive - dt)
            if diff < min_diff:
                min_diff = diff
                closest_dt_str = dt_str
        except Exception as e:
            pass
            
    if closest_dt_str:
        return closest_dt_str, weather_dict[closest_dt_str]
    return None, None

def main():
    measurements_file = Path('/mnt/c/proprojet/black-ice-detector/python/measurements.jsonl')
    measurements = []
    with open(measurements_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                measurements.append(json.loads(line))
                
    # Cache weather data by date
    weather_cache = {}
    
    results = []
    
    for m in measurements:
        dt = datetime.fromisoformat(m['measured_at'])
        date_str = dt.strftime('%Y-%m-%d')
        
        if date_str not in weather_cache:
            weather_cache[date_str] = load_weather_data(date_str)
            
        weather_data = weather_cache[date_str]
        
        m_result = {
            'time': m['time'],
            'location': m['location'],
            'status': m['black_ice_status'],
            'sensor_ta': m['temperature'],
            'sensor_road': m['road_surface_temp'],
            'sensor_hm': m['humidity']
        }
        
        if weather_data:
            closest_time, kma = find_closest_weather(weather_data, dt)
            if kma:
                m_result['kma_ta'] = round(kma['ta'], 1)
                m_result['kma_hm'] = round(kma['hm'], 1)
                m_result['kma_td'] = round(kma['td'], 1)
                m_result['kma_rn'] = round(kma['rn'], 1)
                m_result['kma_time'] = closest_time[-4:-2] + ':' + closest_time[-2:]
        results.append(m_result)
        
    # Group by status
    occurred = [r for r in results if r['status'] == 'occurred']
    not_occurred = [r for r in results if r['status'] == 'not_occurred']
    
    print("--- Occurred ---")
    for r in occurred:
        print(f"Time:{r['time']} | Sensor: Ta={r['sensor_ta']:5.1f}, Road={r['sensor_road']:5.1f}, Hm={r['sensor_hm']:4.1f} | KMA({r.get('kma_time')}): Ta={r.get('kma_ta')}, Hm={r.get('kma_hm')}, Td={r.get('kma_td')}, Rain={r.get('kma_rn')}")

    print("\n--- Not Occurred (Sample of 10) ---")
    for r in not_occurred[:10]:
        print(f"Time:{r['time']} | Sensor: Ta={r['sensor_ta']:5.1f}, Road={r['sensor_road']:5.1f}, Hm={r['sensor_hm']:4.1f} | KMA({r.get('kma_time')}): Ta={r.get('kma_ta')}, Hm={r.get('kma_hm')}, Td={r.get('kma_td')}, Rain={r.get('kma_rn')}")

    # Check overall precipitation for black ice days
    print("\n--- Rainfall context ---")
    occurred_dates = set(m['date'] for m in measurements if m['black_ice_status'] == 'occurred')
    for d in occurred_dates:
        wd = load_weather_data(d)
        if wd:
            total_rain = sum(w['rn'] for w in wd.values()) / len(wd) # Actually RN_DAY is daily accum, but we average points
            max_rain = max(w['rn'] for w in wd.values())
            print(f"Date: {d}, Max RN_DAY across intervals: {max_rain:.1f}")

if __name__ == '__main__':
    main()
