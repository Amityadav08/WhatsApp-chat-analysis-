import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

import preprocessor
import helper

# ------------------------------------------------------------------
# Page config & global styles
# ------------------------------------------------------------------
st.set_page_config(
    page_title="WhatsApp Chat Analyzer",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

ACCENT = "#25D366"
BG = "#0B141A"
CARD_BG = "#111B21"
MUTED = "#8696A0"
CHART_COLORS = ["#25D366", "#53BDEB", "#F7B801", "#FF6B6B", "#A78BFA"]

st.markdown(
    f"""
    <style>
    .block-container {{ padding-top: 2rem; padding-bottom: 3rem; }}

    .metric-card {{
        background: {CARD_BG};
        border: 1px solid rgba(134,150,160,0.15);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        text-align: left;
    }}
    .metric-card .label {{
        color: {MUTED};
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }}
    .metric-card .value {{
        color: #E9EDEF;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1.1;
    }}
    .metric-card .accent {{ color: {ACCENT}; }}

    .hero {{
        background: {CARD_BG};
        border: 1px solid rgba(134,150,160,0.15);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        text-align: center;
        margin-top: 2rem;
    }}
    .hero h1 {{ margin-bottom: 0.5rem; }}
    .hero p {{ color: {MUTED}; max-width: 560px; margin: 0 auto; }}

    section[data-testid="stSidebar"] .stButton button {{
        width: 100%;
        background: {ACCENT};
        color: #0B141A;
        font-weight: 700;
        border: none;
        border-radius: 8px;
    }}
    section[data-testid="stSidebar"] .stButton button:hover {{
        background: #1FB855;
        color: #0B141A;
    }}

    h1, h2, h3 {{ letter-spacing: -0.02em; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def metric_card(label: str, value, accent: bool = False) -> str:
    value_class = "value accent" if accent else "value"
    return f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="{value_class}">{value:,}</div>
    </div>
    """


def style_fig(fig, height: int = 380):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(color="#E9EDEF"),
        hoverlabel=dict(bgcolor=CARD_BG),
    )
    fig.update_xaxes(gridcolor="rgba(134,150,160,0.12)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(134,150,160,0.12)", zeroline=False)
    return fig


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"## 💬 WhatsApp Chat Analyzer")
    st.caption("Upload an exported chat (.txt) to explore stats, timelines, activity and more.")
    st.divider()

    uploaded_file = st.file_uploader("Upload chat export", type=["txt"])

    selected_user = None
    df = None

    if uploaded_file is not None:
        data = uploaded_file.getvalue().decode("utf-8")
        head = data[:40].lower()
        is_12h = "pm" in head or "am" in head
        try:
            df = preprocessor.preprocess(data, is_12h)
        except Exception:
            st.error("Couldn't parse this file. Make sure it's a WhatsApp chat export (.txt).")
            df = None

        if df is not None and not df.empty:
            user_list = df["user"].unique().tolist()
            if "group_notification" in user_list:
                user_list.remove("group_notification")
            user_list.sort()
            user_list.insert(0, "Overall")

            selected_user = st.selectbox("Analyze for", user_list)
            run = st.button("Run Analysis", use_container_width=True)
            if run:
                st.session_state["run_analysis"] = True
                st.session_state["selected_user"] = selected_user

    st.divider()
    st.caption("Tip: export a chat from WhatsApp via ⋮ → More → Export chat → Without media.")


# ------------------------------------------------------------------
# Empty state
# ------------------------------------------------------------------
if df is None or not st.session_state.get("run_analysis"):
    st.markdown(
        """
        <div class="hero">
            <h1>💬 WhatsApp Chat Analyzer</h1>
            <p>Turn your chat history into insights &mdash; message trends, most active
            members, busiest hours, favorite words and emojis. Upload a chat export
            in the sidebar to get started.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    for col, (icon, title, desc) in zip(
        (c1, c2, c3),
        [
            ("📈", "Timelines", "Monthly and daily message trends over the life of the chat."),
            ("🔥", "Activity Maps", "Busiest days, months and an hour-by-hour weekly heatmap."),
            ("😀", "Words & Emojis", "Word cloud, most common words and emoji breakdown."),
        ],
    ):
        with col:
            st.markdown(
                f"""
                <div class="metric-card" style="margin-top:1rem;">
                    <div style="font-size:1.6rem;">{icon}</div>
                    <div class="value" style="font-size:1.1rem; margin:0.35rem 0;">{title}</div>
                    <div class="label" style="text-transform:none; letter-spacing:0;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.stop()

selected_user = st.session_state.get("selected_user", "Overall")
if selected_user not in df["user"].unique().tolist() + ["Overall"]:
    selected_user = "Overall"

# ------------------------------------------------------------------
# Header + top stats
# ------------------------------------------------------------------
scope = "Everyone" if selected_user == "Overall" else selected_user
st.markdown(f"# Chat Insights · {scope}")
st.caption(f"{df['only_date'].min()} → {df['only_date'].max()}")

num_messages, words, num_media, num_links = helper.fetch_stats(selected_user, df)

c1, c2, c3, c4 = st.columns(4)
c1.markdown(metric_card("Total Messages", num_messages, accent=True), unsafe_allow_html=True)
c2.markdown(metric_card("Total Words", words), unsafe_allow_html=True)
c3.markdown(metric_card("Media Shared", num_media), unsafe_allow_html=True)
c4.markdown(metric_card("Links Shared", num_links), unsafe_allow_html=True)

st.write("")

# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
tab_labels = ["📈 Timelines", "🔥 Activity", "💬 Words", "😀 Emojis"]
if selected_user == "Overall":
    tab_labels.insert(1, "👥 Members")
tabs = st.tabs(tab_labels)
tab_map = dict(zip(tab_labels, tabs))

# ---- Timelines ----
with tab_map["📈 Timelines"]:
    st.subheader("Monthly Timeline")
    timeline = helper.monthly_timeline(selected_user, df)
    fig = px.area(timeline, x="time", y="message", labels={"time": "", "message": "Messages"})
    fig.update_traces(line_color=ACCENT, fillcolor="rgba(37,211,102,0.15)")
    st.plotly_chart(style_fig(fig), use_container_width=True)

    st.subheader("Daily Timeline")
    daily = helper.daily_timeline(selected_user, df)
    fig = px.line(daily, x="only_date", y="message", labels={"only_date": "", "message": "Messages"})
    fig.update_traces(line_color="#53BDEB")
    st.plotly_chart(style_fig(fig), use_container_width=True)

# ---- Members (Overall only) ----
if selected_user == "Overall":
    with tab_map["👥 Members"]:
        st.subheader("Most Active Members")
        x, new_df = helper.most_busy_users(df)
        col1, col2 = st.columns([3, 2])
        with col1:
            fig = px.bar(
                x=x.index, y=x.values,
                labels={"x": "", "y": "Messages"},
                color=x.index,
                color_discrete_sequence=CHART_COLORS,
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(style_fig(fig), use_container_width=True)
        with col2:
            new_df.columns = ["Member", "Share (%)"]
            st.dataframe(new_df, use_container_width=True, hide_index=True, height=380)

# ---- Activity ----
with tab_map["🔥 Activity"]:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Busiest Day")
        busy_day = helper.week_activity_map(selected_user, df)
        fig = px.bar(x=busy_day.index, y=busy_day.values, labels={"x": "", "y": "Messages"})
        fig.update_traces(marker_color=ACCENT)
        st.plotly_chart(style_fig(fig, 320), use_container_width=True)
    with col2:
        st.subheader("Busiest Month")
        busy_month = helper.month_activity_map(selected_user, df)
        fig = px.bar(x=busy_month.index, y=busy_month.values, labels={"x": "", "y": "Messages"})
        fig.update_traces(marker_color="#53BDEB")
        st.plotly_chart(style_fig(fig, 320), use_container_width=True)

    st.subheader("Weekly Activity Heatmap")
    heatmap = helper.activity_heatmap(selected_user, df)
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heatmap = heatmap.reindex([d for d in day_order if d in heatmap.index])
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap.values,
            x=heatmap.columns.tolist(),
            y=heatmap.index.tolist(),
            colorscale=[[0, CARD_BG], [1, ACCENT]],
            hovertemplate="%{y}, %{x}h<br>%{z} messages<extra></extra>",
        )
    )
    st.plotly_chart(style_fig(fig, 420), use_container_width=True)

# ---- Words ----
with tab_map["💬 Words"]:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Word Cloud")
        try:
            df_wc = helper.create_wordcloud(selected_user, df)
            fig, ax = plt.subplots(figsize=(6, 6))
            fig.patch.set_facecolor(BG)
            ax.imshow(df_wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig, use_container_width=True)
        except Exception:
            st.info("Not enough text to build a word cloud.")
    with col2:
        st.subheader("Most Common Words")
        most_common_df = helper.most_common_words(selected_user, df)
        if len(most_common_df) > 0:
            most_common_df.columns = ["word", "count"]
            fig = px.bar(
                most_common_df.sort_values("count"),
                x="count", y="word", orientation="h",
                labels={"count": "Occurrences", "word": ""},
            )
            fig.update_traces(marker_color=ACCENT)
            st.plotly_chart(style_fig(fig, 520), use_container_width=True)
        else:
            st.info("No common words found.")

# ---- Emojis ----
with tab_map["😀 Emojis"]:
    emoji_df = helper.emoji_helper(selected_user, df)
    if len(emoji_df) == 0:
        st.info("No emojis were shared in this chat.")
    else:
        emoji_df.columns = ["emoji", "count"]
        col1, col2 = st.columns([2, 3])
        with col1:
            st.subheader("All Emojis")
            st.dataframe(emoji_df, use_container_width=True, hide_index=True, height=420)
        with col2:
            st.subheader("Top Emojis")
            top = emoji_df.head(8)
            fig = px.pie(
                top, values="count", names="emoji", hole=0.55,
                color_discrete_sequence=CHART_COLORS,
            )
            fig.update_traces(textinfo="label+percent", textfont_size=16)
            st.plotly_chart(style_fig(fig, 420), use_container_width=True)
