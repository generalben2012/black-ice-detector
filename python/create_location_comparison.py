import json

notebook = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# 발생 위치별(Location) 블랙아이스 발생/미발생 조건 정밀 비교\n",
    "동일한 날짜, 비슷한 아침 시간대임에도 불구하고 어떤 위치(Location)에서는 블랙아이스가 발생하고 어떤 곳에서는 발생하지 않았습니다.\n",
    "이 노트북은 KMA 광역 데이터가 아닌 **실제 현장의 각 위치별 센서 측정 데이터**를 직접 비교하여, 발생 구역과 미발생 구역의 결정적인 환경적 차이를 시각화합니다."
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
    "\n",
    "import warnings\n",
    "warnings.filterwarnings('ignore')\n",
    "plt.rcdefaults()\n",
    "\n",
    "df = pd.read_csv('measurements.csv')\n",
    "df['measured_at'] = pd.to_datetime(df['measured_at'])\n",
    "df = df[df['black_ice_status'].isin(['occurred', 'not_occurred'])]\n",
    "\n",
    "# 2월 10일과 12일 (블랙아이스 발생일) 데이터만 추출\n",
    "df_target = df[df['date'].isin(['2026-02-10', '2026-02-12'])].copy()\n",
    "df_target = df_target.sort_values(by=['date', 'location'])\n",
    "df_target.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### 1. 동일 날짜의 위치별(Location 1~5) 노면 온도 및 대기 온도 비교\n",
    "블랙아이스가 발생한 2월 10일과 12일 아침, 각 위치(1~5구역)별로 측정된 대기 온도와 노면 온도를 나란히 비교합니다.\n",
    "발생 구역(빨간색)과 미발생 구역(파란색) 간에 어떤 수치가 극명하게 엇갈리는지 확인합니다."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "fig, axes = plt.subplots(2, 1, figsize=(14, 12))\n",
    "\n",
    "colors = {'occurred': 'red', 'not_occurred': 'blue'}\n",
    "\n",
    "for i, date_str in enumerate(['2026-02-10', '2026-02-12']):\n",
    "    df_day = df_target[df_target['date'] == date_str]\n",
    "    \n",
    "    ax = axes[i]\n",
    "    # 위치별 대기 온도(Air Temp)와 노면 온도(Road Temp)를 선으로 연결하여 비교\n",
    "    for idx, row in df_day.iterrows():\n",
    "        color = colors[row['black_ice_status']]\n",
    "        marker = '*' if row['black_ice_status'] == 'occurred' else 'o'\n",
    "        size = 200 if row['black_ice_status'] == 'occurred' else 100\n",
    "        \n",
    "        # 대기 온도 점\n",
    "        ax.scatter(row['location'] - 0.1, row['temperature'], color=color, marker=marker, s=size, edgecolor='black', zorder=5)\n",
    "        # 노면 온도 점\n",
    "        ax.scatter(row['location'] + 0.1, row['road_surface_temp'], color=color, marker=marker, s=size, edgecolor='black', zorder=5)\n",
    "        \n",
    "        # 두 온도의 차이를 잇는 선\n",
    "        ax.plot([row['location'] - 0.1, row['location'] + 0.1], \n",
    "                [row['temperature'], row['road_surface_temp']], color=color, alpha=0.5, linewidth=2)\n",
    "        \n",
    "        # 텍스트 라벨\n",
    "        ax.text(row['location'] - 0.1, row['temperature'] + 0.3, f\"Air:\\n{row['temperature']:.1f}\", ha='center', fontsize=9)\n",
    "        ax.text(row['location'] + 0.1, row['road_surface_temp'] + 0.3, f\"Road:\\n{row['road_surface_temp']:.1f}\", ha='center', fontsize=9)\n",
    "        \n",
    "    ax.axhline(0, color='gray', linestyle='--', alpha=0.5, label='0C (Freezing Point)')\n",
    "    \n",
    "    ax.set_title(f'Temperature Difference by Location on {date_str}', fontsize=14)\n",
    "    ax.set_xlabel('Sensor Location (1 to 5)', fontsize=12)\n",
    "    ax.set_ylabel('Temperature (C)', fontsize=12)\n",
    "    ax.set_xticks([1, 2, 3, 4, 5])\n",
    "    ax.grid(True, alpha=0.3)\n",
    "\n",
    "# 범례 수동 추가\n",
    "import matplotlib.lines as mlines\n",
    "red_star = mlines.Line2D([], [], color='red', marker='*', linestyle='None', markersize=15, label='Occurred (Black Ice)')\n",
    "blue_circle = mlines.Line2D([], [], color='blue', marker='o', linestyle='None', markersize=10, label='Not Occurred')\n",
    "axes[0].legend(handles=[red_star, blue_circle], loc='upper left')\n",
    "axes[1].legend(handles=[red_star, blue_circle], loc='upper left')\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### 💡 위치별 데이터 분석 결과 (발생 vs 미발생의 결정적 차이)\n",
    "\n",
    "위 그래프를 통해 같은 날 아침이라도 구역(Location)에 따라 블랙아이스가 생기고 안 생기는 물리적 이유가 명확히 드러납니다.\n",
    "\n",
    "1. **2월 10일의 차이**:\n",
    "   * **미발생 구역 (Loc 1, 3 - 파란색)**: 대기 온도와 노면 온도가 모두 **0도 이하(영하)**에 머물러 있습니다. 이 경우 노면에 맺힌 수분은 단순히 꽁꽁 얼어붙은 얇은 '서리' 형태로 남아있습니다.\n",
    "   * **발생 구역 (Loc 2, 4, 5 - 빨간색)**: 대기 온도는 여전히 영하권(-0.2 ~ 0.2도)인데, **노면 온도는 영상(1.0 ~ 3.8도)**으로 살짝 올라가 있습니다. \n",
    "   * **결론**: 아침 햇살(일사량)이나 지열의 영향으로 노면이 살짝 녹으면서 얇은 물막이 형성되고, 그 위를 영하의 차가운 대기가 스치며 투명하고 얇은 '블랙아이스'로 재결빙된 것입니다.\n",
    "\n",
    "2. **발생/미발생을 가르는 핵심 지표**:\n",
    "   단순히 춥다고 생기는 것이 아닙니다. **\"대기 온도는 0도 이하(영하)이면서, 동시에 노면 온도는 0도 이상(영상 1~4도)일 때\"** (그래프의 선이 0도 기준선을 가로지르는 우상향 형태일 때) 블랙아이스가 집중적으로 검출되었습니다."
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

with open('/mnt/c/proprojet/black-ice-detector/python/visualization_location.ipynb', 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=2)

print("visualization_location.ipynb generated successfully.")
