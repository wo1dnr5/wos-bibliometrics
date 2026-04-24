#!/usr/bin/env python3
"""
Web of Science 서지분석 (Bibliometrics Analysis)
분야: 비디오 분석/검색/요약 (Video Analysis, Retrieval, Summarization)
데이터: savedrecs.txt, savedrecs-2.txt, savedrecs-3.txt (각 500건, 총 1,500편)
"""

import os
import re
import json
import warnings
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
import networkx as nx

warnings.filterwarnings('ignore')

# ── 출력 경로 ──────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 폰트 설정 (한글 미사용 → 영문 출력) ───────────────────────────────────────
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.unicode_minus': False,
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
})

PALETTE = sns.color_palette("husl", 12)
sns.set_style("whitegrid")

# ══════════════════════════════════════════════════════════════════════════════
# 1. WoS 파일 파싱
# ══════════════════════════════════════════════════════════════════════════════
def parse_wos_file(filepath: str) -> list[dict]:
    """WoS tagged-format 파일을 레코드 딕셔너리 목록으로 변환."""
    records = []
    current: dict[str, list[str]] = {}
    current_tag = None

    with open(filepath, encoding='utf-8-sig') as f:
        for line in f:
            line = line.rstrip('\n')
            if len(line) < 2:
                continue
            tag = line[:2].strip()
            value = line[3:].strip() if len(line) > 3 else ''

            if tag == 'ER':           # end of record
                if current:
                    records.append(current)
                current = {}
                current_tag = None
            elif tag == 'EF':         # end of file
                break
            elif tag and tag != '  ':
                current_tag = tag
                if tag not in current:
                    current[tag] = []
                if value:
                    current[tag].append(value)
            else:                     # continuation line
                if current_tag and value:
                    current[current_tag].append(value)

    return records

def load_all_records() -> list[dict]:
    base = BASE_DIR
    files = ["savedrecs.txt", "savedrecs-2.txt", "savedrecs-3.txt"]
    all_records = []
    for fn in files:
        recs = parse_wos_file(os.path.join(base, fn))
        all_records.extend(recs)
        print(f"  {fn}: {len(recs)} records")
    print(f"  Total: {len(all_records)} records\n")
    return all_records

# ══════════════════════════════════════════════════════════════════════════════
# 2. 데이터프레임 구성 (핵심 필드 추출)
# ══════════════════════════════════════════════════════════════════════════════
def build_dataframe(records: list[dict]) -> pd.DataFrame:
    rows = []
    for r in records:
        def get(tag, join='; '):
            vals = r.get(tag, [])
            return join.join(vals) if vals else None

        def get_int(tag):
            v = get(tag)
            try:
                return int(v) if v else None
            except Exception:
                return None

        # 저자 (AF 우선, 없으면 AU)
        authors_raw = r.get('AF') or r.get('AU') or []
        # 국가 추출: C1 필드에서 마지막 쉼표 뒤 토큰
        c1_lines = r.get('C1', [])
        countries = []
        for line in c1_lines:
            m = re.search(r',\s*([A-Za-z\s]+)\.?\s*$', line)
            if m:
                c = m.group(1).strip().rstrip('.')
                # 영미권 주/도시 제거
                if c and len(c) > 2 and c not in ('USA',):
                    countries.append(c)
                elif c == 'USA':
                    countries.append('USA')

        # 인용 수
        tc = get_int('TC') or 0
        # 기관 (C3 필드)
        institutions = r.get('C3', [])
        # WC (Web of Science Categories)
        wc = r.get('WC', [])

        rows.append({
            'UT': get('UT'),
            'PT': get('PT'),               # 문헌유형 코드
            'DT': get('DT'),               # Document Type
            'TI': get('TI', ' '),          # Title
            'SO': get('SO', ' '),          # Source (journal/conference)
            'J9': get('J9'),               # Journal abbreviation
            'PY': get_int('PY'),           # Publication Year
            'TC': tc,                      # Times Cited
            'NR': get_int('NR') or 0,      # Reference count
            'AU_count': len(authors_raw),
            'authors': authors_raw,
            'DE': get('DE', ' '),          # Author keywords
            'ID': get('ID', ' '),          # Keywords Plus
            'AB': get('AB', ' '),          # Abstract
            'LA': get('LA'),               # Language
            'WC': '; '.join(wc),           # WoS Categories
            'SC': get('SC', '; '),         # Subject Categories
            'C1': '; '.join(c1_lines),
            'countries': countries,
            'institutions': institutions,
            'PU': get('PU'),               # Publisher
            'U1': get_int('U1') or 0,      # Usage count (180 days)
            'U2': get_int('U2') or 0,      # Usage count (all time)
        })

    df = pd.DataFrame(rows)
    df['PY'] = pd.to_numeric(df['PY'], errors='coerce')
    df['TC']  = pd.to_numeric(df['TC'],  errors='coerce').fillna(0).astype(int)
    return df

# ══════════════════════════════════════════════════════════════════════════════
# 3. 분석 함수들
# ══════════════════════════════════════════════════════════════════════════════

def fig_annual_publication(df: pd.DataFrame):
    """연도별 출판 건수 + 누적 인용 추세."""
    year_df = df.dropna(subset=['PY'])
    year_df = year_df[year_df['PY'] >= 1990]
    pub_cnt  = year_df.groupby('PY').size().reset_index(name='count')
    cite_sum = year_df.groupby('PY')['TC'].sum().reset_index(name='total_tc')
    merged   = pub_cnt.merge(cite_sum, on='PY')

    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax2 = ax1.twinx()

    bars = ax1.bar(merged['PY'], merged['count'], color=PALETTE[0], alpha=0.75,
                   label='Publications')
    ax2.plot(merged['PY'], merged['total_tc'], color=PALETTE[2], marker='o',
             linewidth=2, label='Total Citations')

    ax1.set_xlabel('Publication Year', fontsize=12)
    ax1.set_ylabel('Number of Publications', color=PALETTE[0], fontsize=12)
    ax2.set_ylabel('Total Citations per Year', color=PALETTE[2], fontsize=12)
    ax1.tick_params(axis='x', rotation=45)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    plt.title('Annual Publications & Citation Trend (1990–2024)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/01_annual_trend.png")
    plt.close()
    print("  [01] Annual trend saved.")
    return merged

def fig_document_types(df: pd.DataFrame):
    """문헌 유형 분포 파이차트."""
    dt_cnt = df['DT'].value_counts().head(8)
    fig, ax = plt.subplots(figsize=(9, 6))
    wedges, texts, autotexts = ax.pie(
        dt_cnt.values, labels=dt_cnt.index,
        autopct='%1.1f%%', colors=sns.color_palette('Set2', len(dt_cnt)),
        startangle=140, pctdistance=0.82,
        wedgeprops=dict(edgecolor='white', linewidth=1.5)
    )
    for t in autotexts:
        t.set_fontsize(10)
    ax.set_title('Document Type Distribution (N=1,500)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/02_document_types.png")
    plt.close()
    print("  [02] Document types saved.")

def fig_top_journals(df: pd.DataFrame):
    """상위 20개 게재지."""
    j_cnt = df['SO'].value_counts().head(20)
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(j_cnt.index[::-1], j_cnt.values[::-1],
                   color=sns.color_palette('Blues_r', len(j_cnt)))
    ax.set_xlabel('Number of Publications', fontsize=12)
    ax.set_title('Top 20 Journals / Conferences', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, j_cnt.values[::-1]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontsize=9)
    # 긴 레이블 자르기
    labels = [l[:60] + '...' if len(l) > 60 else l for l in j_cnt.index[::-1]]
    ax.set_yticklabels(labels, fontsize=8)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/03_top_journals.png")
    plt.close()
    print("  [03] Top journals saved.")
    return j_cnt

def fig_top_authors(df: pd.DataFrame):
    """상위 20명 저자 (논문 수 기준)."""
    author_list = []
    for row in df['authors']:
        author_list.extend(row)
    auth_cnt = Counter(author_list).most_common(20)
    names, counts = zip(*auth_cnt)
    # 성, 이름 약어 → 정리
    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(list(names)[::-1], list(counts)[::-1],
                   color=sns.color_palette('Greens_r', 20))
    ax.set_xlabel('Number of Publications', fontsize=12)
    ax.set_title('Top 20 Most Productive Authors', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, list(counts)[::-1]):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/04_top_authors.png")
    plt.close()
    print("  [04] Top authors saved.")
    return Counter(author_list)

def fig_top_countries(df: pd.DataFrame):
    """국가별 논문 수 (상위 20개국)."""
    country_list = []
    for row in df['countries']:
        country_list.extend(row)

    # 표준화
    replace_map = {
        'Peoples R China': 'China',
        'South Korea': 'South Korea',
        'Eng': 'England',
        'England': 'England',
        'Scotland': 'Scotland',
        'Wales': 'Wales',
        'North Ireland': 'North Ireland',
    }
    country_list = [replace_map.get(c, c) for c in country_list]
    c_cnt = Counter(country_list).most_common(20)
    countries, counts = zip(*c_cnt)

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.barh(list(countries)[::-1], list(counts)[::-1],
                   color=sns.color_palette('Oranges_r', 20))
    ax.set_xlabel('Number of Publications', fontsize=12)
    ax.set_title('Top 20 Countries by Publication Count', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, list(counts)[::-1]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/05_top_countries.png")
    plt.close()
    print("  [05] Top countries saved.")
    return Counter(country_list)

def fig_top_institutions(df: pd.DataFrame):
    """상위 20개 기관 (C3 필드)."""
    inst_list = []
    for row in df['institutions']:
        inst_list.extend(row)
    inst_cnt = Counter(inst_list).most_common(20)
    if not inst_cnt:
        print("  [06] No institution data.")
        return Counter()
    insts, counts = zip(*inst_cnt)

    fig, ax = plt.subplots(figsize=(13, 7))
    bars = ax.barh(list(insts)[::-1], list(counts)[::-1],
                   color=sns.color_palette('Purples_r', 20))
    ax.set_xlabel('Number of Publications', fontsize=12)
    ax.set_title('Top 20 Institutions by Publication Count', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, list(counts)[::-1]):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontsize=9)
    labels = [l[:55] + '...' if len(l) > 55 else l for l in insts[::-1]]
    ax.set_yticklabels(labels, fontsize=8)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/06_top_institutions.png")
    plt.close()
    print("  [06] Top institutions saved.")
    return Counter(inst_list)

def fig_keywords(df: pd.DataFrame):
    """저자 키워드 빈도 수평 막대 (상위 30개)."""
    kw_list = []
    for de in df['DE'].dropna():
        for kw in re.split(r'[;,]', de):
            kw = kw.strip().lower()
            if kw and len(kw) > 2:
                kw_list.append(kw)

    kw_cnt = Counter(kw_list).most_common(30)
    words, freqs = zip(*kw_cnt)

    fig, ax = plt.subplots(figsize=(12, 9))
    bars = ax.barh(list(words)[::-1], list(freqs)[::-1],
                   color=sns.color_palette('coolwarm', 30))
    ax.set_xlabel('Frequency', fontsize=12)
    ax.set_title('Top 30 Author Keywords', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, list(freqs)[::-1]):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontsize=8)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/07_top_keywords.png")
    plt.close()
    print("  [07] Top keywords saved.")
    return Counter(kw_list)

def fig_keyword_wordcloud(kw_cnt: Counter):
    """워드클라우드."""
    try:
        from wordcloud import WordCloud
    except ImportError:
        print("  [08] wordcloud not installed, skip.")
        return

    wc = WordCloud(
        width=1600, height=800,
        background_color='white',
        colormap='viridis',
        max_words=150,
        prefer_horizontal=0.8,
    ).generate_from_frequencies(dict(kw_cnt))

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title('Author Keyword Word Cloud (N=1,500 papers)',
                 fontsize=16, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/08_wordcloud.png")
    plt.close()
    print("  [08] Word cloud saved.")

def fig_most_cited(df: pd.DataFrame):
    """인용 TOP 15 논문 (수평 막대)."""
    top15 = df.nlargest(15, 'TC')[['TI', 'AU_count', 'PY', 'SO', 'TC']].copy()
    top15['label'] = top15.apply(
        lambda r: f"{str(r['TI'])[:55]}... ({int(r['PY']) if pd.notna(r['PY']) else '?'})", axis=1
    )

    fig, ax = plt.subplots(figsize=(13, 7))
    bars = ax.barh(top15['label'].values[::-1], top15['TC'].values[::-1],
                   color=sns.color_palette('Reds_r', 15))
    ax.set_xlabel('Times Cited', fontsize=12)
    ax.set_title('Top 15 Most Cited Papers', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, top15['TC'].values[::-1]):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontsize=9)
    ax.tick_params(axis='y', labelsize=8)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/09_most_cited.png")
    plt.close()
    print("  [09] Most cited saved.")
    return top15

def fig_citation_distribution(df: pd.DataFrame):
    """인용 수 분포 (Log scale)."""
    tc_vals = df['TC'][df['TC'] > 0]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # 왼쪽: 로그 스케일 히스토그램
    axes[0].hist(tc_vals, bins=50, color=PALETTE[4], edgecolor='white', alpha=0.85)
    axes[0].set_yscale('log')
    axes[0].set_xlabel('Times Cited', fontsize=11)
    axes[0].set_ylabel('Frequency (log scale)', fontsize=11)
    axes[0].set_title('Citation Distribution (log scale)', fontsize=12, fontweight='bold')

    # 오른쪽: Box plot by decade
    df_decade = df.dropna(subset=['PY']).copy()
    df_decade['Decade'] = (df_decade['PY'] // 10 * 10).astype(int).astype(str) + 's'
    decade_order = sorted(df_decade['Decade'].unique())
    sns.boxplot(data=df_decade, x='Decade', y='TC', order=decade_order,
                palette='Set3', ax=axes[1], showfliers=False)
    axes[1].set_yscale('log')
    axes[1].set_xlabel('Decade', fontsize=11)
    axes[1].set_ylabel('Times Cited (log scale)', fontsize=11)
    axes[1].set_title('Citation by Decade (no outliers)', fontsize=12, fontweight='bold')
    axes[1].tick_params(axis='x', rotation=30)

    plt.suptitle('Citation Analysis', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/10_citation_distribution.png")
    plt.close()
    print("  [10] Citation distribution saved.")

def fig_wos_categories(df: pd.DataFrame):
    """WoS 주제 카테고리 분포 (상위 15개)."""
    cat_list = []
    for wc in df['WC'].dropna():
        for c in wc.split(';'):
            c = c.strip()
            if c:
                cat_list.append(c)
    cat_cnt = Counter(cat_list).most_common(15)
    cats, counts = zip(*cat_cnt)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(list(cats)[::-1], list(counts)[::-1],
                   color=sns.color_palette('tab20', 15))
    ax.set_xlabel('Number of Publications', fontsize=12)
    ax.set_title('Top 15 WoS Subject Categories', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, list(counts)[::-1]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontsize=9)
    labels = [l[:58] + '...' if len(l) > 58 else l for l in cats[::-1]]
    ax.set_yticklabels(labels, fontsize=9)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/11_wos_categories.png")
    plt.close()
    print("  [11] WoS categories saved.")
    return Counter(cat_list)

def fig_keyword_cooccurrence(kw_cnt: Counter, df: pd.DataFrame, top_n: int = 40):
    """키워드 공출현 네트워크 (상위 40개 키워드)."""
    top_kws = {kw for kw, _ in kw_cnt.most_common(top_n)}
    G = nx.Graph()
    G.add_nodes_from(top_kws)

    co_cnt: Counter = Counter()
    for de in df['DE'].dropna():
        paper_kws = set()
        for kw in re.split(r'[;,]', de):
            kw = kw.strip().lower()
            if kw in top_kws:
                paper_kws.add(kw)
        for pair in combinations(sorted(paper_kws), 2):
            co_cnt[pair] += 1

    for (a, b), w in co_cnt.items():
        if w >= 3:
            G.add_edge(a, b, weight=w)

    # 고립 노드 제거
    G.remove_nodes_from(list(nx.isolates(G)))

    fig, ax = plt.subplots(figsize=(16, 14))
    pos = nx.spring_layout(G, seed=42, k=2.5)
    node_size = [kw_cnt[n] * 25 for n in G.nodes()]
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    nx.draw_networkx_nodes(G, pos, node_size=node_size,
                           node_color=PALETTE[1], alpha=0.85, ax=ax)
    nx.draw_networkx_edges(G, pos, width=[w * 0.15 for w in edge_weights],
                           edge_color='gray', alpha=0.5, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold', ax=ax)
    ax.set_title(f'Keyword Co-occurrence Network (Top {top_n} Keywords, edge ≥ 3)',
                 fontsize=14, fontweight='bold')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/12_keyword_network.png")
    plt.close()
    print("  [12] Keyword co-occurrence network saved.")

def fig_country_collaboration(df: pd.DataFrame):
    """국가 간 협력 네트워크 (논문당 2개국 이상)."""
    G = nx.Graph()
    co_cnt: Counter = Counter()
    for countries in df['countries']:
        uniq = list(set(countries))
        if len(uniq) >= 2:
            for pair in combinations(sorted(uniq), 2):
                co_cnt[pair] += 1

    top_pairs = co_cnt.most_common(60)
    for (a, b), w in top_pairs:
        G.add_edge(a, b, weight=w)

    if G.number_of_nodes() == 0:
        print("  [13] No collaboration data.")
        return

    fig, ax = plt.subplots(figsize=(16, 12))
    pos = nx.spring_layout(G, seed=77, k=3)
    degrees = dict(G.degree())
    node_size = [degrees[n] * 120 for n in G.nodes()]
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]

    nx.draw_networkx_nodes(G, pos, node_size=node_size,
                           node_color=PALETTE[5], alpha=0.9, ax=ax)
    nx.draw_networkx_edges(G, pos, width=[w * 0.3 for w in edge_weights],
                           edge_color='steelblue', alpha=0.5, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold', ax=ax)
    ax.set_title('International Collaboration Network (Top 60 country pairs)',
                 fontsize=14, fontweight='bold')
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/13_country_collaboration.png")
    plt.close()
    print("  [13] Country collaboration network saved.")

def fig_hindex_analysis(df: pd.DataFrame, auth_cnt: Counter):
    """상위 저자 H-index 추정 (논문 수 × 단순 근사)."""
    # 저자별 논문 인용 수 집계
    author_papers: dict[str, list[int]] = defaultdict(list)
    for _, row in df.iterrows():
        for au in row['authors']:
            author_papers[au].append(row['TC'])

    def h_index(cites):
        cites_sorted = sorted(cites, reverse=True)
        h = 0
        for i, c in enumerate(cites_sorted, 1):
            if c >= i:
                h = i
            else:
                break
        return h

    top30_authors = [au for au, _ in auth_cnt.most_common(30)]
    h_data = []
    for au in top30_authors:
        cites = author_papers[au]
        h_data.append({
            'Author': au,
            'Papers': len(cites),
            'H-index': h_index(cites),
            'Total_Citations': sum(cites),
            'Avg_Citations': round(sum(cites) / len(cites), 1) if cites else 0,
        })
    h_df = pd.DataFrame(h_data).sort_values('H-index', ascending=False).head(20)

    fig, ax = plt.subplots(figsize=(13, 7))
    bars = ax.barh(h_df['Author'][::-1], h_df['H-index'][::-1],
                   color=sns.color_palette('magma', 20))
    ax2 = ax.twiny()
    ax2.scatter(h_df['Total_Citations'][::-1],
                range(len(h_df)), color='crimson', zorder=5, s=60, label='Total Citations')
    ax.set_xlabel('H-index (within dataset)', fontsize=12, color='navy')
    ax2.set_xlabel('Total Citations (within dataset)', fontsize=11, color='crimson')
    ax.set_title('Top 20 Authors: H-index & Total Citations', fontsize=14, fontweight='bold')
    ax2.legend(loc='lower right', fontsize=10)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/14_author_hindex.png")
    plt.close()
    print("  [14] H-index analysis saved.")
    return h_df

def fig_language_distribution(df: pd.DataFrame):
    """언어 분포."""
    lang_cnt = df['LA'].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(lang_cnt.index, lang_cnt.values,
                  color=sns.color_palette('pastel', len(lang_cnt)))
    ax.set_xlabel('Language', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title('Language Distribution', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, lang_cnt.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                str(val), ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/15_language.png")
    plt.close()
    print("  [15] Language distribution saved.")

def fig_references_per_year(df: pd.DataFrame):
    """연도별 평균 참고문헌 수 추세."""
    yr_df = df.dropna(subset=['PY']).copy()
    yr_df = yr_df[yr_df['PY'] >= 1995]
    avg_nr = yr_df.groupby('PY')['NR'].mean().reset_index()

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(avg_nr['PY'], avg_nr['NR'], marker='s', color=PALETTE[3], linewidth=2)
    ax.fill_between(avg_nr['PY'], avg_nr['NR'], alpha=0.15, color=PALETTE[3])
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Average Reference Count', fontsize=12)
    ax.set_title('Average Number of References per Paper by Year', fontsize=14, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/16_avg_references.png")
    plt.close()
    print("  [16] Avg references saved.")

def fig_keyword_trend(df: pd.DataFrame):
    """주요 키워드 연도별 등장 빈도 추세 (상위 8개)."""
    target_kws = [
        'deep learning', 'video summarization', 'convolutional neural network',
        'object detection', 'attention', 'transformer',
        'video retrieval', 'action recognition',
    ]
    df2 = df.dropna(subset=['PY', 'DE']).copy()
    df2 = df2[(df2['PY'] >= 2000) & (df2['PY'] <= 2024)]

    rows = []
    for _, row in df2.iterrows():
        de_lower = str(row['DE']).lower()
        for kw in target_kws:
            if kw in de_lower:
                rows.append({'PY': int(row['PY']), 'keyword': kw})

    if not rows:
        print("  [17] No keyword trend data.")
        return

    kw_trend = pd.DataFrame(rows).groupby(['PY', 'keyword']).size().reset_index(name='count')

    fig, ax = plt.subplots(figsize=(14, 6))
    for kw in target_kws:
        sub = kw_trend[kw_trend['keyword'] == kw]
        if not sub.empty:
            ax.plot(sub['PY'], sub['count'], marker='o', linewidth=1.8, label=kw)

    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Key Concept Emergence Trend (2000–2024)', fontsize=14, fontweight='bold')
    ax.legend(fontsize=9, loc='upper left')
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/17_keyword_trend.png")
    plt.close()
    print("  [17] Keyword trend saved.")

def fig_collaboration_heatmap(df: pd.DataFrame, country_cnt: Counter):
    """상위 국가 간 협력 히트맵."""
    top_countries = [c for c, _ in country_cnt.most_common(15)]
    matrix = pd.DataFrame(0, index=top_countries, columns=top_countries)

    for countries in df['countries']:
        uniq = [c for c in set(countries) if c in top_countries]
        for a, b in combinations(sorted(uniq), 2):
            matrix.loc[a, b] += 1
            matrix.loc[b, a] += 1

    fig, ax = plt.subplots(figsize=(12, 10))
    mask = np.triu(np.ones_like(matrix, dtype=bool))
    sns.heatmap(matrix, mask=mask, annot=True, fmt='d', cmap='YlOrRd',
                linewidths=0.5, ax=ax, cbar_kws={'label': 'Co-authored Papers'})
    ax.set_title('International Collaboration Heatmap (Top 15 Countries)',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/18_collaboration_heatmap.png")
    plt.close()
    print("  [18] Collaboration heatmap saved.")

# ══════════════════════════════════════════════════════════════════════════════
# 4. 통계 요약 JSON 저장
# ══════════════════════════════════════════════════════════════════════════════
def save_summary(df, merged_yr, top15_cited, h_df, j_cnt, auth_cnt, country_cnt, cat_cnt):
    summary = {
        "total_records": len(df),
        "year_range": [int(df['PY'].min()), int(df['PY'].max())],
        "avg_tc": round(float(df['TC'].mean()), 2),
        "median_tc": round(float(df['TC'].median()), 2),
        "total_citations": int(df['TC'].sum()),
        "h_index_corpus": int(sum(1 for i, c in enumerate(sorted(df['TC'], reverse=True), 1) if c >= i)),
        "top5_journals": j_cnt.head(5).to_dict(),
        "top5_authors": dict(auth_cnt.most_common(5)),
        "top5_countries": dict(country_cnt.most_common(5)),
        "top5_categories": dict(cat_cnt.most_common(5)),
        "top10_cited_papers": top15_cited[['TI', 'PY', 'TC']].head(10).to_dict(orient='records'),
        "top10_h_index_authors": h_df[['Author', 'Papers', 'H-index', 'Total_Citations']].head(10).to_dict(orient='records'),
        "annual_stats": merged_yr.to_dict(orient='records'),
    }
    with open(f"{OUTPUT_DIR}/summary_stats.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    print("  [SUM] Summary JSON saved.")
    return summary

# ══════════════════════════════════════════════════════════════════════════════
# 5. 메인 실행
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 65)
    print("  WoS Bibliometrics Analysis — Video Analysis / Retrieval")
    print("=" * 65)

    print("\n[1] Loading & parsing WoS records...")
    records = load_all_records()

    print("[2] Building DataFrame...")
    df = build_dataframe(records)
    print(f"  DataFrame shape: {df.shape}")
    print(f"  Year range: {int(df['PY'].min())} – {int(df['PY'].max())}")
    print(f"  Avg citations: {df['TC'].mean():.2f}")

    print("\n[3] Generating figures...")
    merged_yr  = fig_annual_publication(df)
    fig_document_types(df)
    j_cnt      = fig_top_journals(df)
    auth_cnt   = fig_top_authors(df)
    country_cnt = fig_top_countries(df)
    inst_cnt   = fig_top_institutions(df)
    kw_cnt     = fig_keywords(df)
    fig_keyword_wordcloud(kw_cnt)
    top15_cited = fig_most_cited(df)
    fig_citation_distribution(df)
    cat_cnt    = fig_wos_categories(df)
    fig_keyword_cooccurrence(kw_cnt, df, top_n=40)
    fig_country_collaboration(df)
    h_df       = fig_hindex_analysis(df, auth_cnt)
    fig_language_distribution(df)
    fig_references_per_year(df)
    fig_keyword_trend(df)
    fig_collaboration_heatmap(df, country_cnt)

    print("\n[4] Saving summary statistics...")
    summary = save_summary(df, merged_yr, top15_cited, h_df, j_cnt,
                           auth_cnt, country_cnt, cat_cnt)

    print("\n" + "=" * 65)
    print("  ANALYSIS COMPLETE")
    print(f"  Output directory: {OUTPUT_DIR}")
    print("  Figures: 01–18  |  Summary: summary_stats.json")
    print("=" * 65)

    # 핵심 통계 요약 출력
    print(f"\n  Total records  : {summary['total_records']:,}")
    print(f"  Year range     : {summary['year_range'][0]} – {summary['year_range'][1]}")
    print(f"  Total citations: {summary['total_citations']:,}")
    print(f"  Mean TC        : {summary['avg_tc']}")
    print(f"  Corpus H-index : {summary['h_index_corpus']}")
    print(f"\n  Top-3 journals :")
    for j, c in list(summary['top5_journals'].items())[:3]:
        print(f"    {c:>4}  {j[:65]}")
    print(f"\n  Top-3 countries:")
    for co, c in list(summary['top5_countries'].items())[:3]:
        print(f"    {c:>4}  {co}")
    print(f"\n  Top-3 categories:")
    for ca, c in list(summary['top5_categories'].items())[:3]:
        print(f"    {c:>4}  {ca}")

if __name__ == '__main__':
    main()
