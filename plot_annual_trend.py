#!/usr/bin/env python3.14
"""
연도별 논문 수 추이 시각화
데이터: savedrecs.txt / savedrecs-2.txt / savedrecs-3.txt (WoS, 총 1,500편)
"""

import os, re, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import FancyArrowPatch
import seaborn as sns

warnings.filterwarnings('ignore')

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── 1. WoS 파싱 (공통 유틸) ─────────────────────────────────────────────────
def parse_wos_file(filepath):
    records, current, current_tag = [], {}, None
    with open(filepath, encoding='utf-8-sig') as f:
        for line in f:
            line = line.rstrip('\n')
            if len(line) < 2:
                continue
            tag   = line[:2].strip()
            value = line[3:].strip() if len(line) > 3 else ''
            if tag == 'ER':
                if current:
                    records.append(current)
                current, current_tag = {}, None
            elif tag == 'EF':
                break
            elif tag and tag != '  ':
                current_tag = tag
                current.setdefault(tag, [])
                if value:
                    current[tag].append(value)
            else:
                if current_tag and value:
                    current[current_tag].append(value)
    return records

def load_df():
    base  = BASE_DIR
    files = ["savedrecs.txt", "savedrecs-2.txt", "savedrecs-3.txt"]
    recs  = []
    for fn in files:
        recs.extend(parse_wos_file(os.path.join(base, fn)))

    rows = []
    for r in recs:
        py_val = r.get('PY', [None])[0]
        dt_val = (r.get('DT') or r.get('PT') or ['Unknown'])[0]
        try:
            py_val = int(py_val)
        except Exception:
            py_val = None
        rows.append({'PY': py_val, 'DT': dt_val})

    df = pd.DataFrame(rows)
    df['PY'] = pd.to_numeric(df['PY'], errors='coerce')
    return df

# ─── 2. 집계 ─────────────────────────────────────────────────────────────────
def prepare(df):
    df = df.dropna(subset=['PY']).copy()
    df = df[(df['PY'] >= 1993) & (df['PY'] <= 2025)]   # 데이터가 충분한 구간
    df['PY'] = df['PY'].astype(int)

    # 문헌 유형 단순화
    def simplify(dt):
        dt = str(dt).lower()
        if 'review' in dt:
            return 'Review'
        if 'proceeding' in dt or 'conference' in dt:
            return 'Conference Paper'
        if 'article' in dt:
            return 'Article'
        return 'Other'

    df['DT_simple'] = df['DT'].apply(simplify)

    total = df.groupby('PY').size().reset_index(name='count')
    stacked = (df.groupby(['PY', 'DT_simple'])
                 .size()
                 .reset_index(name='count')
                 .pivot(index='PY', columns='DT_simple', values='count')
                 .fillna(0)
                 .astype(int))
    # 5년 이동평균
    total['ma5'] = total['count'].rolling(5, min_periods=1, center=True).mean()

    return total, stacked, df

# ─── 3. 그래프 ───────────────────────────────────────────────────────────────
def plot_annual_trend(total, stacked, df):
    years = total['PY'].values

    # ── 색상·스타일 ──
    sns.set_theme(style='whitegrid', context='talk')
    BAR_COLOR  = '#4A90D9'
    MA_COLOR   = '#E05C2A'
    AREA_COLOR = '#4A90D9'

    fig = plt.figure(figsize=(16, 10))
    gs  = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.35)
    ax1 = fig.add_subplot(gs[0, :])   # 상단 전체: 연도별 총 논문 수
    ax2 = fig.add_subplot(gs[1, 0])   # 하단 좌: 문헌 유형 누적 막대
    ax3 = fig.add_subplot(gs[1, 1])   # 하단 우: 10년 단위 박스플롯 대신 히트맵

    fig.suptitle(
        'Annual Publication Trend — Video Analysis / Retrieval / Summarization\n'
        'Web of Science  |  N = 1,500 papers  |  1993–2025',
        fontsize=15, fontweight='bold', y=0.98
    )

    # ══ [ax1] 막대 + 5년 이동평균선 ═══════════════════════════════════════════
    bars = ax1.bar(
        years, total['count'],
        color=BAR_COLOR, alpha=0.70, width=0.75,
        zorder=2, label='Annual publications'
    )
    ax1.plot(
        years, total['ma5'],
        color=MA_COLOR, linewidth=2.8, marker='o', markersize=4,
        zorder=3, label='5-year moving average'
    )
    ax1.fill_between(years, total['ma5'], alpha=0.12, color=MA_COLOR, zorder=1)

    # 값 레이블 (막대 위 숫자) — 2019 이후만 표시해 과밀 방지
    for bar, yr, cnt in zip(bars, years, total['count']):
        if yr >= 2019:
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1.2,
                str(cnt), ha='center', va='bottom',
                fontsize=8.5, color='#333333', fontweight='bold'
            )

    # 주요 이벤트 주석
    events = {
        2002: ('Shot boundary\ndetection era', 0.62),
        2012: ('AlexNet /\nDeep Learning', 0.72),
        2017: ('Attention /\nTransformer', 0.58),
        2022: ('LLM + Video\nfusion', 0.48),
    }
    for yr, (label, yrel) in events.items():
        cnt_at = total.loc[total['PY'] == yr, 'count']
        if cnt_at.empty:
            continue
        y_bar = int(cnt_at.values[0])
        y_ann = total['count'].max() * yrel
        ax1.annotate(
            label,
            xy=(yr, y_bar), xytext=(yr, y_ann),
            arrowprops=dict(arrowstyle='->', color='#555', lw=1.4),
            ha='center', fontsize=8.2, color='#333',
            bbox=dict(boxstyle='round,pad=0.3', fc='#fffbe6', ec='#ccc', alpha=0.9),
        )

    ax1.set_xlabel('Publication Year', fontsize=11)
    ax1.set_ylabel('Number of Publications', fontsize=11)
    ax1.set_xlim(years.min() - 0.8, years.max() + 0.8)
    ax1.set_ylim(0, total['count'].max() * 1.18)
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax1.tick_params(axis='x', rotation=45, labelsize=9)
    ax1.tick_params(axis='y', labelsize=9)
    ax1.legend(fontsize=10, loc='upper left', framealpha=0.85)
    ax1.grid(axis='y', alpha=0.4, zorder=0)
    ax1.set_axisbelow(True)

    # ══ [ax2] 문헌 유형 누적 스택 막대 ════════════════════════════════════════
    dt_colors = {
        'Article':          '#4A90D9',
        'Conference Paper': '#E8A838',
        'Review':           '#5DBB6A',
        'Other':            '#BDBDBD',
    }
    bottom = np.zeros(len(stacked))
    for dt in ['Article', 'Conference Paper', 'Review', 'Other']:
        if dt not in stacked.columns:
            continue
        vals = stacked[dt].values
        ax2.bar(
            stacked.index, vals,
            bottom=bottom, label=dt,
            color=dt_colors[dt], alpha=0.82, width=0.75
        )
        bottom += vals

    ax2.set_title('By Document Type (stacked)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Year', fontsize=10)
    ax2.set_ylabel('Publications', fontsize=10)
    ax2.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax2.tick_params(axis='x', rotation=45, labelsize=8)
    ax2.tick_params(axis='y', labelsize=8)
    ax2.legend(fontsize=8.5, loc='upper left', framealpha=0.85)
    ax2.grid(axis='y', alpha=0.35)
    ax2.set_axisbelow(True)

    # ══ [ax3] 5년 구간별 논문 수 히트맵 (1995–2025) ════════════════════════
    df_heat = df[(df['PY'] >= 1995) & (df['PY'] <= 2025)].copy()
    bins    = list(range(1995, 2026, 5))
    labels  = [f"{b}–{b+4}" for b in bins[:-1]]
    df_heat['period'] = pd.cut(df_heat['PY'], bins=bins, right=False, labels=labels)

    def simplify2(dt):
        dt = str(dt).lower()
        if 'review'      in dt: return 'Review'
        if 'proceeding'  in dt or 'conference' in dt: return 'Conference'
        if 'article'     in dt: return 'Article'
        return 'Other'

    df_heat['DT2'] = df_heat['DT'].apply(simplify2)
    pivot = (df_heat.groupby(['period', 'DT2'], observed=True)
                    .size()
                    .unstack(fill_value=0))
    # 열 순서 고정
    for col in ['Article', 'Conference', 'Review', 'Other']:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot = pivot[['Article', 'Conference', 'Review', 'Other']]

    sns.heatmap(
        pivot.T, ax=ax3,
        annot=True, fmt='d', cmap='YlOrRd',
        linewidths=0.5, linecolor='#eee',
        cbar_kws={'label': 'Papers', 'shrink': 0.85},
        annot_kws={'size': 8.5}
    )
    ax3.set_title('Publication Count Heatmap (5-yr × Type)', fontsize=11, fontweight='bold')
    ax3.set_xlabel('Period', fontsize=10)
    ax3.set_ylabel('')
    ax3.tick_params(axis='x', rotation=35, labelsize=8)
    ax3.tick_params(axis='y', rotation=0,  labelsize=9)

    plt.savefig(f"{OUTPUT_DIR}/annual_trend_detail.png", dpi=180, bbox_inches='tight')
    plt.close()
    print(f"Saved → {OUTPUT_DIR}/annual_trend_detail.png")

# ─── 4. 실행 ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Loading data...")
    df = load_df()
    print(f"  {len(df)} records  |  {int(df['PY'].min())}–{int(df['PY'].max())}")

    total, stacked, df_clean = prepare(df)
    print(f"  Plotting 1993–2025 ({len(total)} years)...")
    plot_annual_trend(total, stacked, df_clean)
    print("Done.")
