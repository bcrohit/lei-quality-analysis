import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards

from utils.data_quality_checks import run_quality_checks
from utils.scoring import calculate_quality_score
from utils.utils import (check_for_timestamp, fetch_data_from_db,
                         format_dataframe, get_display_name, iso2_to_iso3)

st.set_page_config(
    page_title="LEI Data Quality Analyzer",
    layout="wide",
    page_icon="🔍"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main color theme */
    :root {
        --primary: #2c3e50;
        --secondary: #3498db;
        --success: #27ae60;
        --warning: #f39c12;
        --danger: #e74c3c;
    }
            
    .stApp {
        background-color: #f8f9fa;
    }
    
    .stButton>button {
        border-radius: 20px;
        border: 1px solid var(--primary);
        color: var(--primary);
        background: white;
    }
    
    .stButton>button:hover {
        background-color: #f0f2f6;
    }
    
    .header-section {
        background: linear-gradient(120deg, #2c3e50, #4a6491);
        padding: 1.5rem;
        border-radius: 0 0 10px 10px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .card {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        background: white;
    }
    
    .section-title {
        color: var(--primary);
        border-bottom: 2px solid var(--secondary);
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .lei-table tr:hover {
        background-color: #f5f5f5 !important;
    }
    
    .pagination-container {
        display: flex;
        justify-content: center;
        margin-top: 1rem;
    }
    
    .tab-container {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header section
st.markdown('<div class="header-section">', unsafe_allow_html=True)
st.title("🔍 LEI Data Quality Analyzer")
st.markdown("Analyze LEI data quality from uploaded files or database connections")
st.markdown('</div>', unsafe_allow_html=True)

# Data source selection
st.subheader("📂 Data Source")
source_option = st.radio("Select data source:", 
                         ("Upload CSV", "Fetch from Database"),
                         horizontal=True)

df = None

if source_option == "Upload CSV":
    uploaded_file = st.file_uploader("Upload LEI CSV File", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
elif source_option == "Fetch from Database":
    # if st.button("Fetch Data", type="primary"):
    with st.spinner("Fetching data from database..."):
        df = fetch_data_from_db()
        df = check_for_timestamp(df)

if df is not None:
    with st.spinner("Analyzing data quality..."):
        df = run_quality_checks(df)
        df = calculate_quality_score(df)
        df = format_dataframe(df)
        
        # Store in session state
        st.session_state.df = df
        st.session_state.score_counts = df["QualityLabel"].value_counts().reindex(
            ["Good", "Moderate", "Poor"], fill_value=0
        )
        
        # Additional metrics for new visualizations
        st.session_state.avg_score = df["QualityScore"].mean()
        st.session_state.median_score = df["QualityScore"].median()
        st.session_state.min_score = df["QualityScore"].min()
        st.session_state.max_score = df["QualityScore"].max()
    
    # ====================== Enhanced Visualization Section ======================
    st.subheader("📊 Data Quality Metrics")
    
    # Top level metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Average Score", f"{st.session_state.avg_score:.1f}")
    with col2:
        st.metric("Median Score", f"{st.session_state.median_score:.1f}")
    with col3:
        st.metric("Min Score", st.session_state.min_score)
    with col4:
        st.metric("Max Score", st.session_state.max_score)
    style_metric_cards()
    
    # Quality distribution cards
    st.subheader("📈 Quality Distribution")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Good", st.session_state.score_counts["Good"], 
                 help="Records with 80-100% quality score")
    with col2:
        st.metric("Moderate", st.session_state.score_counts["Moderate"], 
                 help="Records with 50-79% quality score")
    with col3:
        st.metric("Poor", st.session_state.score_counts["Poor"], 
                 help="Records with 0-49% quality score")
    
    # Apply custom styling to metric cards
    style_metric_cards(background_color="#FFFFFF", border_left_color="#2c3e50")
    
    # Visualization tabs
    tab1, tab2, tab3 = st.tabs(["Geospatial", "Distribution", "Score Analysis"])
 
    with tab1:  # Geospatial tab (if location data exists)
        country = 'Legal Address → Country'
        if country in df.columns:
            st.subheader("Geospatial Analysis")
            
            country_counts = df[country].value_counts().reset_index()
            country_counts.columns = [country, 'Count']
            
            # Country quality scores
            country_quality = df.groupby(country)['QualityScore'].mean().reset_index()
            country_data = country_counts.merge(country_quality, on=country)
            country_data.rename(columns = {country: 'country'}, inplace=True)
            country_data["Country"] = country_data["country"].apply(iso2_to_iso3)
            
            fig = px.choropleth(
                country_data,
                locations='Country',
                locationmode="ISO-3",
                color="QualityScore",
                hover_name='country',
                hover_data=["Count"],
                color_continuous_scale="RdYlGn",
                range_color=[0, 100],
                title="Average QualityScore by Country"
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("No geographic data available for mapping.")
    
    with tab2:  # Distribution tab
        col1, col2 = st.columns(2)
        with col1:
            # Bar chart
            fig = px.bar(
                st.session_state.score_counts, 
                x=st.session_state.score_counts.index,
                y=st.session_state.score_counts.values,
                color=st.session_state.score_counts.index,
                color_discrete_map={
                    "Good": "#27ae60", 
                    "Moderate": "#f39c12", 
                    "Poor": "#e74c3c"
                },
                labels={'x': 'Quality Level', 'y': 'Count'},
                height=400,
                title="Quality Level Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Pie chart
            fig = px.pie(
                st.session_state.score_counts, 
                values=st.session_state.score_counts.values,
                names=st.session_state.score_counts.index,
                color=st.session_state.score_counts.index,
                color_discrete_map={
                    "Good": "#27ae60", 
                    "Moderate": "#f39c12", 
                    "Poor": "#e74c3c"
                },
                hole=0.4,
                height=500,
                title="Quality Level Proportion"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:  # Score Analysis tab
        col1, col2 = st.columns(2)
        with col1:
            # Histogram
            fig = px.histogram(
                st.session_state.df, 
                x="QualityScore",
                nbins=20,
                color_discrete_sequence=["#3498db"],
                height=400,
                title="QualityScore Distribution"
            )
            fig.update_layout(
                xaxis_title="QualityScore",
                yaxis_title="Count",
                bargap=0.1
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            # Box plot
            fig = px.box(
                st.session_state.df, 
                y="QualityScore",
                points="all",
                height=400,
                title="QualityScore Spread",
                color_discrete_sequence=["#3498db"]
            )
            fig.update_layout(
                yaxis_title="QualityScore",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Trend line (if time-based data exists)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                time_df = df.set_index('timestamp').resample('D')['QualityScore'].mean().reset_index()
                fig = px.line(
                    time_df, 
                    x='timestamp', 
                    y='QualityScore',
                    title="QualityScore Trend Over Time",
                    markers=True
                )
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Average QualityScore"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # ====================== Data Explorer Section ======================
    st.subheader("🔍 Data Explorer")
    
    # Create summary table
    summary_df = df[["LEI", "QualityScore", "QualityLabel"]].copy()
    
    # Add row numbers
    summary_df.insert(0, "#", range(1, len(summary_df) + 1))
    
    # Pagination settings
    page_size = st.slider("Rows per page", 5, 50, 10)
    total_pages = (len(summary_df) - 1) // page_size + 1
    
    if "page" not in st.session_state:
        st.session_state.page = 0
    
    # Navigation
    col1, col2, col3, col4 = st.columns([2, 2, 4, 2])
    with col1:
        if st.button("◀ Previous", disabled=st.session_state.page == 0):
            st.session_state.page = max(0, st.session_state.page - 1)
    with col2:
        if st.button("Next ▶", disabled=st.session_state.page >= total_pages - 1):
            st.session_state.page = min(total_pages - 1, st.session_state.page + 1)
    with col4:
        st.caption(f"Page {st.session_state.page + 1} of {total_pages}")
    
    # Paginate data
    start_idx = st.session_state.page * page_size
    end_idx = start_idx + page_size
    paginated_df = summary_df.iloc[start_idx:end_idx]
    paginated_df['LEI'] = paginated_df['LEI'].astype('string')
    # Debug code line
    # paginated_df.astype('string')
    
    # Display table with custom styling
    st.dataframe(
        paginated_df,
        height=(min(len(paginated_df), 10) * 35) + 35,
        use_container_width=True
    )

    
    # Download button
    st.download_button(
        label="📥 Download Report",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='lei_quality_report.csv',
        mime='text/csv'
    )
    
    # Drill-down details
    st.subheader("🔬 Record Details")
    df['Display Name'] = df.apply(get_display_name, axis=1)

    # Streamlit selectbox with search
    selected_lei = st.selectbox(
        "🔍 Search or Select LEI Record", 
        options=df['Display Name'].tolist(),
        index=0,
        key="select_lei"
    )

    if selected_lei:
        record_details = df[df['Display Name'] == selected_lei]
        record_details = (record_details.dropna(axis=1, how='all')).T
        record_details.columns = ["Value"]
        
        # Display as a table with key-value pairs
        st.table(record_details)


else:
    # Show empty state with instructions
    st.markdown("""
    <div class="card">
        <h3>Get Started</h3>
        <p>Choose a data source to begin the data quality analysis:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Example chart placeholder
    st.subheader("Example Report Preview")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="color: #2c3e50; margin-top: 0;">Quality Distribution</h4>
            <img src="https://discovery.cs.illinois.edu/static/learn/NC-WebG.png" style="width:100%; border-radius: 8px;">
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h4 style="color: #2c3e50; margin-top: 0;">Data Sample</h4>
            <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 8px; border: 1px solid #ddd;">LEI</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Score</th>
                    <th style="padding: 8px; border: 1px solid #ddd;">Status</th>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">1234567890</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">92</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #27ae60;">Good</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">0987654321</td>
                    <td style="padding: 8px; border: 1px solid #ddd;">65</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #f39c12;">Moderate</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)