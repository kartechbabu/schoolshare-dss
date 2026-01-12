"""
Simplified map visualization using only optimization results
"""

import folium
import folium.plugins
from folium.plugins import MarkerCluster
import streamlit as st
from typing import List, Tuple, Optional
import pandas as pd
from pathlib import Path
from config import PROCESSED_PATH

def create_clustered_school_map(
    state: str,
    service: str,
    activated_schools: List[str],
    max_markers: int = None  # None = show all markers
) -> Optional[folium.Map]:
    """
    Create a simple map with direct markers for all activated schools.
    No limit by default - shows all schools selected by the optimization.
    """
    # State FIPS mapping
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

    # State centers for map initialization
    state_centers = {
        'Texas': (31.0, -99.0), 'California': (36.7, -119.4), 'New York': (42.9, -75.5),
        'Florida': (27.8, -81.7), 'Illinois': (40.0, -89.0), 'Pennsylvania': (40.9, -77.8),
        'Ohio': (40.4, -82.7), 'Georgia': (32.6, -83.4), 'North Carolina': (35.5, -79.8),
        'Michigan': (44.3, -85.6)
    }
    center = state_centers.get(state, (39.8, -98.5))

    # Try to load school data from configurable path
    file_path = PROCESSED_PATH / f"HS_gdf_meters_clipped_{state_fips}.pkl"

    if not file_path.exists():
        return None

    try:
        gdf = pd.read_pickle(file_path)
        if hasattr(gdf, 'geometry'):
            gdf = gdf.to_crs(epsg=4326)
    except Exception as e:
        st.warning(f"Could not load school data: {e}")
        return None

    # Create simple base map - no extra plugins
    m = folium.Map(
        location=center,
        zoom_start=6,
        tiles='cartodbpositron'  # Lighter tiles, faster loading
    )

    activated_set = set(str(s) for s in activated_schools)
    count = 0

    # Add markers directly to map (simpler, more reliable)
    for idx, school in gdf.iterrows():
        if str(idx) in activated_set:
            if hasattr(school, 'geometry'):
                lat, lon = school.geometry.y, school.geometry.x
            else:
                continue

            # Simple circle marker - small for performance with many markers
            folium.CircleMarker(
                location=[lat, lon],
                radius=3,  # Smaller for dense areas
                color='#27ae60',
                fill=True,
                fillColor='#2ecc71',
                fillOpacity=0.7,
                weight=1
            ).add_to(m)

            count += 1
            # Only limit if explicitly set
            if max_markers and count >= max_markers:
                break

    return m

def create_simple_optimization_map(
    state: str,
    service: str,
    results: dict,
    activation_rate: int
) -> folium.Map:
    """
    Create a simple map showing the state and basic metrics
    """
    # State center coordinates
    state_centers = {
        'Alabama': (32.806671, -86.791130),
        'Alaska': (61.370716, -152.404419),
        'Arizona': (33.729759, -111.431221),
        'Arkansas': (34.969704, -92.373123),
        'California': (36.116203, -119.681564),
        'Colorado': (39.059811, -105.311104),
        'Connecticut': (41.597782, -72.755371),
        'Delaware': (39.318523, -75.507141),
        'District of Columbia': (38.897438, -77.026817),
        'Florida': (27.766279, -81.686783),
        'Georgia': (33.040619, -83.643074),
        'Hawaii': (21.094318, -157.498337),
        'Idaho': (44.240459, -114.478828),
        'Illinois': (40.349457, -88.986137),
        'Indiana': (39.849426, -86.258278),
        'Iowa': (42.011539, -93.210526),
        'Kansas': (38.526600, -96.726486),
        'Kentucky': (37.668140, -84.670067),
        'Louisiana': (31.169546, -91.867805),
        'Maine': (44.693947, -69.381927),
        'Maryland': (39.063946, -76.802101),
        'Massachusetts': (42.230171, -71.530106),
        'Michigan': (43.326618, -84.536095),
        'Minnesota': (45.694454, -93.900192),
        'Mississippi': (32.320513, -90.075913),
        'Missouri': (38.456085, -92.288368),
        'Montana': (46.921925, -110.454353),
        'Nebraska': (41.125370, -98.268082),
        'Nevada': (38.313515, -117.055374),
        'New Hampshire': (43.452492, -71.563896),
        'New Jersey': (40.298904, -74.521011),
        'New Mexico': (34.840515, -106.248482),
        'New York': (42.165726, -74.948051),
        'North Carolina': (35.630066, -79.806419),
        'North Dakota': (47.528912, -99.784012),
        'Ohio': (40.388783, -82.764915),
        'Oklahoma': (35.565342, -96.928917),
        'Oregon': (44.572021, -122.070938),
        'Pennsylvania': (40.590752, -77.209755),
        'Rhode Island': (41.680893, -71.511780),
        'South Carolina': (33.856892, -80.945007),
        'South Dakota': (44.299782, -99.438828),
        'Tennessee': (35.747845, -86.692345),
        'Texas': (31.054487, -97.563461),
        'Utah': (40.150032, -111.862434),
        'Vermont': (44.045876, -72.710686),
        'Virginia': (37.769337, -78.169968),
        'Washington': (47.400902, -121.490494),
        'West Virginia': (38.491226, -80.954453),
        'Wisconsin': (44.268543, -89.616508),
        'Wyoming': (42.755966, -107.302490)
    }
    
    # Get state center
    center = state_centers.get(state, (39.8283, -98.5795))
    
    # Create map
    m = folium.Map(
        location=center,
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Add state marker
    folium.Marker(
        location=center,
        popup=f"""
        <b>{state}</b><br>
        Service: {service}<br>
        Activation Rate: {activation_rate}%<br>
        """,
        icon=folium.Icon(color='blue', icon='info-sign'),
        tooltip=state
    ).add_to(m)
    
    # Add metrics info box
    if results and 'optimized' in results and activation_rate in results['optimized']:
        metrics = results['optimized'][activation_rate]
        n_schools = metrics.get('n_schools_activated', 0)
        
        # Create a custom HTML for the info box
        info_html = f"""
        <div style="position: fixed; 
                    top: 10px; 
                    right: 10px; 
                    width: 300px; 
                    background-color: white; 
                    border: 2px solid rgba(0,0,0,0.2);
                    border-radius: 5px;
                    padding: 10px;
                    z-index: 1000;">
            <h4 style="margin-top: 0;">{state} Optimization Results</h4>
            <p><b>Activated Schools:</b> {n_schools}</p>
            <p><b>Primary Coverage:</b> {metrics.get('primary_coverage', 0):,} CBGs</p>
            <p><b>Avg Distance:</b> {metrics.get('avg_distance_m', 0)/1000:.1f} km</p>
            <p><b>Service Type:</b> {service}</p>
        </div>
        """
        
        # Add the HTML to the map
        m.get_root().html.add_child(folium.Element(info_html))
    
    # Add scale
    folium.plugins.MiniMap().add_to(m)
    
    return m

def create_coverage_circles_map(
    state: str,
    service: str,
    primary_dist_km: float,
    secondary_dist_km: float,
    center_points: List[Tuple[float, float]] = None
) -> folium.Map:
    """
    Create a map showing coverage circles around activated schools
    """
    # Get state center
    state_centers = {
        'Texas': (31.054487, -97.563461),
        'California': (36.116203, -119.681564),
        'New York': (42.165726, -74.948051),
        # Add more as needed
    }
    
    center = state_centers.get(state, (39.8283, -98.5795))
    
    # Create map
    m = folium.Map(
        location=center,
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # If we have center points (activated schools), add coverage circles
    if center_points:
        for i, (lat, lon) in enumerate(center_points[:20]):  # Limit to first 20
            # Primary coverage circle
            folium.Circle(
                location=[lat, lon],
                radius=primary_dist_km * 1000,  # Convert km to meters
                popup=f'Primary Coverage ({primary_dist_km:.1f} km)',
                color='green',
                fill=True,
                fillOpacity=0.1,
                weight=2
            ).add_to(m)
            
            # Secondary coverage circle
            folium.Circle(
                location=[lat, lon],
                radius=secondary_dist_km * 1000,
                popup=f'Secondary Coverage ({secondary_dist_km:.1f} km)',
                color='blue',
                fill=True,
                fillOpacity=0.05,
                weight=1,
                dashArray='5, 5'
            ).add_to(m)
            
            # School marker
            folium.CircleMarker(
                location=[lat, lon],
                radius=5,
                popup=f'School {i+1}',
                color='darkgreen',
                fill=True,
                fillColor='green',
                fillOpacity=0.8
            ).add_to(m)
    
    return m