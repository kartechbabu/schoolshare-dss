"""
Map visualization utilities for SchoolShare DSS
"""

import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
import streamlit as st
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import ast
from .raw_data_loader import get_facility_data_for_map
from config import DATA_PATH, PROCESSED_PATH

@st.cache_data(ttl=3600)
def load_school_data(state_fips: str) -> Optional[gpd.GeoDataFrame]:
    """
    Load high school data for a specific state
    
    Args:
        state_fips: State FIPS code (e.g., '48' for Texas)
    
    Returns:
        GeoDataFrame with school data or None if not found
    """
    # Use configurable path from config module
    data_path = PROCESSED_PATH
    
    # Try to load state-specific file
    file_path = data_path / f"HS_gdf_meters_clipped_{state_fips}.pkl"
    
    if file_path.exists():
        try:
            # Check if file is not empty
            if file_path.stat().st_size == 0:
                st.warning(f"School data file is empty: {file_path.name}")
                return None
                
            gdf = pd.read_pickle(file_path)
            # Check if it's a GeoDataFrame
            if hasattr(gdf, 'geometry'):
                # Convert back to lat/lon for mapping
                gdf = gdf.to_crs(epsg=4326)
            return gdf
        except Exception as e:
            st.error(f"Error loading school data: {e}")
            # Try alternate approach - load from CSV if available
            csv_path = file_path.with_suffix('.csv')
            if csv_path.exists():
                try:
                    df = pd.read_csv(csv_path)
                    return df
                except:
                    pass
            return None
    else:
        # Try loading full dataset and filtering
        full_path = data_path / "HS_gdf_meters.pkl"
        if full_path.exists():
            try:
                gdf = pd.read_pickle(full_path)
                # Filter by state
                gdf = gdf[gdf['State_FIPS_code'] == state_fips]
                # Convert to lat/lon
                gdf = gdf.to_crs(epsg=4326)
                return gdf
            except:
                return None
    return None

@st.cache_data(ttl=3600)
def load_facility_data(state_fips: str, service: str) -> Optional[gpd.GeoDataFrame]:
    """
    Load facility data (arts or hospitals) for a specific state
    """
    # Use configurable path from config module
    data_path = PROCESSED_PATH
    
    if 'arts' in service.lower():
        # Try state-specific arts file
        file_path = data_path / f"OM_gdf_meters_clipped_{state_fips}.pkl"
        if not file_path.exists():
            file_path = data_path / "OM_gdf_meters.pkl"
    else:
        # Try state-specific hospital file
        file_path = data_path / f"HO_gdf_meters_clipped_{state_fips}.pkl"
        if not file_path.exists():
            file_path = data_path / "HO_gdf_meters.pkl"
    
    if file_path.exists():
        try:
            gdf = pd.read_pickle(file_path)
            if 'arts' in service.lower():
                # Filter by state if full dataset
                if 'State' in gdf.columns:
                    state_code = get_state_code_from_fips(state_fips)
                    gdf = gdf[gdf['State'] == state_code]
            else:
                # Filter hospitals by state
                if 'ST_FIPS' in gdf.columns:
                    gdf = gdf[gdf['ST_FIPS'] == int(state_fips)]
            
            # Convert to lat/lon
            gdf = gdf.to_crs(epsg=4326)
            return gdf
        except Exception as e:
            st.error(f"Error loading facility data: {e}")
            return None
    return None

def get_state_code_from_fips(fips: str) -> str:
    """Convert FIPS code to state abbreviation"""
    fips_to_state = {
        '01': 'AL', '04': 'AZ', '05': 'AR', '06': 'CA', '08': 'CO',
        '09': 'CT', '10': 'DE', '11': 'DC', '12': 'FL', '13': 'GA',
        '16': 'ID', '17': 'IL', '18': 'IN', '19': 'IA', '20': 'KS',
        '21': 'KY', '22': 'LA', '23': 'ME', '24': 'MD', '25': 'MA',
        '26': 'MI', '27': 'MN', '28': 'MS', '29': 'MO', '30': 'MT',
        '31': 'NE', '32': 'NV', '33': 'NH', '34': 'NJ', '35': 'NM',
        '36': 'NY', '37': 'NC', '38': 'ND', '39': 'OH', '40': 'OK',
        '41': 'OR', '42': 'PA', '44': 'RI', '45': 'SC', '46': 'SD',
        '47': 'TN', '48': 'TX', '49': 'UT', '50': 'VT', '51': 'VA',
        '53': 'WA', '54': 'WV', '55': 'WI', '56': 'WY'
    }
    return fips_to_state.get(fips, fips)

def create_optimization_map(
    state: str,
    service: str,
    activated_schools: List[str],
    school_gdf: Optional[gpd.GeoDataFrame] = None,
    facility_gdf: Optional[gpd.GeoDataFrame] = None,
    results: Optional[Dict] = None
) -> folium.Map:
    """
    Create an interactive map showing optimization results
    
    Args:
        state: State name
        service: Service type (arts/hospitals)
        activated_schools: List of NCES IDs for activated schools
        school_gdf: GeoDataFrame with all schools
        facility_gdf: GeoDataFrame with facilities
    
    Returns:
        Folium map object
    """
    # Get state FIPS for data loading
    state_to_fips = {
        'Alabama': '01', 'Arizona': '04', 'Arkansas': '05', 'California': '06',
        'Colorado': '08', 'Connecticut': '09', 'Delaware': '10', 'District of Columbia': '11',
        'Florida': '12', 'Georgia': '13', 'Idaho': '16', 'Illinois': '17',
        'Indiana': '18', 'Iowa': '19', 'Kansas': '20', 'Kentucky': '21',
        'Louisiana': '22', 'Maine': '23', 'Maryland': '24', 'Massachusetts': '25',
        'Michigan': '26', 'Minnesota': '27', 'Mississippi': '28', 'Missouri': '29',
        'Montana': '30', 'Nebraska': '31', 'Nevada': '32', 'New Hampshire': '33',
        'New Jersey': '34', 'New Mexico': '35', 'New York': '36', 'North Carolina': '37',
        'North Dakota': '38', 'Ohio': '39', 'Oklahoma': '40', 'Oregon': '41',
        'Pennsylvania': '42', 'Rhode Island': '44', 'South Carolina': '45',
        'South Dakota': '46', 'Tennessee': '47', 'Texas': '48', 'Utah': '49',
        'Vermont': '50', 'Virginia': '51', 'Washington': '53', 'West Virginia': '54',
        'Wisconsin': '55', 'Wyoming': '56'
    }
    
    state_fips = state_to_fips.get(state, '48')
    
    # Load data if not provided
    if school_gdf is None or facility_gdf is None:
        # Try loading from pickle files first
        if school_gdf is None:
            with st.spinner("Loading school data..."):
                school_gdf = load_school_data(state_fips)
        
        if facility_gdf is None:
            with st.spinner("Loading facility data..."):
                facility_gdf = load_facility_data(state_fips, service)
        
        # If still no data, use synthetic data
        if (school_gdf is None or len(school_gdf) == 0) or (facility_gdf is None or len(facility_gdf) == 0):
            school_df, facility_df = get_facility_data_for_map(state, service, results)
            
            # Convert to basic dataframes for mapping (not GeoDataFrames)
            if school_gdf is None or len(school_gdf) == 0:
                school_gdf = school_df
            if facility_gdf is None or len(facility_gdf) == 0:
                facility_gdf = facility_df
    
    # Create base map
    if school_gdf is not None and len(school_gdf) > 0:
        # Center on state
        if hasattr(school_gdf, 'geometry'):
            center_lat = school_gdf.geometry.y.mean()
            center_lon = school_gdf.geometry.x.mean()
        else:
            # Regular dataframe with LAT/LON columns
            center_lat = school_gdf['LAT'].mean() if 'LAT' in school_gdf else 39.8283
            center_lon = school_gdf['LON'].mean() if 'LON' in school_gdf else -98.5795
    else:
        # Default center (US)
        center_lat, center_lon = 39.8283, -98.5795
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add facilities layer
    if facility_gdf is not None and len(facility_gdf) > 0:
        facility_group = folium.FeatureGroup(name=f'{service} Facilities')
        
        for idx, facility in facility_gdf.iterrows():
            if 'arts' in service.lower():
                name = facility.get('OrgName', 'Arts Organization')
                popup_text = f"""
                <b>{name}</b><br>
                Type: {facility.get('macro_sector', 'N/A')}<br>
                Address: {facility.get('City', 'N/A')}, {facility.get('State', 'N/A')}
                """
                color = 'purple'
                icon = 'music'
            else:
                name = facility.get('NAME', 'Hospital')
                popup_text = f"""
                <b>{name}</b><br>
                Type: {facility.get('TYPE', 'N/A')}<br>
                Beds: {facility.get('BEDS', 'N/A')}<br>
                Trauma: {facility.get('TRAUMA', 'N/A')}
                """
                color = 'red'
                icon = 'hospital-o'
            
            # Get coordinates
            if hasattr(facility, 'geometry'):
                lat, lon = facility.geometry.y, facility.geometry.x
            else:
                # Regular dataframe
                lat = facility.get('Latitude', facility.get('LATITUDE', 0))
                lon = facility.get('Longitude', facility.get('LONGITUDE', 0))
            
            if lat and lon:
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_text, max_width=300),
                    icon=folium.Icon(color=color, icon=icon, prefix='fa'),
                    tooltip=name
                ).add_to(facility_group)
        
        facility_group.add_to(m)
    
    # Add schools layers
    if school_gdf is not None and len(school_gdf) > 0:
        # Activated schools
        activated_group = folium.FeatureGroup(name='Activated Schools')
        activated_set = set(str(s) for s in activated_schools)  # Ensure all are strings
        
        activated_count = 0
        for idx, school in school_gdf.iterrows():
            # Get school ID from index (where NCESSCH is stored)
            school_id = str(idx)
                
            if school_id in activated_set:
                activated_count += 1
                popup_text = f"""
                <b>{school.get('School Name', 'School')}</b><br>
                <span style='color: green'>✓ ACTIVATED</span><br>
                Students: {school.get('Students', 'N/A')}<br>
                Address: {school.get('City', 'N/A')}, {school.get('State', 'N/A')}<br>
                Locale: {school.get('Locale', 'N/A')}
                """
                
                # Get coordinates
                if hasattr(school, 'geometry'):
                    lat, lon = school.geometry.y, school.geometry.x
                else:
                    lat = school.get('LAT', 0)
                    lon = school.get('LON', 0)
                
                if lat and lon:
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=8,
                        popup=folium.Popup(popup_text, max_width=300),
                        color='green',
                        fill=True,
                        fillColor='lightgreen',
                        fillOpacity=0.8,
                        weight=2,
                        tooltip=school.get('School Name', 'School')
                    ).add_to(activated_group)
        
        activated_group.add_to(m)
        
        # All schools layer (optional, may be too many)
        if len(school_gdf) < 1000:  # Only show if reasonable number
            all_schools_group = folium.FeatureGroup(name='All High Schools', show=False)
            
            for idx, school in school_gdf.iterrows():
                school_id = str(idx)
                if school_id not in activated_set:
                    popup_text = f"""
                    <b>{school.get('School Name', 'School')}</b><br>
                    Students: {school.get('Students', 'N/A')}<br>
                    Address: {school.get('City', 'N/A')}, {school.get('State', 'N/A')}
                    """
                    
                    # Get coordinates
                    if hasattr(school, 'geometry'):
                        lat, lon = school.geometry.y, school.geometry.x
                    else:
                        lat = school.get('LAT', 0)
                        lon = school.get('LON', 0)
                    
                    if lat and lon:
                        folium.CircleMarker(
                            location=[lat, lon],
                            radius=4,
                            popup=folium.Popup(popup_text, max_width=300),
                            color='gray',
                            fill=True,
                            fillColor='lightgray',
                            fillOpacity=0.5,
                            weight=1
                        ).add_to(all_schools_group)
            
            all_schools_group.add_to(m)
    
    # Add search functionality
    if school_gdf is not None:
        search = plugins.Search(
            layer=activated_group,
            search_label='tooltip',
            search_zoom=12,
            placeholder='Search activated schools...'
        )
        m.add_child(search)
    
    # Add fullscreen button
    plugins.Fullscreen().add_to(m)
    
    # Add measurement tool
    plugins.MeasureControl().add_to(m)
    
    return m

def create_coverage_heatmap(
    state: str,
    service: str,
    activation_rate: int,
    coverage_improvements: Optional[pd.DataFrame] = None
) -> Optional[folium.Map]:
    """
    Create a heatmap showing coverage improvements
    """
    # This would require CBG-level coverage data
    # For now, return None as we don't have this data readily available
    return None