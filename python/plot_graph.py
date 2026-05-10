import pandas as pd
import matplotlib.pyplot as plt
import os

df = pd.read_csv('measurements.csv')
df = df[df['black_ice_status'].isin(['occurred', 'not_occurred'])]
df['measured_at'] = pd.to_datetime(df['measured_at'])
df_time = df.sort_values('measured_at')

plt.figure(figsize=(15, 6))
plt.plot(df_time['measured_at'], df_time['temperature'], label='Air Temp', marker='o', alpha=0.6)
plt.plot(df_time['measured_at'], df_time['road_surface_temp'], label='Road Temp', marker='s', alpha=0.6)

occurred_df = df_time[df_time['black_ice_status'] == 'occurred']
plt.scatter(occurred_df['measured_at'], occurred_df['road_surface_temp'], color='red', s=150, zorder=5, label='Black Ice Occurred')

plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5, label='0C Line')
plt.title('Temperature Changes Over Time', fontsize=14)
plt.xlabel('Time', fontsize=12)
plt.ylabel('Temperature (C)', fontsize=12)
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

out_path = '/home/mystous/.gemini/antigravity/brain/0f6ddcce-d807-4181-9fd0-a202eb11efae/line_chart.png'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
plt.savefig(out_path)
print("Saved to", out_path)
