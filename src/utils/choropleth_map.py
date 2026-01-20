"""
Choropleth Map Visualization for DSS App v2
Provides CBG-level choropleth maps with facility markers
"""

import folium
import folium.plugins
from folium.plugins import MarkerCluster
import pandas as pd
import geopandas as gpd
import numpy as np
import streamlit as st
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import branca.colormap as cm

# Import configurable paths
from config import DATA_PATH, CENSUS_PATH


# State mappings
STATE_TO_FIPS = {
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

STATE_CODE_TO_FIPS = {
    'AL': '01', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08', 'CT': '09',
    'DC': '11', 'DE': '10', 'FL': '12', 'GA': '13', 'ID': '16', 'IL': '17',
    'IN': '18', 'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23',
    'MD': '24', 'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29',
    'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33', 'NJ': '34', 'NM': '35',
    'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39', 'OK': '40', 'OR': '41',
    'PA': '42', 'RI': '44', 'SC': '45', 'SD': '46', 'TN': '47', 'TX': '48',
    'UT': '49', 'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55',
    'WY': '56'
}

STATE_CENTERS = {
    'Texas': (31.0, -99.0), 'California': (36.7, -119.4), 'New York': (42.9, -75.5),
    'Florida': (27.8, -81.7), 'Illinois': (40.0, -89.0), 'Pennsylvania': (40.9, -77.8),
    'Ohio': (40.4, -82.7), 'Georgia': (32.6, -83.4), 'North Carolina': (35.5, -79.8),
    'Michigan': (44.3, -85.6), 'Alabama': (32.8, -86.8), 'Arizona': (34.0, -111.1),
    'Arkansas': (34.8, -92.2), 'Colorado': (39.1, -105.4), 'Connecticut': (41.6, -72.7),
    'Delaware': (39.0, -75.5), 'District of Columbia': (38.9, -77.0),
    'Idaho': (44.1, -114.7), 'Indiana': (39.8, -86.1), 'Iowa': (42.0, -93.5),
    'Kansas': (38.5, -98.8), 'Kentucky': (37.8, -85.3), 'Louisiana': (31.0, -92.0),
    'Maine': (45.4, -69.0), 'Maryland': (39.0, -76.7), 'Massachusetts': (42.4, -71.4),
    'Minnesota': (46.3, -94.2), 'Mississippi': (32.7, -89.7), 'Missouri': (38.5, -92.3),
    'Montana': (46.9, -110.4), 'Nebraska': (41.5, -99.9), 'Nevada': (38.8, -116.4),
    'New Hampshire': (44.0, -71.5), 'New Jersey': (40.3, -74.5), 'New Mexico': (34.5, -106.1),
    'North Dakota': (47.5, -100.5), 'Oklahoma': (35.5, -97.5), 'Oregon': (44.0, -120.5),
    'Rhode Island': (41.7, -71.5), 'South Carolina': (33.9, -81.0), 'South Dakota': (44.4, -100.2),
    'Tennessee': (35.9, -86.4), 'Utah': (39.3, -111.7), 'Vermont': (44.0, -72.7),
    'Virginia': (37.5, -78.9), 'Washington': (47.4, -120.5), 'West Virginia': (38.9, -80.2),
    'Wisconsin': (44.8, -89.5), 'Wyoming': (43.0, -107.6)
}

# Data paths are imported from config module above


@st.cache_data(ttl=3600)
def load_coverage_data(state: str, service: str, activation_rate: int) -> Optional[pd.DataFrame]:
    """
    Load CBG-level coverage data from optimization results
    """
    fips = STATE_TO_FIPS.get(state)
    if not fips:
        return None

    # Find state code
    state_code = None
    for code, f in STATE_CODE_TO_FIPS.items():
        if f == fips:
            state_code = code
            break

    if not state_code:
        return None

    # Determine data directory
    if 'arts' in service.lower():
        data_dir = DATA_PATH / "raw/result_arts_250425/coverages"
    else:
        data_dir = DATA_PATH / "raw/result_hospital_250507/coverages"

    # Find coverage file
    pattern = f"{state_code}_{fips}_coverage_mindist_numfacility_{activation_rate}perc.csv"
    file_path = data_dir / pattern

    if not file_path.exists():
        # Try to find closest activation rate
        files = list(data_dir.glob(f"{state_code}_{fips}_coverage_*.csv"))
        if files:
            file_path = files[0]
        else:
            return None

    # Load data
    df = pd.read_csv(file_path, dtype={'GEOID': str})

    # Zero-pad GEOID to 12 characters (fixes leading zero issue)
    df['GEOID'] = df['GEOID'].str.zfill(12)

    # Calculate derived metrics
    df['distance_reduction_m'] = df['mindist_current'] - df['mindist_sol']
    df['distance_reduction_km'] = df['distance_reduction_m'] / 1000

    # Calculate percentage improvement
    df['pct_improvement'] = np.where(
        df['mindist_current'] > 0,
        (df['distance_reduction_m'] / df['mindist_current']) * 100,
        0
    )

    # Determine coverage status (within 10km)
    df['covered_before'] = df['mindist_current'] <= 10000
    df['covered_after'] = df['mindist_sol'] <= 10000
    df['newly_covered'] = (~df['covered_before']) & df['covered_after']

    return df


@st.cache_data(ttl=3600)
def load_cbg_geometries(state: str) -> Optional[gpd.GeoDataFrame]:
    """
    Load CBG geometries for the state from the geopackage
    """
    fips = STATE_TO_FIPS.get(state)
    if not fips:
        return None

    gpkg_path = CENSUS_PATH / "cbg_shapes_2020.gpkg"
    if not gpkg_path.exists():
        return None

    try:
        # Read only CBGs for this state (filter by GEOID prefix)
        gdf = gpd.read_file(
            gpkg_path,
            where=f"GEOID LIKE '{fips}%'"
        )

        # Ensure WGS84 projection
        if gdf.crs is None or gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        return gdf
    except Exception as e:
        st.warning(f"Could not load CBG geometries: {e}")
        return None


def load_school_data(state: str) -> Optional[gpd.GeoDataFrame]:
    """
    Load school location data for the state
    """
    fips = STATE_TO_FIPS.get(state)
    if not fips:
        return None

    file_path = DATA_PATH / f"processed/HS_gdf_meters_clipped_{fips}.pkl"
    if not file_path.exists():
        return None

    try:
        gdf = pd.read_pickle(file_path)
        if hasattr(gdf, 'to_crs'):
            gdf = gdf.to_crs(epsg=4326)
        return gdf
    except Exception as e:
        return None


def load_arts_facilities(state: str) -> Optional[pd.DataFrame]:
    """
    Load arts facility data from OrgMap
    """
    fips = STATE_TO_FIPS.get(state)
    if not fips:
        return None

    # Try pickled processed file first
    processed_path = DATA_PATH / f"processed/OM_gdf_meters_clipped_{fips}.pkl"
    if processed_path.exists():
        try:
            gdf = pd.read_pickle(processed_path)
            if hasattr(gdf, 'to_crs'):
                gdf = gdf.to_crs(epsg=4326)
            return gdf
        except:
            pass

    # Fall back to raw OrgMap Excel
    orgmap_path = DATA_PATH / "raw/OrgMap/OrgMap_05_15_2023.xlsx"
    if not orgmap_path.exists():
        return None

    try:
        # Get state code for filtering
        state_abbr = None
        for code, f in STATE_CODE_TO_FIPS.items():
            if f == fips:
                state_abbr = code
                break

        df = pd.read_excel(orgmap_path)
        # Filter to state
        df = df[df['State'] == state_abbr].copy()

        # Rename columns for consistency
        df = df.rename(columns={
            'OrgName': 'name',
            'Latitude': 'lat',
            'Longitude': 'lon',
            'Address': 'address',
            'City': 'city',
            'NTEECC': 'org_type'
        })

        return df
    except Exception as e:
        return None


def load_hospital_data(state: str) -> Optional[gpd.GeoDataFrame]:
    """
    Load hospital location data for the state
    """
    fips = STATE_TO_FIPS.get(state)
    if not fips:
        return None

    file_path = DATA_PATH / f"processed/HO_gdf_meters_clipped_{fips}.pkl"
    if not file_path.exists():
        return None

    try:
        gdf = pd.read_pickle(file_path)
        if hasattr(gdf, 'to_crs'):
            gdf = gdf.to_crs(epsg=4326)
        return gdf
    except Exception as e:
        return None


def create_choropleth_map(
    state: str,
    service: str,
    activation_rate: int,
    activated_schools: List[str],
    view_type: str = "Distance (km)",
    show_facilities: bool = True,
    show_schools: bool = True,
    pairings: List[Tuple] = None,
    show_pairing_lines: bool = False
) -> Optional[folium.Map]:
    """
    Create a choropleth map showing coverage improvements

    Args:
        state: State name
        service: Service type ("Arts Facilities" or "Hospitals")
        activation_rate: School activation rate percentage
        activated_schools: List of activated school IDs
        view_type: One of "Distance (km)", "% Improvement", "Coverage Status"
        show_facilities: Whether to show existing facilities
        show_schools: Whether to show activated schools
        pairings: List of (facility_id, school_id) tuples for pairing visualization
        show_pairing_lines: Whether to draw lines connecting paired facilities/schools
    """
    # Get center coordinates
    center = STATE_CENTERS.get(state, (39.8, -98.5))

    # Create base map
    m = folium.Map(
        location=center,
        zoom_start=6,
        tiles='cartodbpositron'
    )

    # Load coverage data
    coverage_df = load_coverage_data(state, service, activation_rate)

    # Load CBG geometries
    cbg_gdf = load_cbg_geometries(state)

    # Add choropleth if we have both data and geometries
    if coverage_df is not None and cbg_gdf is not None:
        # Merge coverage data with geometries
        cbg_gdf['GEOID'] = cbg_gdf['GEOID'].astype(str)
        coverage_df['GEOID'] = coverage_df['GEOID'].astype(str)

        merged = cbg_gdf.merge(coverage_df, on='GEOID', how='left')

        # Determine which column to visualize
        if view_type == "Distance (km)":
            column = 'distance_reduction_km'
            legend_name = 'Distance Reduction (km)'
            # Create colormap: gray (0) to green (max improvement)
            # Filter to positive values only for calculating max
            positive_vals = merged[column][merged[column] > 0]
            if len(positive_vals) > 0:
                max_val = positive_vals.quantile(0.95)
            else:
                max_val = 1.0
            # Ensure max_val is valid (not NaN, not negative, not zero)
            if pd.isna(max_val) or max_val <= 0:
                max_val = 1.0
            colormap = cm.LinearColormap(
                colors=['#f5f5f5', '#c7e9c0', '#74c476', '#238b45'],
                vmin=0,
                vmax=float(max_val)
            )
        elif view_type == "% Improvement":
            column = 'pct_improvement'
            legend_name = 'Distance Improvement (%)'
            # Filter to positive values for calculating max
            positive_vals = merged[column][merged[column] > 0]
            if len(positive_vals) > 0:
                max_val = min(positive_vals.quantile(0.95), 100)
            else:
                max_val = 100.0
            if pd.isna(max_val) or max_val <= 0:
                max_val = 100.0
            colormap = cm.LinearColormap(
                colors=['#f5f5f5', '#c6dbef', '#6baed6', '#2171b5'],
                vmin=0,
                vmax=float(max_val)
            )
        else:  # Coverage Status
            column = 'newly_covered'
            legend_name = 'Coverage Status'
            # Custom handling for categorical

        # Add choropleth layer
        if view_type != "Coverage Status":
            # Simplify geometries for performance
            merged_simple = merged.copy()
            merged_simple['geometry'] = merged_simple['geometry'].simplify(0.001)

            # Create GeoJson layer
            choropleth_layer = folium.FeatureGroup(name='Coverage')

            for idx, row in merged_simple.iterrows():
                value = row.get(column, 0)
                if pd.isna(value):
                    value = 0

                # Show all CBGs - gray for no change, colored for improvement
                if value > 0:
                    color = colormap(value)
                    opacity = 0.6
                else:
                    color = '#e0e0e0'  # Light gray for no change
                    opacity = 0.3

                folium.GeoJson(
                    row['geometry'].__geo_interface__,
                    style_function=lambda x, c=color, o=opacity: {
                        'fillColor': c,
                        'color': '#666',
                        'weight': 0.3,
                        'fillOpacity': o
                    },
                    tooltip=f"GEOID: {row['GEOID']}<br>"
                            f"Distance reduction: {row.get('distance_reduction_km', 0):.1f} km<br>"
                            f"Improvement: {row.get('pct_improvement', 0):.1f}%"
                ).add_to(choropleth_layer)

            choropleth_layer.add_to(m)
            colormap.add_to(m)
        else:
            # Coverage status view: red (not covered) / yellow (was covered) / green (newly covered)
            choropleth_layer = folium.FeatureGroup(name='Coverage Status')

            merged_simple = merged.copy()
            merged_simple['geometry'] = merged_simple['geometry'].simplify(0.001)

            for idx, row in merged_simple.iterrows():
                # Handle missing data
                newly_covered = row.get('newly_covered', False)
                covered_after = row.get('covered_after', False)

                if pd.isna(newly_covered):
                    newly_covered = False
                if pd.isna(covered_after):
                    covered_after = False

                if newly_covered:
                    color = '#27ae60'  # Green - newly covered
                    status = 'Newly Covered'
                    opacity = 0.6
                elif covered_after:
                    color = '#f1c40f'  # Yellow - already covered
                    status = 'Already Covered'
                    opacity = 0.5
                else:
                    color = '#e74c3c'  # Red - not covered
                    status = 'Not Covered (>10km)'
                    opacity = 0.4

                folium.GeoJson(
                    row['geometry'].__geo_interface__,
                    style_function=lambda x, c=color, o=opacity: {
                        'fillColor': c,
                        'color': '#666',
                        'weight': 0.3,
                        'fillOpacity': o
                    },
                    tooltip=f"Status: {status}<br>"
                            f"Distance before: {row.get('mindist_current', 0)/1000:.1f} km<br>"
                            f"Distance after: {row.get('mindist_sol', 0)/1000:.1f} km"
                ).add_to(choropleth_layer)

            choropleth_layer.add_to(m)

    # Add facility markers
    if show_facilities:
        if 'arts' in service.lower():
            arts_df = load_arts_facilities(state)
            if arts_df is not None:
                add_facility_markers(m, arts_df, 'arts')
        else:
            hospital_gdf = load_hospital_data(state)
            if hospital_gdf is not None:
                add_facility_markers(m, hospital_gdf, 'hospital')

    # Add activated school markers
    if show_schools and activated_schools:
        school_gdf = load_school_data(state)
        if school_gdf is not None:
            add_school_markers(m, school_gdf, activated_schools)

    # Add pairing lines if enabled
    if show_pairing_lines and pairings:
        school_gdf = load_school_data(state) if 'school_gdf' not in dir() else school_gdf
        if 'arts' in service.lower():
            facility_df = load_arts_facilities(state)
        else:
            facility_df = load_hospital_data(state)

        if school_gdf is not None and facility_df is not None:
            add_pairing_lines(m, pairings, facility_df, school_gdf,
                            facility_type='arts' if 'arts' in service.lower() else 'hospital')

    # Add layer control
    folium.LayerControl().add_to(m)

    return m


def add_facility_markers(
    m: folium.Map,
    facilities: pd.DataFrame,
    facility_type: str = 'arts',
    max_markers: int = 500
) -> None:
    """
    Add facility markers to the map
    """
    # Create feature group
    group_name = 'Arts Facilities' if facility_type == 'arts' else 'Hospitals'
    fg = folium.FeatureGroup(name=group_name)

    # Determine marker style
    if facility_type == 'arts':
        color = '#9b59b6'  # Purple
        icon_name = 'fa-theater-masks'
    else:
        color = '#3498db'  # Blue
        icon_name = 'fa-hospital'

    count = 0
    for idx, row in facilities.iterrows():
        # Get coordinates
        if hasattr(row, 'geometry') and row.geometry is not None:
            lat, lon = row.geometry.y, row.geometry.x
        elif 'lat' in row.index and 'lon' in row.index:
            lat, lon = row['lat'], row['lon']
        elif 'Latitude' in row.index and 'Longitude' in row.index:
            lat, lon = row['Latitude'], row['Longitude']
        elif 'LATITUDE' in row.index and 'LONGITUDE' in row.index:
            lat, lon = row['LATITUDE'], row['LONGITUDE']
        else:
            continue

        if pd.isna(lat) or pd.isna(lon):
            continue

        # Create popup content
        if facility_type == 'arts':
            name = row.get('name', row.get('OrgName', 'Arts Facility'))
            city = row.get('city', row.get('City', ''))
            org_type = row.get('org_type', row.get('NTEECC', ''))
            popup_html = f"""
                <b>{name}</b><br>
                Type: {org_type}<br>
                City: {city}
            """
        else:
            name = row.get('NAME', 'Hospital')
            beds = row.get('BEDS', 'N/A')
            trauma = row.get('TRAUMA', 'N/A')
            hosp_type = row.get('TYPE', '')
            popup_html = f"""
                <b>{name}</b><br>
                Type: {hosp_type}<br>
                Beds: {beds}<br>
                Trauma Level: {trauma}
            """

        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=1,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=name
        ).add_to(fg)

        count += 1
        if count >= max_markers:
            break

    fg.add_to(m)


def add_school_markers(
    m: folium.Map,
    school_gdf: gpd.GeoDataFrame,
    activated_schools: List[str],
    max_markers: int = None
) -> None:
    """
    Add activated school markers to the map
    """
    fg = folium.FeatureGroup(name='Activated Schools')

    activated_set = set(str(s) for s in activated_schools)
    count = 0

    for idx, school in school_gdf.iterrows():
        if str(idx) not in activated_set:
            continue

        if not hasattr(school, 'geometry') or school.geometry is None:
            continue

        lat, lon = school.geometry.y, school.geometry.x

        # Get school info
        name = school.get('School Name', school.get('NAME', f'School {idx}'))
        city = school.get('CITY', school.get('City', ''))
        students = school.get('Students*', 'N/A')
        district = school.get('District', '')

        popup_html = f"""
            <b>{name}</b><br>
            District: {district}<br>
            City: {city}<br>
            Students: {students}
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            color='#27ae60',  # Green
            fill=True,
            fillColor='#2ecc71',
            fillOpacity=0.8,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"School: {name}"
        ).add_to(fg)

        count += 1
        if max_markers and count >= max_markers:
            break

    fg.add_to(m)


def add_pairing_lines(
    m: folium.Map,
    pairings: List[Tuple],
    facilities: pd.DataFrame,
    schools: gpd.GeoDataFrame,
    facility_type: str = 'arts'
) -> None:
    """
    Draw dashed lines connecting each facility to its paired school.

    Args:
        m: Folium map to add lines to
        pairings: List of (facility_id, school_id) tuples
        facilities: DataFrame/GeoDataFrame with facility data
        schools: GeoDataFrame with school data
        facility_type: 'arts' or 'hospital'
    """
    fg = folium.FeatureGroup(name='Pairing Connections')

    # Build lookup dictionaries for coordinates
    facility_coords = {}
    school_coords = {}

    # Build facility coordinate lookup
    for idx, row in facilities.iterrows():
        # Get facility ID
        if facility_type == 'arts':
            fac_id = row.get('NCARID', idx)
        else:
            fac_id = idx

        # Get coordinates
        if hasattr(row, 'geometry') and row.geometry is not None:
            lat, lon = row.geometry.y, row.geometry.x
        elif 'lat' in row.index and 'lon' in row.index:
            lat, lon = row['lat'], row['lon']
        elif 'Latitude' in row.index and 'Longitude' in row.index:
            lat, lon = row['Latitude'], row['Longitude']
        elif 'LATITUDE' in row.index and 'LONGITUDE' in row.index:
            lat, lon = row['LATITUDE'], row['LONGITUDE']
        else:
            continue

        if not pd.isna(lat) and not pd.isna(lon):
            facility_coords[fac_id] = (lat, lon)

    # Build school coordinate lookup
    for idx, school in schools.iterrows():
        if not hasattr(school, 'geometry') or school.geometry is None:
            continue
        lat, lon = school.geometry.y, school.geometry.x
        school_coords[str(idx)] = (lat, lon)

    # Draw lines for each pairing
    lines_added = 0
    for facility_id, school_id in pairings:
        fac_coord = facility_coords.get(facility_id)
        sch_coord = school_coords.get(str(school_id))

        if fac_coord and sch_coord:
            folium.PolyLine(
                locations=[fac_coord, sch_coord],
                color='#e67e22',  # Orange
                weight=1.5,
                opacity=0.6,
                dash_array='5, 5',  # Dashed line
                tooltip=f"Pairing: Facility {facility_id} → School {school_id}"
            ).add_to(fg)
            lines_added += 1

    fg.add_to(m)


def create_simple_markers_map(
    state: str,
    service: str,
    activated_schools: List[str],
    show_facilities: bool = True
) -> folium.Map:
    """
    Create a simple map with just markers (no choropleth) for faster loading
    """
    center = STATE_CENTERS.get(state, (39.8, -98.5))

    m = folium.Map(
        location=center,
        zoom_start=6,
        tiles='cartodbpositron'
    )

    # Add activated schools
    if activated_schools:
        school_gdf = load_school_data(state)
        if school_gdf is not None:
            add_school_markers(m, school_gdf, activated_schools)

    # Add facilities
    if show_facilities:
        if 'arts' in service.lower():
            arts_df = load_arts_facilities(state)
            if arts_df is not None:
                add_facility_markers(m, arts_df, 'arts')
        else:
            hospital_gdf = load_hospital_data(state)
            if hospital_gdf is not None:
                add_facility_markers(m, hospital_gdf, 'hospital')

    folium.LayerControl().add_to(m)

    return m
