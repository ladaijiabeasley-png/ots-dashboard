import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PHL5 OTS Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }

/* KPI metric cards */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e4e7ec;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.04);
}
[data-testid="metric-container"] label {
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    letter-spacing: .07em !important;
    text-transform: uppercase !important;
    color: #9aa3af !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    letter-spacing: -.04em !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    border-bottom: 2px solid #e4e7ec;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px 8px 0 0;
    font-weight: 600;
    font-size: .85rem;
    color: #5a6472;
    border: none;
    padding: .5rem 1rem;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #1d4ed8 !important;
    border-bottom: 2px solid #1d4ed8;
}

/* Section headers */
.section-title {
    font-size: 1rem; font-weight: 700; color: #0f1924;
    letter-spacing: -.02em; margin: 1.5rem 0 .75rem;
    padding-bottom: .5rem; border-bottom: 1px solid #e4e7ec;
}
.kpi-header {
    font-size: 1.5rem; font-weight: 800; letter-spacing: -.04em; color: #0f1924;
}

/* Shift badge */
.badge { display:inline-block; padding:.2rem .55rem; border-radius:6px; font-size:.75rem; font-weight:700; font-family:'DM Mono',monospace; }
.badge-s1 { background:#ede9fe; color:#6d28d9; }
.badge-s2 { background:#dbeafe; color:#1d4ed8; }
.badge-s4 { background:#f3f4f6; color:#374151; }
.badge-s5 { background:#fef3c7; color:#92400e; }

/* Shift summary card */
.shift-card {
    background: white; border: 1px solid #e4e7ec; border-radius: 12px;
    padding: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,.06);
}

/* Insight cards */
.insight-card {
    background: white; border: 1px solid #e4e7ec; border-radius: 12px;
    padding: 1rem 1.25rem; display: flex; gap: .75rem; align-items: flex-start;
    box-shadow: 0 1px 3px rgba(0,0,0,.04); margin-bottom: .6rem;
}
.insight-icon { font-size: 1.1rem; margin-top: 1px; }
.insight-text { font-size: .84rem; color: #5a6472; line-height: 1.55; }
.insight-text strong { color: #0f1924; }

/* Tag pills */
.tag { padding:.2rem .55rem; border-radius:99px; font-size:.7rem; font-weight:700; border:1px solid; }
.tag-excellent { background:#f0fdf4; color:#16a34a; border-color:#bbf7d0; }
.tag-fair      { background:#fffbeb; color:#d97706; border-color:#fde68a; }
.tag-poor      { background:#fef2f2; color:#dc2626; border-color:#fecaca; }

/* Top banner */
.top-banner {
    background: linear-gradient(135deg, #0f1924 0%, #1d4ed8 100%);
    border-radius: 16px; padding: 1.5rem 2rem; margin-bottom: 1.5rem;
    display: flex; align-items: center; justify-content: space-between;
}

/* Upload area */
.upload-hint {
    background: #f0f6ff; border: 2px dashed #93c5fd; border-radius: 12px;
    padding: 2rem; text-align: center; margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── Shift assignment ──────────────────────────────────────────────────────────
def assign_shift(dow, cut_str):
    try:
        h, m = map(int, str(cut_str).strip().split(':'))
        mins = h * 60 + m
        if dow <= 3:
            return 'S1' if 450 <= mins < 1080 else 'S2'
        return 'S4' if 450 <= mins < 1170 else 'S5'
    except:
        return 'Unknown'

# ── Parse Excel ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def parse_excel(file_bytes):
    raw = pd.read_excel(io.BytesIO(file_bytes), sheet_name=0, header=None)
    data = raw.iloc[1:].copy().reset_index(drop=True)
    data.columns = range(len(data.columns))
    data[5] = data[5].ffill()
    data[4] = data[4].ffill()
    data[2] = data[2].ffill()
    bad = {'Cut Time', 'ESD Total', 'Total', 'nan', ''}
    mask = (data[6].notna() & ~data[6].astype(str).isin(bad) &
            data[5].notna() & ~data[5].astype(str).isin(['ESD','Total','nan','']))
    df = data[mask].copy()
    df['Date'] = pd.to_datetime(df[5].astype(str), format='%m/%d/%Y', errors='coerce')
    df = df[df['Date'].notna()].copy()

    def norm(t):
        s = str(t).strip()
        if ':' in s:
            p = s.split(':')
            return f"{int(p[0]):02d}:{int(p[1]):02d}"
        return s

    df['CutTime']      = df[6].apply(norm)
    df['Due_Qty']      = pd.to_numeric(df[7],  errors='coerce').fillna(0).astype(int)
    df['Late_Packed']  = pd.to_numeric(df[8],  errors='coerce').fillna(0).astype(int)
    df['Late_Loaded']  = pd.to_numeric(df[9],  errors='coerce').fillna(0).astype(int)
    df['Late_Shipped'] = pd.to_numeric(df[10], errors='coerce').fillna(0).astype(int)
    df['WW']  = pd.to_numeric(df[4], errors='coerce').fillna(0).astype(int)
    df['FY']  = pd.to_numeric(df[2], errors='coerce').fillna(0).astype(int)
    df['DOW'] = df['Date'].dt.dayofweek
    df['Shift']   = df.apply(lambda r: assign_shift(r['DOW'], r['CutTime']), axis=1)
    df['DayName'] = df['Date'].dt.day_name()
    df['On_Time'] = df['Due_Qty'] - df['Late_Shipped']
    return df

# ── Colors ────────────────────────────────────────────────────────────────────
SHIFT_COLORS = {'S1': '#6366f1', 'S2': '#3b82f6', 'S4': '#6b7280', 'S5': '#f59e0b'}
SHIFT_SCHED  = {
    'S1': 'Mon–Thu · 7:30a–6:00p', 'S2': 'Mon–Thu · 6:30p–5:00a',
    'S4': 'Fri–Sun · 7:30a–7:30p', 'S5': 'Fri–Sun · 7:30p–7:30a',
}

def pct(num, den): return round(num / den * 100, 2) if den else 0
def ots_color(v): return '#16a34a' if v >= 95 else ('#d97706' if v >= 90 else '#dc2626')
def ots_emoji(v): return '🟢' if v >= 95 else ('🟡' if v >= 90 else '🔴')

# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
def main():

    # ── Header ────────────────────────────────────────────────────────────────
    col_logo, col_title, col_upload = st.columns([.08, .7, .22])
    with col_logo:
        st.markdown("<div style='font-size:2.5rem;padding-top:.3rem'>📦</div>", unsafe_allow_html=True)
    with col_title:
        st.markdown("<div class='kpi-header'>PHL5 OTS Weekly Dashboard</div>", unsafe_allow_html=True)
        st.caption("On-Time Shipment Analytics · Specialty FC · Work Week: Saturday – Friday")
    with col_upload:
        uploaded = st.file_uploader("", type=["xlsx","xls"], label_visibility="collapsed",
                                    help="Upload your weekly OTS .xlsx file")

    if not uploaded:
        st.markdown("---")
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("""
            <div class='upload-hint'>
                <div style='font-size:2.5rem;margin-bottom:.5rem'>☁️</div>
                <div style='font-weight:700;font-size:1.1rem;margin-bottom:.25rem'>Drop your .xlsx file above</div>
                <div style='color:#6b7280;font-size:.9rem'>File can contain multiple weeks — latest week becomes the focus</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### How it works")
            steps = [
                ("1", "Upload your weekly OTS .xlsx download"),
                ("2", "Shifts auto-assigned by date + cut time"),
                ("3", "Latest week shown as main dashboard"),
                ("4", "All weeks feed week-over-week trend chart"),
                ("5", "Share the app URL — everyone sees it live"),
            ]
            for num, text in steps:
                st.markdown(f"**{num}.** {text}")

            st.markdown("##### Shift Schedule")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("🟣 **S1** · Mon–Thu 7:30a–6:00p")
                st.markdown("⚫ **S4** · Fri–Sun 7:30a–7:30p")
            with c2:
                st.markdown("🔵 **S2** · Mon–Thu 6:30p–5:00a")
                st.markdown("🟡 **S5** · Fri–Sun 7:30p–7:30a")
        return

    # ── Load data ─────────────────────────────────────────────────────────────
    with st.spinner("Processing your data…"):
        try:
            df = parse_excel(uploaded.read())
        except Exception as e:
            st.error(f"⚠️ Error reading file: {e}")
            return

    weeks      = sorted(df['WW'].unique())
    latest_ww  = max(weeks)
    cur        = df[df['WW'] == latest_ww].copy()
    fy         = int(cur['FY'].iloc[0]) if len(cur) else 0

    # Week selector in sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        selected_ww = st.selectbox("View Week", options=weeks[::-1],
                                   format_func=lambda w: f"WW{w}{' (latest)' if w==latest_ww else ''}",
                                   index=0)
        st.markdown("---")
        st.markdown("### 📋 Shift Schedule")
        for sh, sched in SHIFT_SCHED.items():
            st.markdown(f"**{sh}** · {sched}")
        st.markdown("---")
        st.caption(f"File contains **{len(weeks)}** week(s): {', '.join(f'WW{w}' for w in weeks)}")

    cur = df[df['WW'] == selected_ww].copy()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    tq  = int(cur['Due_Qty'].sum())
    tlp = int(cur['Late_Packed'].sum())
    tll = int(cur['Late_Loaded'].sum())
    tls = int(cur['Late_Shipped'].sum())
    otp = pct(tq-tlp, tq)
    otl = pct(tq-tll, tq)
    ots = pct(tq-tls, tq)

    date_min = cur['Date'].min().strftime('%m/%d/%Y')
    date_max = cur['Date'].max().strftime('%m/%d/%Y')

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#0f1924,#1d4ed8);border-radius:14px;
    padding:1.2rem 1.75rem;margin-bottom:1.25rem;color:white;display:flex;
    justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem'>
        <div>
            <div style='font-size:1.2rem;font-weight:800;letter-spacing:-.03em'>
                Work Week {selected_ww} &nbsp;·&nbsp; FY{fy}
            </div>
            <div style='opacity:.7;font-size:.85rem;margin-top:.2rem'>
                {date_min} – {date_max} &nbsp;·&nbsp; {len(cur):,} cut-time records &nbsp;·&nbsp;
                {len(weeks)} week(s) loaded
            </div>
        </div>
        <div style='font-size:1.5rem'>{ots_emoji(ots)} Overall OTS: <strong>{ots}%</strong></div>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Overall OTP", f"{otp}%", help="On-Time Packed")
    k2.metric("Overall OTL", f"{otl}%", help="On-Time Loading")
    k3.metric("Overall OTS", f"{ots}%", help="On-Time Shipment")
    k4.metric("Total Volume", f"{tq:,}", help="Units due this week")
    k5.metric("Late Shipped", f"{tls:,}", delta=f"-{round(tls/tq*100,1)}% of volume" if tq else None,
              delta_color="inverse")

    st.markdown("---")

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Shift Overview", "📈 Trends", "🔍 Analysis", "📋 Cut Detail"])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — Shift Overview
    # ════════════════════════════════════════════════════════════════════════
    with tab1:

        # Shift summaries
        shift_data = []
        for sh in ['S1','S2','S4','S5']:
            sg = cur[cur['Shift'] == sh]
            if not len(sg): continue
            sq  = int(sg['Due_Qty'].sum())
            slp = int(sg['Late_Packed'].sum())
            sll = int(sg['Late_Loaded'].sum())
            sls = int(sg['Late_Shipped'].sum())
            shift_data.append({
                'shift': sh, 'units': sq, 'late_packed': slp,
                'late_loaded': sll, 'late_shipped': sls,
                'otp': pct(sq-slp,sq), 'otl': pct(sq-sll,sq), 'ots': pct(sq-sls,sq)
            })

        if not shift_data:
            st.warning("No shift data found for this week.")
            return

        st.markdown("<div class='section-title'>Performance by Shift</div>", unsafe_allow_html=True)
        cols = st.columns(len(shift_data))
        for col, s in zip(cols, shift_data):
            with col:
                color = ots_color(s['ots'])
                st.markdown(f"""
                <div class='shift-card'>
                    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:.85rem'>
                        <span class='badge badge-{s["shift"].lower()}'>{s["shift"]}</span>
                        <span style='font-size:.75rem;color:#9aa3af'>{s["units"]:,} units</span>
                    </div>
                    <div style='margin-bottom:.5rem'>
                        <div style='display:flex;justify-content:space-between;margin-bottom:.2rem'>
                            <span style='font-size:.72rem;color:#9aa3af;font-weight:500'>OTP</span>
                            <span style='font-size:.72rem;font-weight:700;color:{ots_color(s["otp"])}'>{s["otp"]}%</span>
                        </div>
                        <div style='height:4px;background:#f0f2f5;border-radius:2px'>
                            <div style='height:4px;width:{max(0,(s["otp"]-85)/15*100):.1f}%;background:{ots_color(s["otp"])};border-radius:2px'></div>
                        </div>
                    </div>
                    <div style='margin-bottom:.5rem'>
                        <div style='display:flex;justify-content:space-between;margin-bottom:.2rem'>
                            <span style='font-size:.72rem;color:#9aa3af;font-weight:500'>OTL</span>
                            <span style='font-size:.72rem;font-weight:700;color:{ots_color(s["otl"])}'>{s["otl"]}%</span>
                        </div>
                        <div style='height:4px;background:#f0f2f5;border-radius:2px'>
                            <div style='height:4px;width:{max(0,(s["otl"]-85)/15*100):.1f}%;background:{ots_color(s["otl"])};border-radius:2px'></div>
                        </div>
                    </div>
                    <div style='margin-bottom:.75rem'>
                        <div style='display:flex;justify-content:space-between;margin-bottom:.2rem'>
                            <span style='font-size:.72rem;color:#9aa3af;font-weight:500'>OTS</span>
                            <span style='font-size:.72rem;font-weight:700;color:{color}'>{s["ots"]}%</span>
                        </div>
                        <div style='height:4px;background:#f0f2f5;border-radius:2px'>
                            <div style='height:4px;width:{max(0,(s["ots"]-85)/15*100):.1f}%;background:{color};border-radius:2px'></div>
                        </div>
                    </div>
                    <div style='border-top:1px solid #e4e7ec;padding-top:.6rem;display:flex;gap:.6rem;flex-wrap:wrap'>
                        <span style='font-size:.7rem;color:#9aa3af'><b style="color:#5a6472">{s["late_packed"]:,}</b> late packed</span>
                        <span style='font-size:.7rem;color:#9aa3af'><b style="color:#5a6472">{s["late_shipped"]:,}</b> late shipped</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Rankings
        st.markdown("<div class='section-title'>Shift Rankings</div>", unsafe_allow_html=True)
        ranked = sorted(shift_data, key=lambda x: x['ots'], reverse=True)
        medals = ['🥇','🥈','🥉','4️⃣']
        rlabels = ['CHAMPION','RUNNER-UP','CONTENDER','NEEDS FOCUS']
        rcols = st.columns(4)
        for i, (s, col) in enumerate(zip(ranked, rcols)):
            with col:
                border = '#fbbf24' if i==0 else ('#fecaca' if i==3 else '#e4e7ec')
                bg = 'linear-gradient(135deg,#fffbeb,#fff)' if i==0 else ('linear-gradient(135deg,#fef2f2,#fff)' if i==3 else 'white')
                lbl_color = '#d97706' if i==0 else ('#dc2626' if i==3 else '#6b7280')
                st.markdown(f"""
                <div style='background:{bg};border:1px solid {border};border-radius:12px;
                padding:1.4rem 1rem;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.06)'>
                    <div style='font-size:1.8rem;margin-bottom:.3rem'>{medals[i]}</div>
                    <span class='badge badge-{s["shift"].lower()}'>{s["shift"]}</span>
                    <div style='font-size:1.7rem;font-weight:800;letter-spacing:-.04em;
                    color:{ots_color(s["ots"])};margin:.4rem 0 .2rem'>{s["ots"]}%</div>
                    <div style='font-size:.62rem;font-weight:800;letter-spacing:.1em;
                    text-transform:uppercase;color:{lbl_color};margin-bottom:.3rem'>{rlabels[i]}</div>
                    <div style='font-size:.73rem;color:#9aa3af'>{s["units"]:,} units</div>
                </div>
                """, unsafe_allow_html=True)

        # OTS bar chart
        st.markdown("<div class='section-title'>OTS% vs OTP% by Shift</div>", unsafe_allow_html=True)
        fig_bar = go.Figure()
        for metric, opacity in [('otp', 0.35), ('ots', 1.0)]:
            fig_bar.add_trace(go.Bar(
                name=metric.upper(),
                x=[s['shift'] for s in shift_data],
                y=[s[metric] for s in shift_data],
                marker_color=[f"rgba({int(SHIFT_COLORS[s['shift']][1:3],16)},"
                              f"{int(SHIFT_COLORS[s['shift']][3:5],16)},"
                              f"{int(SHIFT_COLORS[s['shift']][5:7],16)},{opacity})"
                              for s in shift_data],
                text=[f"{s[metric]}%" for s in shift_data],
                textposition='outside',
            ))
        fig_bar.update_layout(
            barmode='group', height=340,
            margin=dict(l=0,r=0,t=20,b=0),
            plot_bgcolor='white', paper_bgcolor='white',
            yaxis=dict(range=[85,101], ticksuffix='%', gridcolor='#f0f2f5'),
            xaxis=dict(gridcolor='#f0f2f5'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            font=dict(family='DM Sans'),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — Trends
    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("<div class='section-title'>OTS% — Week over Week Trend</div>", unsafe_allow_html=True)

        wow_rows = []
        for ww in weeks:
            wd = df[df['WW'] == ww]
            wq = int(wd['Due_Qty'].sum())
            wls = int(wd['Late_Shipped'].sum())
            overall_ots = pct(wq-wls, wq)
            row = {'WW': f'WW{ww}', 'Overall': overall_ots}
            for sh in ['S1','S2','S4','S5']:
                sg = wd[wd['Shift']==sh]
                if len(sg):
                    sq = int(sg['Due_Qty'].sum()); sls = int(sg['Late_Shipped'].sum())
                    row[sh] = pct(sq-sls, sq)
                else:
                    row[sh] = None
            wow_rows.append(row)

        fig_wow = go.Figure()
        for sh in ['S1','S2','S4','S5']:
            vals = [r[sh] for r in wow_rows]
            fig_wow.add_trace(go.Scatter(
                x=[r['WW'] for r in wow_rows], y=vals, name=sh,
                mode='lines+markers',
                line=dict(color=SHIFT_COLORS[sh], width=2.5),
                marker=dict(size=7, color=SHIFT_COLORS[sh]),
                connectgaps=True,
            ))
        fig_wow.add_trace(go.Scatter(
            x=[r['WW'] for r in wow_rows], y=[r['Overall'] for r in wow_rows],
            name='Overall', mode='lines+markers',
            line=dict(color='#0f1924', width=2, dash='dash'),
            marker=dict(size=6, color='#0f1924'),
        ))
        fig_wow.update_layout(
            height=380, margin=dict(l=0,r=0,t=20,b=0),
            plot_bgcolor='white', paper_bgcolor='white',
            yaxis=dict(range=[85,101], ticksuffix='%', gridcolor='#f0f2f5', title='OTS%'),
            xaxis=dict(gridcolor='#f0f2f5', title='Work Week'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            font=dict(family='DM Sans'),
            hovermode='x unified',
        )
        st.plotly_chart(fig_wow, use_container_width=True)

        # Daily OTS trend for current week
        st.markdown("<div class='section-title'>Daily OTS% — Current Week by Shift</div>", unsafe_allow_html=True)
        daily_rows = []
        for date, dg in cur.groupby('Date'):
            row = {'Date': date.strftime('%a %m/%d')}
            for sh in ['S1','S2','S4','S5']:
                sg = dg[dg['Shift']==sh]
                if len(sg):
                    sq=int(sg['Due_Qty'].sum()); sls=int(sg['Late_Shipped'].sum())
                    row[sh] = pct(sq-sls,sq)
                else:
                    row[sh] = None
            daily_rows.append(row)

        fig_daily = go.Figure()
        for sh in ['S1','S2','S4','S5']:
            vals = [r.get(sh) for r in daily_rows]
            if any(v is not None for v in vals):
                fig_daily.add_trace(go.Bar(
                    name=sh, x=[r['Date'] for r in daily_rows], y=vals,
                    marker_color=SHIFT_COLORS[sh],
                    text=[f"{v}%" if v else '' for v in vals],
                    textposition='outside',
                ))
        fig_daily.update_layout(
            barmode='group', height=340,
            margin=dict(l=0,r=0,t=20,b=0),
            plot_bgcolor='white', paper_bgcolor='white',
            yaxis=dict(range=[85,102], ticksuffix='%', gridcolor='#f0f2f5'),
            xaxis=dict(gridcolor='#f0f2f5'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            font=dict(family='DM Sans'),
        )
        st.plotly_chart(fig_daily, use_container_width=True)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3 — Analysis
    # ════════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("<div class='section-title'>Pack → Ship Conversion Gap Analysis</div>", unsafe_allow_html=True)

        gap_data = []
        for s in shift_data:
            g = round(s['otp'] - s['ots'], 2)
            gap_data.append({
                **s,
                'gap': g,
                'rating': 'Excellent' if g<=1 else ('Fair' if g<=3 else 'Poor'),
                'otp_otl_gap': round(s['otp']-s['otl'], 2),
                'otl_ots_gap': round(s['otl']-s['ots'], 2),
            })

        # Gap table
        col_h = st.columns([1,1.2,1,1.2,1,1.2,1,1.2])
        headers = ['Shift','OTP%','→','OTL%','→','OTS%','Total Gap','Rating']
        for col, h in zip(col_h, headers):
            col.markdown(f"<span style='font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#9aa3af'>{h}</span>", unsafe_allow_html=True)

        for g in gap_data:
            cols = st.columns([1,1.2,1,1.2,1,1.2,1,1.2])
            cols[0].markdown(f"<span class='badge badge-{g['shift'].lower()}'>{g['shift']}</span>", unsafe_allow_html=True)
            cols[1].markdown(f"<span style='font-family:DM Mono,monospace'>{g['otp']}%</span>", unsafe_allow_html=True)
            cols[2].markdown(f"<span style='color:#9aa3af;font-size:.78rem'>–{g['otp_otl_gap']}pp →</span>", unsafe_allow_html=True)
            cols[3].markdown(f"<span style='font-family:DM Mono,monospace'>{g['otl']}%</span>", unsafe_allow_html=True)
            cols[4].markdown(f"<span style='color:#9aa3af;font-size:.78rem'>–{g['otl_ots_gap']}pp →</span>", unsafe_allow_html=True)
            cols[5].markdown(f"<span style='font-family:DM Mono,monospace;font-weight:700;color:{ots_color(g['ots'])}'>{g['ots']}%</span>", unsafe_allow_html=True)
            cols[6].markdown(f"<span style='font-family:DM Mono,monospace;color:#5a6472'>+{g['gap']}pp</span>", unsafe_allow_html=True)
            rat = g['rating']
            icon = '✅' if rat=='Excellent' else ('⚠️' if rat=='Fair' else '🚨')
            cols[7].markdown(f"<span class='tag tag-{rat.lower()}'>{icon} {rat}</span>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Gap waterfall chart
        st.markdown("<div class='section-title'>OTP → OTL → OTS Waterfall by Shift</div>", unsafe_allow_html=True)
        fig_gap = go.Figure()
        for s in gap_data:
            fig_gap.add_trace(go.Scatter(
                x=['OTP', 'OTL', 'OTS'], y=[s['otp'], s['otl'], s['ots']],
                name=s['shift'], mode='lines+markers',
                line=dict(color=SHIFT_COLORS[s['shift']], width=2.5),
                marker=dict(size=8),
            ))
        fig_gap.update_layout(
            height=320, margin=dict(l=0,r=0,t=20,b=0),
            plot_bgcolor='white', paper_bgcolor='white',
            yaxis=dict(ticksuffix='%', gridcolor='#f0f2f5'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            font=dict(family='DM Sans'), hovermode='x unified',
        )
        st.plotly_chart(fig_gap, use_container_width=True)

        # Key Insights
        st.markdown("<div class='section-title'>Key Insights</div>", unsafe_allow_html=True)
        best  = max(shift_data, key=lambda x: x['ots'])
        worst = min(shift_data, key=lambda x: x['ots'])
        big_gap = next((g for g in gap_data if g['gap']>3), None)
        avg_otp = round(sum(s['otp'] for s in shift_data)/len(shift_data), 1)

        insights = [
            ("📦", f"Packing performance is strong across all shifts (avg OTP: <strong>{avg_otp}%</strong>). Pack operations are not the primary bottleneck."),
            ("🌟", f"<strong>{best['shift']}</strong> leads with <strong>{best['ots']}% OTS</strong> on {best['units']:,} units. Pack→ship gap is only {round(best['otp']-best['ots'],2)}pp — outstanding conversion."),
            ("🔍", f"<strong>{worst['shift']}</strong> has the lowest OTS at <strong>{worst['ots']}%</strong> despite {worst['otp']}% OTP. The {round(worst['otp']-worst['ots'],2)}pp gap suggests downstream bottlenecks."),
            ("⚠️" if big_gap else "✅",
             f"<strong>{big_gap['shift']}</strong> shows a {big_gap['gap']}pp conversion gap — signals dock/sortation/linehaul compression issues."
             if big_gap else "All shifts show solid pack-to-ship conversion (&lt;3pp gap). Maintain cut-time discipline."),
            ("🎯", f"Weekend shifts (S4/S5) generally show stronger conversion. These can serve as a process benchmark for weekday operations."),
        ]
        c1, c2 = st.columns(2)
        for i, (icon, text) in enumerate(insights):
            col = c1 if i % 2 == 0 else c2
            with col:
                st.markdown(f"""
                <div class='insight-card'>
                    <div class='insight-icon'>{icon}</div>
                    <div class='insight-text'>{text}</div>
                </div>""", unsafe_allow_html=True)

        # Worst cut times
        st.markdown("<div class='section-title'>⚠️ Attention Needed — Lowest OTS% Cut Times</div>", unsafe_allow_html=True)
        cuts_df = cur.copy()
        cuts_df['OTS%'] = cuts_df.apply(lambda r: pct(r['Due_Qty']-r['Late_Shipped'], r['Due_Qty']), axis=1)
        cuts_df['OTP%'] = cuts_df.apply(lambda r: pct(r['Due_Qty']-r['Late_Packed'],  r['Due_Qty']), axis=1)
        worst_cuts = cuts_df[cuts_df['Due_Qty']>50].nsmallest(10, 'OTS%')[
            ['Date','CutTime','Shift','Due_Qty','Late_Shipped','OTS%']
        ].copy()
        worst_cuts['Date'] = worst_cuts['Date'].dt.strftime('%a %m/%d')
        worst_cuts.columns = ['Day','Cut Time','Shift','Due Units','Late Shipped','OTS%']
        st.dataframe(
            worst_cuts.style
                .format({'OTS%': '{:.1f}%', 'Due Units': '{:,}', 'Late Shipped': '{:,}'})
                .applymap(lambda v: 'color: #dc2626; font-weight: 700' if isinstance(v, float) and v < 50 else
                          ('color: #d97706; font-weight: 700' if isinstance(v, float) and v < 90 else ''), subset=['OTS%']),
            use_container_width=True, hide_index=True,
        )

    # ════════════════════════════════════════════════════════════════════════
    # TAB 4 — Cut Detail
    # ════════════════════════════════════════════════════════════════════════
    with tab4:
        st.markdown("<div class='section-title'>Cut Time Detail — Full Table</div>", unsafe_allow_html=True)

        # Filters
        f1, f2, f3 = st.columns([2,1,1])
        with f1:
            search = st.text_input("🔍 Search", placeholder="Filter by day or cut time…", label_visibility="collapsed")
        with f2:
            shift_filter = st.selectbox("Shift", ["All Shifts","S1","S2","S4","S5"], label_visibility="collapsed")
        with f3:
            ots_filter = st.selectbox("OTS Filter", ["All", "< 90% (Action)", "90-95% (Watch)", "≥ 95% (Good)"], label_visibility="collapsed")

        detail = cur.copy()
        detail['OTS%'] = detail.apply(lambda r: pct(r['Due_Qty']-r['Late_Shipped'], r['Due_Qty']), axis=1)
        detail['OTL%'] = detail.apply(lambda r: pct(r['Due_Qty']-r['Late_Loaded'],  r['Due_Qty']), axis=1)
        detail['OTP%'] = detail.apply(lambda r: pct(r['Due_Qty']-r['Late_Packed'],  r['Due_Qty']), axis=1)
        detail['Day']  = detail['Date'].dt.strftime('%a %m/%d')
        detail = detail.sort_values(['Date','CutTime'])

        if search:
            detail = detail[detail['Day'].str.contains(search, case=False) |
                            detail['CutTime'].str.contains(search, case=False)]
        if shift_filter != "All Shifts":
            detail = detail[detail['Shift'] == shift_filter]
        if ots_filter == "< 90% (Action)":
            detail = detail[detail['OTS%'] < 90]
        elif ots_filter == "90-95% (Watch)":
            detail = detail[(detail['OTS%'] >= 90) & (detail['OTS%'] < 95)]
        elif ots_filter == "≥ 95% (Good)":
            detail = detail[detail['OTS%'] >= 95]

        display = detail[['Day','CutTime','Shift','Due_Qty','Late_Packed','Late_Loaded','Late_Shipped','OTP%','OTL%','OTS%']].copy()
        display.columns = ['Day','Cut Time','Shift','Due Units','Late Packed','Late Loaded','Late Shipped','OTP%','OTL%','OTS%']

        st.caption(f"Showing {len(display):,} of {len(cur):,} rows")
        st.dataframe(
            display.style
                .format({'Due Units':'{:,}','Late Packed':'{:,}','Late Loaded':'{:,}',
                         'Late Shipped':'{:,}','OTP%':'{:.1f}%','OTL%':'{:.1f}%','OTS%':'{:.1f}%'})
                .applymap(lambda v: 'color:#dc2626;font-weight:700' if isinstance(v,float) and v<90
                          else ('color:#d97706;font-weight:700' if isinstance(v,float) and v<95
                          else ('color:#16a34a;font-weight:700' if isinstance(v,float) and v>=95 else '')),
                          subset=['OTS%']),
            use_container_width=True, hide_index=True, height=500,
        )

        # Download button
        csv = display.to_csv(index=False)
        st.download_button("⬇️ Download as CSV", csv,
                           file_name=f"OTS_WW{selected_ww}_detail.csv", mime="text/csv")

if __name__ == '__main__':
    main()
