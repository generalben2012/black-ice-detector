import json

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# 블랙아이스 발생 시각화\n",
    "초음파 거리, 노면 온도, 대기 온도, 조도(LDR), 습도 센서 데이터와 블랙아이스 발생 여부 간의 상관관계를 시각화합니다."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "import warnings\n",
    "warnings.filterwarnings('ignore')\n",
    "\n",
    "# 폰트 설정 초기화 (이전 커널 메모리에 남은 NanumGothic 설정 제거)\n",
    "plt.rcdefaults()\n",
    "\n",
    "# 데이터 로드\n",
    "df = pd.read_csv('measurements.csv')\n",
    "# 상태가 'unknown'인 데이터는 시각화의 명확성을 위해 제외\n",
    "df = df[df['black_ice_status'].isin(['occurred', 'not_occurred'])]\n",
    "df.head()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 분석할 센서 특성들\n",
    "features = ['temperature', 'road_surface_temp', 'distance_cm_avg', 'ldr_avg', 'humidity']\n",
    "titles = ['Temperature (C)', 'Road Surface Temp (C)', 'Distance (cm)', 'Illumination (LDR)', 'Humidity (%)']\n",
    "\n",
    "fig, axes = plt.subplots(2, 3, figsize=(15, 10))\n",
    "axes = axes.flatten()\n",
    "\n",
    "# 각 변수별로 블랙아이스 발생 여부에 따른 박스플롯(Boxplot) 그리기\n",
    "for i, (col, title) in enumerate(zip(features, titles)):\n",
    "    sns.boxplot(x='black_ice_status', y=col, data=df, ax=axes[i], order=['not_occurred', 'occurred'], palette='Set2')\n",
    "    sns.stripplot(x='black_ice_status', y=col, data=df, ax=axes[i], order=['not_occurred', 'occurred'], color='black', alpha=0.5)\n",
    "    axes[i].set_title(title)\n",
    "    axes[i].set_xlabel('Black Ice Status')\n",
    "    axes[i].set_ylabel('')\n",
    "\n",
    "# 6번째 빈 그래프 숨기기\n",
    "axes[5].axis('off')\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "위의 박스플롯을 보면 발생 여부를 판가름 짓는 강력한 요인은 **온도와 노면 온도** 임을 알 수 있습니다. \n",
    "이 두 가지 핵심 변수를 산점도(Scatter Plot)로 그려서 더 명확히 확인해봅니다."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 산점도를 통한 2차원 관계 시각화 (대기 온도 vs 노면 온도)\n",
    "plt.figure(figsize=(10, 7))\n",
    "\n",
    "sns.scatterplot(x='temperature', y='road_surface_temp', hue='black_ice_status', \n",
    "                style='black_ice_status', s=150, data=df, palette={'not_occurred': 'gray', 'occurred': 'red'})\n",
    "\n",
    "plt.title('Distribution of Black Ice Occurrence (Air Temp vs Road Temp)', fontsize=14)\n",
    "plt.xlabel('Air Temperature (C)', fontsize=12)\n",
    "plt.ylabel('Road Surface Temperature (C)', fontsize=12)\n",
    "\n",
    "# 0도 기준선 그리기\n",
    "plt.axvline(x=0, color='blue', linestyle='--', alpha=0.3, label='0C Air Line') \n",
    "plt.axhline(y=0, color='blue', linestyle='--', alpha=0.3, label='0C Road Line') \n",
    "\n",
    "plt.grid(True, alpha=0.3)\n",
    "plt.legend(title='Status', bbox_to_anchor=(1.05, 1), loc='upper left')\n",
    "plt.tight_layout()\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### 시간에 따른 온도 변화 및 블랙아이스 발생 시점 (Line Chart)\n",
    "측정 시간에 따른 대기 온도와 노면 온도의 추이를 확인하고, 블랙아이스가 발생한 특정 시점을 파악합니다."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "# 시간을 datetime 객체로 변환하고 시간순으로 정렬\n",
    "df['measured_at'] = pd.to_datetime(df['measured_at'])\n",
    "df_time = df.sort_values('measured_at')\n",
    "\n",
    "plt.figure(figsize=(15, 6))\n",
    "\n",
    "# 대기 온도와 노면 온도 변화 추이\n",
    "plt.plot(df_time['measured_at'], df_time['temperature'], label='Air Temp', marker='o', alpha=0.6)\n",
    "plt.plot(df_time['measured_at'], df_time['road_surface_temp'], label='Road Temp', marker='s', alpha=0.6)\n",
    "\n",
    "# 블랙아이스가 발생한 시점만 빨간색 큰 점으로 표시\n",
    "occurred_df = df_time[df_time['black_ice_status'] == 'occurred']\n",
    "plt.scatter(occurred_df['measured_at'], occurred_df['road_surface_temp'], \n",
    "            color='red', s=150, zorder=5, label='Black Ice Occurred')\n",
    "\n",
    "plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5, label='0C Line')\n",
    "plt.title('Temperature Changes Over Time', fontsize=14)\n",
    "plt.xlabel('Time', fontsize=12)\n",
    "plt.ylabel('Temperature (C)', fontsize=12)\n",
    "plt.legend()\n",
    "plt.grid(alpha=0.3)\n",
    "plt.tight_layout()\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### 블랙아이스 발생 여부에 따른 평균 센서값 비교 (Bar Chart)\n",
    "블랙아이스가 발생했을 때와 발생하지 않았을 때의 평균 대기 온도, 노면 온도, 습도를 비교합니다."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "fig, axes = plt.subplots(1, 3, figsize=(15, 5))\n",
    "\n",
    "sns.barplot(x='black_ice_status', y='temperature', data=df, ax=axes[0], palette='pastel')\n",
    "axes[0].set_title('Average Air Temperature (C)')\n",
    "\n",
    "sns.barplot(x='black_ice_status', y='road_surface_temp', data=df, ax=axes[1], palette='pastel')\n",
    "axes[1].set_title('Average Road Temperature (C)')\n",
    "\n",
    "sns.barplot(x='black_ice_status', y='humidity', data=df, ax=axes[2], palette='pastel')\n",
    "axes[2].set_title('Average Humidity (%)')\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### 통계 요약 표 (Summary Table)\n",
    "발생 여부에 따른 각 센서별 정확한 평균 수치를 표로 확인합니다."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "summary_table = df.groupby('black_ice_status')[['temperature', 'road_surface_temp', 'humidity', 'ldr_avg']].mean()\n",
    "summary_table.columns = ['Avg Air Temp (C)', 'Avg Road Temp (C)', 'Avg Humidity (%)', 'Avg LDR']\n",
    "summary_table = summary_table.round(2)\n",
    "display(summary_table)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### 지도 위에 블랙아이스 발생 위치 및 날씨/측정 데이터 통합 표시\n",
    "각 관측소 위치별로 블랙아이스 발생 기록을 지도(Map)에 표시합니다. 빨간색 마커는 블랙아이스 발생, 회색 마커는 미발생을 나타냅니다. 마커를 클릭하면 **센서 측정 데이터**와 가장 근접한 시간대의 **기상청(KMA) 날씨 데이터**를 함께 비교해 볼 수 있습니다."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import folium\n",
    "from datetime import datetime\n",
    "from analyze_weather import load_weather_data, find_closest_weather\n",
    "\n",
    "# 가상의 성북구 관측소 위치 좌표 (위도, 경도) - 시각화를 위해 임의 지정\n",
    "location_coords = {\n",
    "    1: [37.604, 127.032],\n",
    "    2: [37.605, 127.045],\n",
    "    3: [37.592, 127.016],\n",
    "    4: [37.590, 127.025],\n",
    "    5: [37.610, 127.010]\n",
    "}\n",
    "\n",
    "# 성북구 중심 지도 생성\n",
    "m = folium.Map(location=[37.598, 127.026], zoom_start=14)\n",
    "\n",
    "weather_cache = {}\n",
    "\n",
    "# 데이터프레임의 모든 기록을 지도에 마커로 표시\n",
    "for idx, row in df.iterrows():\n",
    "    dt = row['measured_at'].to_pydatetime()\n",
    "    date_str = dt.strftime('%Y-%m-%d')\n",
    "    \n",
    "    # 날씨 데이터 로드 (캐싱)\n",
    "    if date_str not in weather_cache:\n",
    "        weather_cache[date_str] = load_weather_data(date_str)\n",
    "        \n",
    "    weather_data = weather_cache[date_str]\n",
    "    \n",
    "    kma_info = \"<span style='color:gray'>기상청 데이터 없음</span>\"\n",
    "    if weather_data:\n",
    "        closest_time, kma = find_closest_weather(weather_data, dt)\n",
    "        if kma:\n",
    "            kma_info = f\"<b>기상청({closest_time[-4:-2]}:{closest_time[-2:]}):</b> 온도 {kma['ta']:.1f}C, 비/눈 {kma['rn']:.1f}mm, 습도 {kma['hm']:.1f}%\"\n",
    "            \n",
    "    loc_id = row['location']\n",
    "    coords = location_coords.get(loc_id, [37.598, 127.026])\n",
    "    \n",
    "    # 마커가 겹치지 않도록 미세하게 좌표 이동\n",
    "    offset_lat = coords[0] + (idx % 10) * 0.0003\n",
    "    offset_lon = coords[1] + (idx % 10) * 0.0003\n",
    "    \n",
    "    status = row['black_ice_status']\n",
    "    color = 'red' if status == 'occurred' else 'gray'\n",
    "    icon_type = 'info-sign' if status == 'occurred' else 'ok-circle'\n",
    "    \n",
    "    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')\n",
    "    popup_html = f\"\"\"\n",
    "    <div style='width:250px;'>\n",
    "        <b>Location: {loc_id}</b><br>\n",
    "        <b>시간:</b> {time_str}<br>\n",
    "        <b>상태:</b> <span style='color:{color}; font-weight:bold;'>{status.upper()}</span><hr style='margin:5px 0;'>\n",
    "        <b>센서 대기온도:</b> {row['temperature']}C<br>\n",
    "        <b>센서 노면온도:</b> {row['road_surface_temp']}C<br>\n",
    "        <b>센서 습도:</b> {row['humidity']}%<hr style='margin:5px 0;'>\n",
    "        {kma_info}\n",
    "    </div>\n",
    "    \"\"\"\n",
    "    \n",
    "    folium.Marker(\n",
    "        location=[offset_lat, offset_lon],\n",
    "        popup=folium.Popup(popup_html, max_width=300),\n",
    "        icon=folium.Icon(color=color, icon=icon_type)\n",
    "    ).add_to(m)\n",
    "\n",
    "m"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.8.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}

with open('/mnt/c/proprojet/black-ice-detector/python/visualization.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=2)

print("Notebook generated successfully.")
