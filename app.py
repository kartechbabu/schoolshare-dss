"""
SchoolShare Decision Support System v2
Main Streamlit Application with Enhanced Map Visualization
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add src to path for imports
sys.path.append('src')
from utils.csv_data_loader import (
    load_optimization_results,
    calculate_metrics_from_csv,
    get_available_states,
    load_coverage_data,
    load_facility_school_pairings
)
from utils.choropleth_map import (
    create_choropleth_map,
    create_simple_markers_map,
    load_school_data,
    load_arts_facilities,
    load_hospital_data
)

# Page configuration
st.set_page_config(
    page_title="SchoolShare DSS v2",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for analysis
if 'analysis_run' not in st.session_state:
    st.session_state.analysis_run = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = None
if 'last_state' not in st.session_state:
    st.session_state.last_state = None
if 'last_service' not in st.session_state:
    st.session_state.last_service = None
if 'last_activation' not in st.session_state:
    st.session_state.last_activation = None

# Title and description
st.title("🏫 School Infrastructure Sharing Decision Support System")
st.markdown("""
Explore how activating schools as shared service locations can reduce spatial inequality
in access to arts facilities and hospitals.
""")

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")

    # Service type selection first (to determine available states)
    service = st.radio(
        "Service Type",
        options=["Arts Facilities", "Hospitals"],
        help="Select which service type to analyze"
    )

    # Get available states for selected service
    available_states = get_available_states(service)

    # State selection
    state = st.selectbox(
        "Select State",
        options=available_states,
        index=available_states.index("Texas") if "Texas" in available_states else 0,
        help="Choose a state to analyze"
    )

    # Activation rate
    activation = st.slider(
        "School Activation Rate (%)",
        min_value=0,
        max_value=50,
        value=25,
        step=5,
        help="Percentage of high schools to activate as shared service locations"
    )

    # Load data preview to show actual numbers
    with st.spinner("Loading state data..."):
        preview_data = load_optimization_results(state, service)
        if preview_data and 'metadata' in preview_data:
            total_schools = preview_data['metadata'].get('n_schools', 1000)
            total_facilities = preview_data['metadata'].get('n_facilities', 500)

            # Calculate actual schools to activate (constrained by facilities)
            max_schools = min(int(total_schools * 0.5), total_facilities)
            activated_schools = min(int(total_schools * activation / 100), max_schools)

            st.info(f"""
            **State Statistics:**
            - Total high schools: {total_schools:,}
            - Total {service.lower()}: {total_facilities:,}
            - Schools to activate: {activated_schools:,}
            """)
        else:
            activated_schools = int(1000 * activation / 100)
            st.info(f"Estimated schools activated: {activated_schools:,}")

    # Run analysis button
    run_analysis = st.button("Run Analysis", type="primary", use_container_width=True)

# Check if parameters changed - reset analysis if so
params_changed = (
    st.session_state.last_state != state or
    st.session_state.last_service != service or
    st.session_state.last_activation != activation
)

# Main content area - run new analysis or show existing
if run_analysis or (st.session_state.analysis_run and not params_changed):
    # Only reload data if button clicked or params changed
    if run_analysis or st.session_state.results is None:
        with st.spinner("Analyzing impact..."):
            # Load actual optimization results
            results = load_optimization_results(state, service)
            metrics = None

            if results and 'optimized' in results:
                metrics = calculate_metrics_from_csv(results, activation)

            # Store in session state
            st.session_state.results = results
            st.session_state.metrics = metrics
            st.session_state.analysis_run = True
            st.session_state.last_state = state
            st.session_state.last_service = service
            st.session_state.last_activation = activation
    else:
        # Use cached results
        results = st.session_state.results
        metrics = st.session_state.metrics

    # ============================================
    # MAP VISUALIZATION (FIRST - main feature)
    # ============================================
    st.markdown("### Geographic Impact")

    # Get activated schools list
    if results and activation in results['optimized']:
        optimized_data = results['optimized'][activation]
        activated_schools_list = optimized_data.get('activated_schools', [])

        if activated_schools_list:
            # Map controls
            map_controls = st.columns([2, 2, 2, 1])

            with map_controls[0]:
                # Choropleth view toggle
                view_type = st.radio(
                    "Map View",
                    options=["Distance (km)", "% Improvement", "Coverage Status"],
                    horizontal=True,
                    help="Choose how to visualize coverage improvements"
                )

            with map_controls[1]:
                show_facilities = st.checkbox("Show Existing Facilities", value=True)

            with map_controls[2]:
                show_schools = st.checkbox("Show Activated Schools", value=True)

            with map_controls[3]:
                use_simple_map = st.checkbox("Fast Mode", value=False,
                                             help="Use simpler map for faster loading")

            # Display map info with legend based on view type
            if view_type == "Coverage Status":
                legend_text = """
                **Map Legend:**
                - 🟢 Green areas: Newly covered (within 10km after optimization)
                - 🟡 Yellow areas: Already covered (within 10km before)
                - 🔴 Red areas: Not covered (>10km even after optimization)
                """
            else:
                legend_text = f"""
                **Map Legend:**
                - Colored areas: CBGs with distance improvement
                - Gray areas: CBGs with no change (already well-served)
                """

            st.info(f"""
            {legend_text}
            - 🟢 Green markers: Activated schools ({len(activated_schools_list)} total)
            - {'🟣 Purple markers: Arts facilities' if 'arts' in service.lower() else '🔵 Blue markers: Hospitals'}
            """)

            # Create and display map
            with st.spinner(f"Loading map with {len(activated_schools_list)} school locations..."):
                try:
                    if use_simple_map:
                        # Fast loading: just markers, no choropleth
                        the_map = create_simple_markers_map(
                            state=state,
                            service=service,
                            activated_schools=activated_schools_list,
                            show_facilities=show_facilities
                        )
                    else:
                        # Full choropleth map
                        the_map = create_choropleth_map(
                            state=state,
                            service=service,
                            activation_rate=activation,
                            activated_schools=activated_schools_list,
                            view_type=view_type,
                            show_facilities=show_facilities,
                            show_schools=show_schools
                        )

                    if the_map:
                        # Render map as HTML component (larger height for better visibility)
                        map_html = the_map._repr_html_()
                        components.html(map_html, height=700, scrolling=True)
                    else:
                        st.warning("Could not create map. Using fallback visualization.")
                        # Fallback: show school counts by region
                        st.write(f"Activated {len(activated_schools_list)} schools in {state}")

                except Exception as e:
                    st.error(f"Error creating map: {e}")
                    st.write(f"Activated {len(activated_schools_list)} schools in {state}")

        else:
            st.warning("No activated schools data available for this scenario.")
    else:
        st.info("Run the analysis to see the geographic distribution.")

    # ============================================
    # COMPACT METRICS QUADRANT (after map)
    # ============================================
    if metrics:
        st.markdown("---")
        st.markdown("### Impact Summary")

        # Create 2x2 grid: left quadrants for metrics, right quadrants for charts
        top_left, top_right = st.columns([1, 1])
        bottom_left, bottom_right = st.columns([1, 1])

        # TOP LEFT: Key metrics (compact)
        with top_left:
            st.markdown("##### Key Metrics")
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Distance Reduction", f"{metrics['distance_reduction']:.1f}%", f"-{metrics['km_saved']:.1f} km")
                st.metric("Population Helped", f"{metrics['pop_helped']/1e6:.1f}M", f"{metrics['pop_helped_pct']:.1f}% CBGs")
            with m2:
                if service == "Hospitals":
                    st.metric("Lives Saved/Year", f"{metrics.get('lives_saved', 0):,}")
                else:
                    st.metric("New Access <10km", f"{metrics.get('new_access_10km', 0)/1e3:.0f}K")
                cost_per_person = 327 if service == "Hospitals" else 61
                st.metric("Cost/Beneficiary", f"${cost_per_person}", f"BCR: {3.67 if service == 'Hospitals' else 2.54}")

        # TOP RIGHT: Distance bar chart
        with top_right:
            baseline_dist = metrics['mean_baseline_distance']
            optimized_dist = metrics['mean_optimized_distance']
            distance_data = pd.DataFrame({
                'Scenario': ['Baseline', 'Optimized'],
                'Distance (km)': [baseline_dist, optimized_dist]
            })
            fig_dist = px.bar(
                distance_data, x='Scenario', y='Distance (km)',
                title=f'Avg Distance: {baseline_dist:.1f} → {optimized_dist:.1f} km',
                color='Scenario',
                color_discrete_map={'Baseline': '#ff7f0e', 'Optimized': '#2ca02c'}
            )
            fig_dist.update_layout(height=200, showlegend=False, margin=dict(t=30, b=20, l=20, r=20))
            st.plotly_chart(fig_dist, use_container_width=True)

        # BOTTOM LEFT: Demographics (compact)
        with bottom_left:
            st.markdown("##### Demographics Served")
            d1, d2 = st.columns(2)
            with d1:
                nonwhite_pct = metrics.get('nonwhite_pct_served', 0) * 100
                st.metric("Non-white", f"{nonwhite_pct:.1f}%")
            with d2:
                nonbach_pct = metrics.get('nonbach_pct_served', 0) * 100
                st.metric("No Bachelor's", f"{nonbach_pct:.1f}%")

        # BOTTOM RIGHT: Coverage bar chart
        with bottom_right:
            baseline_cov = metrics.get('baseline_coverage_pct', 50)
            optimized_cov = metrics.get('optimized_coverage_pct', 75)
            coverage_data = pd.DataFrame({
                'Scenario': ['Baseline', 'Optimized'],
                'Coverage (%)': [baseline_cov, optimized_cov]
            })
            fig_cov = px.bar(
                coverage_data, x='Scenario', y='Coverage (%)',
                title=f'Coverage: {baseline_cov:.0f}% → {optimized_cov:.0f}%',
                color='Scenario',
                color_discrete_map={'Baseline': '#ff7f0e', 'Optimized': '#2ca02c'}
            )
            fig_cov.update_layout(height=200, showlegend=False, margin=dict(t=30, b=20, l=20, r=20))
            st.plotly_chart(fig_cov, use_container_width=True)

    # ============================================
    # TABS (Secondary Information)
    # ============================================
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Coverage Details", "🔗 Facility Pairings", "💰 Implementation", "🏫 School List"])

    with tab1:
        st.subheader("Detailed Coverage Analysis")

        if results and metrics:
            # Regional breakdown (if available)
            coverage_df = load_coverage_data(state, service, activation)

            if coverage_df is not None:
                # Summary statistics
                st.markdown("##### Coverage Statistics by CBG")

                # Calculate distance reduction if not present
                if 'distance_reduction_km' not in coverage_df.columns:
                    coverage_df['distance_reduction_km'] = (coverage_df['mindist_current'] - coverage_df['mindist_sol']) / 1000

                stats_col1, stats_col2, stats_col3 = st.columns(3)
                with stats_col1:
                    st.metric("CBGs with Improvement",
                              f"{(coverage_df['distance_reduction_km'] > 0).sum():,}",
                              f"of {len(coverage_df):,} total")
                with stats_col2:
                    avg_reduction = coverage_df['distance_reduction_km'].mean()
                    st.metric("Avg Distance Reduction", f"{avg_reduction:.2f} km")
                with stats_col3:
                    # Calculate newly covered (within 10km after but not before)
                    newly_covered = ((coverage_df['mindist_sol'] <= 10000) & (coverage_df['mindist_current'] > 10000)).sum()
                    st.metric("Newly Covered CBGs", f"{newly_covered:,}")

                # Distribution chart
                positive_reductions = coverage_df[coverage_df['distance_reduction_km'] > 0]
                if len(positive_reductions) > 0:
                    fig_hist = px.histogram(
                        positive_reductions,
                        x='distance_reduction_km',
                        nbins=50,
                        title="Distribution of Distance Reductions",
                        labels={'distance_reduction_km': 'Distance Reduction (km)', 'count': 'Number of CBGs'}
                    )
                    fig_hist.update_layout(height=300)
                    st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.info("Detailed coverage data not available for this state/activation rate.")

            # Note about equity
            st.info("""
            **Note**: The optimization prioritizes underserved areas, resulting in progressive benefits.
            Communities with poor baseline access see larger improvements than those already well-served.
            """)
        else:
            st.info("Run the analysis to see coverage details.")

    with tab2:
        st.subheader("Facility-School Pairings")
        
        if results and activation in results['optimized']:
            optimized_data = results['optimized'][activation]
            pairings = optimized_data.get('facility_school_pairings', [])
            
            if pairings:
                st.success(f"**{len(pairings)} facility-school pairings** in this optimization scenario")
                
                # Load facility and school data for name lookups
                school_gdf = load_school_data(state)
                if 'arts' in service.lower():
                    facility_df = load_arts_facilities(state)
                else:
                    facility_df = load_hospital_data(state)
                
                # Build pairing table
                pairing_data = []
                for facility_id, school_id in pairings:
                    row = {
                        'Facility ID': str(facility_id),
                        'Facility Name': '',
                        'School ID': str(school_id),
                        'School Name': ''
                    }
                    
                    # Look up facility name
                    if facility_df is not None:
                        if 'arts' in service.lower():
                            # OrgMap uses NCARID
                            if 'NCARID' in facility_df.columns:
                                match = facility_df[facility_df['NCARID'] == facility_id]
                                if len(match) > 0:
                                    row['Facility Name'] = match.iloc[0].get('name', match.iloc[0].get('OrgName', ''))
                            elif hasattr(facility_df, 'index'):
                                try:
                                    if facility_id in facility_df.index:
                                        row['Facility Name'] = facility_df.loc[facility_id].get('name', facility_df.loc[facility_id].get('OrgName', ''))
                                except:
                                    pass
                        else:
                            # Hospitals
                            if hasattr(facility_df, 'index'):
                                try:
                                    if facility_id in facility_df.index:
                                        row['Facility Name'] = facility_df.loc[facility_id].get('NAME', '')
                                except:
                                    pass
                    
                    # Look up school name
                    if school_gdf is not None:
                        school_id_str = str(school_id)
                        if school_id_str in school_gdf.index.astype(str).values:
                            try:
                                school_row = school_gdf.loc[school_gdf.index.astype(str) == school_id_str].iloc[0]
                                row['School Name'] = school_row.get('School Name', school_row.get('NAME', ''))
                            except:
                                pass
                    
                    pairing_data.append(row)
                
                pairing_df = pd.DataFrame(pairing_data)
                
                # Display table
                st.dataframe(
                    pairing_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Facility ID': st.column_config.TextColumn('Facility ID', width='small'),
                        'Facility Name': st.column_config.TextColumn('Facility Name', width='medium'),
                        'School ID': st.column_config.TextColumn('School ID (NCESSCH)', width='small'),
                        'School Name': st.column_config.TextColumn('Paired School', width='medium'),
                    }
                )
                
                # Download button
                csv = pairing_df.to_csv(index=False)
                st.download_button(
                    label="Download Pairings (CSV)",
                    data=csv,
                    file_name=f"{state.lower()}_{service.lower().replace(' ', '_')}_pairings_{activation}pct.csv",
                    mime="text/csv"
                )
                
                st.info("""
                **How to interpret**: Each row shows which existing facility is paired with an activated school.
                The optimization assigns each facility to the school that best serves its coverage area.
                """)
            else:
                st.warning("No facility-school pairing data available for this scenario.")
                st.info("Pairing data shows which existing facilities are assigned to activated schools in the optimization.")
        else:
            st.info("Run the analysis to see facility-school pairings.")

    with tab3:
        st.subheader("Implementation Resources")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### Estimated Costs")

            if results and metrics:
                n_schools = metrics.get('n_schools_activated', activated_schools)

                # Cost calculator
                startup_cost = n_schools * 50000
                annual_cost = n_schools * 30000

                st.metric("Total Startup Cost", f"${startup_cost/1e6:.1f}M")
                st.metric("Annual Operating Cost", f"${annual_cost/1e6:.1f}M")

                if metrics.get('pop_helped', 0) > 0:
                    cost_per_person = startup_cost / metrics['pop_helped']
                    st.metric("Cost per Person Helped", f"${cost_per_person:.0f}")

            st.markdown("##### Funding Sources")
            st.markdown("""
            - **Federal**: Renew America's Schools ($500M)
            - **Federal**: SASI Infrastructure Grants
            - **Federal**: IRA Tax Credits (30% back)
            - **State**: Community Schools Funding
            - **Local**: Facility Rental Revenue
            """)

        with col2:
            st.markdown("##### Implementation Checklist")

            tasks = [
                "Identify pilot schools",
                "Engage community partners",
                "Apply for federal grants",
                "Set up facility rental platform",
                "Establish insurance pool",
                "Create operational protocols",
                "Launch pilot program",
                "Monitor and evaluate"
            ]

            for i, task in enumerate(tasks, 1):
                st.checkbox(f"{i}. {task}", key=f"task_{i}")

            st.markdown("##### Next Steps")
            st.info("""
            1. Download the school list
            2. Review with district leadership
            3. Identify community partners
            4. Prepare grant applications
            5. Schedule stakeholder meetings
            """)

    with tab4:
        st.subheader("Recommended Schools for Activation")

        if results and activation in results['optimized']:
            optimized_data = results['optimized'][activation]
            activated_schools_list = optimized_data.get('activated_schools', [])

            if activated_schools_list:
                st.success(f"**{len(activated_schools_list)} schools selected for activation**")

                # Try to load school details
                school_gdf = load_school_data(state)

                if school_gdf is not None:
                    # Create detailed table
                    activated_set = set(str(s) for s in activated_schools_list)
                    school_data = []

                    for idx, school in school_gdf.iterrows():
                        if str(idx) in activated_set:
                            school_data.append({
                                'NCES ID': str(idx),
                                'School Name': school.get('School Name', school.get('NAME', '')),
                                'District': school.get('District', ''),
                                'City': school.get('CITY', school.get('City', '')),
                                'Students': school.get('Students*', 'N/A')
                            })

                    if school_data:
                        school_df = pd.DataFrame(school_data)
                        st.dataframe(school_df.head(50), use_container_width=True)

                        if len(school_data) > 50:
                            st.warning(f"Showing first 50 of {len(school_data)} schools.")

                        # Download button
                        csv = pd.DataFrame(school_data).to_csv(index=False)
                        st.download_button(
                            label="Download Full School List (CSV)",
                            data=csv,
                            file_name=f"{state.lower()}_{service.lower().replace(' ', '_')}_schools_{activation}pct.csv",
                            mime="text/csv"
                        )
                else:
                    # Fallback: just show IDs
                    school_data = pd.DataFrame({
                        'NCES School ID': activated_schools_list[:50],
                        'Selection Order': range(1, min(51, len(activated_schools_list) + 1))
                    })

                    st.info("School names not available. Showing NCES IDs only.")
                    st.dataframe(school_data, use_container_width=True)

                    # Download button for IDs
                    full_list = pd.DataFrame({
                        'NCES_School_ID': activated_schools_list,
                        'Selection_Order': range(1, len(activated_schools_list) + 1),
                        'State': state,
                        'Service_Type': service,
                        'Activation_Rate': f"{activation}%"
                    })
                    csv = full_list.to_csv(index=False)
                    st.download_button(
                        label="Download School List (CSV)",
                        data=csv,
                        file_name=f"{state.lower()}_{service.lower().replace(' ', '_')}_schools_{activation}pct.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("No school selection data available for this activation rate.")
        else:
            st.error("School selection data not available.")

else:
    # Landing page content
    st.info("👈 Configure your analysis in the sidebar and click 'Run Analysis'")

    # About section
    with st.expander("About this Tool"):
        st.markdown("""
        ### What is SchoolShare DSS?

        This Decision Support System helps policymakers explore the impact of activating
        schools as shared service locations. Our research shows that strategic school
        activation can:

        - Reduce service access gaps by **62-78%**
        - Eliminate **46%** of structural inequality
        - Save **1,953 lives** annually (hospital access)
        - Generate **$474K-$804K** annual revenue per school

        ### How It Works

        1. **Select a state** to analyze
        2. **Choose service type** (arts or hospitals)
        3. **Set activation rate** (0-50% of schools)
        4. **Run analysis** to see projected impacts
        5. **Explore the map** to see geographic distribution

        ### Map Features (v2)

        - **Choropleth visualization** showing coverage improvements by CBG
        - **Toggle views**: Distance reduction, % improvement, or coverage status
        - **Click on markers** to see facility/school details
        - **Layer controls** to show/hide facilities and schools

        ### Research Foundation

        Based on the paper: "Infrastructure Sharing as a Solution to Systemic Spatial
        Inequality" which analyzed 222,783 Census Block Groups across 49 US states.
        
        **Paper**: [Available on SSRN](https://papers.ssrn.com/)
        """)

    # Quick stats
    st.markdown("### National Impact Potential")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Schools Available", "18,209", "Public high schools")

    with col2:
        st.metric("People in Deserts", "7.6M", ">10km from services")

    with col3:
        st.metric("Potential Lives Saved", "1,953", "Annual (50% activation)")

    with col4:
        st.metric("Cost Effectiveness", "$61-$327", "Per person helped")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <small>SchoolShare DSS v2.0 | <a href="https://schoolsharedss.org">schoolsharedss.org</a></small>
    </div>
    """,
    unsafe_allow_html=True
)
