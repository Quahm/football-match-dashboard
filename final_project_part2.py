import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch, VerticalPitch, Sbopen

# ============================================================================
# PAGE CONFIG - must be the very first Streamlit command
# ============================================================================
st.set_page_config(
    page_title="Football Match Analysis Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# STYLE - matches mentorship website exactly
# ============================================================================
st.markdown("""
<style>
.stApp {
    background-color: #0d0d0d;
    color: #ffffff;
}
[data-testid="stSidebar"] {
    background-color: #111111;
    border-right: 1px solid #7C3AED;
}
[data-testid="stSidebar"] * {
    color: #ffffff !important;
}
h1 {
    color: #ffffff !important;
}
h2, h3 {
    color: #7C3AED !important;
}
.stButton > button {
    background-color: #7C3AED;
    color: white;
    border: none;
    border-radius: 8px;
}
.stButton > button:hover {
    background-color: #6d28d9;
}
</style>
""", unsafe_allow_html=True)
# ============================================================================
# MAIN HEADER
# ============================================================================
st.title("Football Match Analysis Dashboard")
st.caption("Powered by StatsBomb Open Data  ·  Football Data Analysis Mentorship – Cohort 1")
st.divider()
# ============================================================================
# STYLE CONSTANTS - use these for all your visualizations
# ============================================================================
BG_COLOR    = '#0d0d0d'   # Figure & pitch background
LINE_COLOR  = '#FFFFFF'   # Pitch lines
MAIN_COLOR  = '#7C3AED'   # Violet - primary color
ACCENT_COLOR = '#A78BFA'  # Light violet - secondary
TEXT_COLOR  = '#FFFFFF'   # All text on figures
GRAY_COLOR  = '#A0A0A0'   # Secondary text

# Apply matplotlib global style
plt.rcParams['figure.facecolor'] = BG_COLOR
plt.rcParams['axes.facecolor']   = BG_COLOR
plt.rcParams['text.color']       = TEXT_COLOR

# ============================================================================
# DATA LOADING - cached for performance
# ============================================================================
parser = Sbopen()

@st.cache_data
def load_matches(competition_id, season_id):
    matches = parser.match(competition_id=competition_id, season_id=season_id)
    matches['label'] = (
        matches['home_team_name'] + ' vs ' +
        matches['away_team_name'] + ' (' +
        matches['match_date'].astype(str) + ')'
    )
    return matches

@st.cache_data
def load_events(match_id):
    return parser.event(match_id=match_id)[0]
def plot_shot_map(events, team_name):
    shots = events[(events['type_name'] == 'Shot') & (events['team_name'] == team_name)].copy()

    pitch = Pitch(pitch_color=BG_COLOR, line_color=LINE_COLOR, stripe=False)
    fig, ax = pitch.draw(figsize=(12, 8))

    for _, shot in shots.iterrows():
        color = '#00FF00' if shot.get('outcome_name') == 'Goal' else MAIN_COLOR
        pitch.scatter(shot['x'], shot['y'], ax=ax, s=100, color=color, edgecolors='white', linewidth=1, zorder=2)

    ax.set_title(f"{team_name} - Shot Map", color=TEXT_COLOR, fontsize=16, pad=10)
    return fig
def plot_passing_network(events, team_name):
    # Filter successful passes for the selected team
    passes = events[
        (events['type_name'] == 'Pass') & 
        (events['team_name'] == team_name) & 
        (events['outcome_name'].isna())
    ].copy()

    # Get average locations of players
    average_locs = passes.groupby('player_name').agg({
        'x': 'mean',
        'y': 'mean',
        'id': 'count'
    }).reset_index()
    average_locs = average_locs.rename(columns={'id': 'pass_count'})

    # Create pass connections
    passes['receiver'] = passes['pass_recipient_name']
    pass_links = passes.groupby(['player_name', 'receiver']).size().reset_index(name='count')
    pass_links = pass_links[pass_links['count'] > 2]

    # Draw pitch
    pitch = Pitch(pitch_color=BG_COLOR, line_color=LINE_COLOR, stripe=False)
    fig, ax = pitch.draw(figsize=(12, 8))

    # Draw pass lines
    for _, link in pass_links.iterrows():
        start = average_locs[average_locs['player_name'] == link['player_name']]
        end = average_locs[average_locs['player_name'] == link['receiver']]
        if not start.empty and not end.empty:
            ax.plot(
                [start['x'].values[0], end['x'].values[0]],
                [start['y'].values[0], end['y'].values[0]],
                color=MAIN_COLOR, alpha=0.4, linewidth=link['count']*0.3, zorder=1
            )

    # Draw player nodes
    pitch.scatter(
        average_locs['x'], average_locs['y'],
        s=average_locs['pass_count']*20,
        color=MAIN_COLOR, edgecolors='white', linewidth=1.5, ax=ax, zorder=2
    )

    # Add player names
    for _, row in average_locs.iterrows():
        ax.text(row['x'], row['y']+2, row['player_name'].split()[-1], 
                color=TEXT_COLOR, fontsize=8, ha='center', va='bottom')

    ax.set_title(f"{team_name} - Passing Network", color=TEXT_COLOR, fontsize=16, pad=10)
    return fig

def plot_pressure_heatmap(events, team_name):
    pressures = events[
        (events['type_name'] == 'Pressure') & 
        (events['team_name'] == team_name)
    ].copy()

    pitch = Pitch(pitch_color=BG_COLOR, line_color=LINE_COLOR, stripe=False)
    fig, ax = pitch.draw(figsize=(12, 8))

    pitch.kdeplot(
        pressures['x'], pressures['y'],
        ax=ax,
        fill=True,
        levels=100,
        thresh=0.05,
        cut=4,
        cmap='magma'
    )

    ax.set_title(f"{team_name} - Pressure Heatmap", color=TEXT_COLOR, fontsize=16, pad=10)
    return fig
def plot_player_heatmap(events, team_name):
    # Get all events for the selected team (or you can filter by a specific player later)
    team_events = events[events['team_name'] == team_name].copy()

    pitch = Pitch(pitch_color=BG_COLOR, line_color=LINE_COLOR, stripe=False)
    fig, ax = pitch.draw(figsize=(12, 8))

    pitch.kdeplot(
        team_events['x'], team_events['y'],
        ax=ax,
        fill=True,
        levels=100,
        thresh=0.05,
        cut=4,
        cmap='coolwarm'
    )

    ax.set_title(f"{team_name} - Player Heatmap", color=TEXT_COLOR, fontsize=16, pad=10)
    return fig
# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.markdown("## Filters")
    st.divider()

    # Load matches
    matches = load_matches(competition_id=1267, season_id=107)

    match_label = st.selectbox("Select a Match", matches['label'])
    match_id = matches[matches['label'] == match_label]['match_id'].values[0]

    events = load_events(match_id)
    teams = sorted(events['team_name'].dropna().unique())
    selected_team = st.selectbox("Select a Team", teams)

    plot_type = st.radio("Visualization", [
        "Passing Network",
        "Shot Map",
        "Pressure Heatmap",
        "Player Heatmap"
    ])

    st.divider()
    st.caption("Football Data Analysis Mentorship")
    st.caption("Cohort 1 – Sara Bentelli")
# ============================================================================
# METRICS ROW
# ============================================================================
team_events = events[events['team_name'] == selected_team]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Passes", len(team_events[team_events['type_name'] == 'Pass']))
col2.metric("Total Shots", len(team_events[team_events['type_name'] == 'Shot']))
col3.metric("Pressures", len(team_events[team_events['type_name'] == 'Pressure']))
col4.metric("Carries", len(team_events[team_events['type_name'] == 'Carry']))

st.divider()
# ============================================================================
# MAIN CONTENT
# ============================================================================
st.subheader(f"{selected_team}")
st.caption(f"Match ID: {match_id} | Visualization: {plot_type}")

# Simple metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Events", len(events))
with col2:
    st.metric("Passes", len(events[events['type_name'] == 'Pass']))
with col3:
    st.metric("Shots", len(events[events['type_name'] == 'Shot']))

st.markdown("---")
# ============================================================================
# VISUALIZATION
# ============================================================================
if plot_type == "Shot Map":
    fig = plot_shot_map(events, selected_team)
    st.pyplot(fig)

elif plot_type == "Passing Network":
    fig = plot_passing_network(events, selected_team)
    st.pyplot(fig)

elif plot_type == "Pressure Heatmap":
    fig = plot_pressure_heatmap(events, selected_team)
    st.pyplot(fig)

elif plot_type == "Player Heatmap":
    fig = plot_player_heatmap(events, selected_team)
    st.pyplot(fig)
    # ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.caption("Football Data Analysis Mentorship – Cohort 1  ·  Sara Bentelli  ·  2026")