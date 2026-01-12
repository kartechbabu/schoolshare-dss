"""
Raw data loader for school, hospital, and arts venue data
Creates synthetic location data when actual files are empty
"""

import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st
from typing import Dict, Optional, List, Tuple
import random

@st.cache_data(ttl=3600)
def load_school_locations_from_nces(state: str, nces_ids: List[str]) -> pd.DataFrame:
    """
    Create synthetic school location data based on NCES IDs
    Uses state boundaries to generate plausible locations
    """
    # State bounding boxes (approximate lat/lon ranges)
    state_bounds = {
        'Alabama': {'lat': (30.0, 35.0), 'lon': (-88.5, -84.5)},
        'Arizona': {'lat': (31.3, 37.0), 'lon': (-114.8, -109.0)},
        'Arkansas': {'lat': (33.0, 36.5), 'lon': (-94.6, -89.6)},
        'California': {'lat': (32.5, 42.0), 'lon': (-124.5, -114.0)},
        'Colorado': {'lat': (37.0, 41.0), 'lon': (-109.0, -102.0)},
        'Connecticut': {'lat': (40.9, 42.0), 'lon': (-73.7, -71.8)},
        'Delaware': {'lat': (38.4, 39.8), 'lon': (-75.8, -75.0)},
        'District of Columbia': {'lat': (38.8, 39.0), 'lon': (-77.1, -76.9)},
        'Florida': {'lat': (24.5, 31.0), 'lon': (-87.6, -80.0)},
        'Georgia': {'lat': (30.3, 35.0), 'lon': (-85.6, -80.8)},
        'Idaho': {'lat': (42.0, 49.0), 'lon': (-117.2, -111.0)},
        'Illinois': {'lat': (37.0, 42.5), 'lon': (-91.5, -87.5)},
        'Indiana': {'lat': (37.8, 41.8), 'lon': (-88.1, -84.8)},
        'Iowa': {'lat': (40.4, 43.5), 'lon': (-96.6, -90.1)},
        'Kansas': {'lat': (37.0, 40.0), 'lon': (-102.0, -94.6)},
        'Kentucky': {'lat': (36.5, 39.1), 'lon': (-89.6, -81.9)},
        'Louisiana': {'lat': (29.0, 33.0), 'lon': (-94.0, -89.0)},
        'Maine': {'lat': (43.0, 47.5), 'lon': (-71.1, -67.0)},
        'Maryland': {'lat': (37.9, 39.7), 'lon': (-79.5, -75.0)},
        'Massachusetts': {'lat': (41.2, 42.9), 'lon': (-73.5, -69.9)},
        'Michigan': {'lat': (41.7, 48.2), 'lon': (-90.4, -82.4)},
        'Minnesota': {'lat': (43.5, 49.4), 'lon': (-97.2, -89.5)},
        'Mississippi': {'lat': (30.2, 35.0), 'lon': (-91.7, -88.1)},
        'Missouri': {'lat': (36.0, 40.6), 'lon': (-95.8, -89.1)},
        'Montana': {'lat': (44.3, 49.0), 'lon': (-116.0, -104.0)},
        'Nebraska': {'lat': (40.0, 43.0), 'lon': (-104.0, -95.3)},
        'Nevada': {'lat': (35.0, 42.0), 'lon': (-120.0, -114.0)},
        'New Hampshire': {'lat': (42.7, 45.3), 'lon': (-72.6, -70.7)},
        'New Jersey': {'lat': (38.9, 41.4), 'lon': (-75.6, -73.9)},
        'New Mexico': {'lat': (31.3, 37.0), 'lon': (-109.0, -103.0)},
        'New York': {'lat': (40.5, 45.0), 'lon': (-79.8, -71.9)},
        'North Carolina': {'lat': (33.8, 36.6), 'lon': (-84.3, -75.5)},
        'North Dakota': {'lat': (45.9, 49.0), 'lon': (-104.0, -96.6)},
        'Ohio': {'lat': (38.4, 42.0), 'lon': (-84.8, -80.5)},
        'Oklahoma': {'lat': (33.6, 37.0), 'lon': (-103.0, -94.4)},
        'Oregon': {'lat': (42.0, 46.3), 'lon': (-124.6, -116.5)},
        'Pennsylvania': {'lat': (39.7, 42.3), 'lon': (-80.5, -74.7)},
        'Rhode Island': {'lat': (41.1, 42.0), 'lon': (-71.9, -71.1)},
        'South Carolina': {'lat': (32.0, 35.2), 'lon': (-83.4, -78.5)},
        'South Dakota': {'lat': (42.5, 45.9), 'lon': (-104.1, -96.4)},
        'Tennessee': {'lat': (35.0, 36.7), 'lon': (-90.3, -81.6)},
        'Texas': {'lat': (25.8, 36.5), 'lon': (-106.6, -93.5)},
        'Utah': {'lat': (37.0, 42.0), 'lon': (-114.0, -109.0)},
        'Vermont': {'lat': (42.7, 45.0), 'lon': (-73.4, -71.5)},
        'Virginia': {'lat': (36.5, 39.5), 'lon': (-83.7, -75.2)},
        'Washington': {'lat': (45.5, 49.0), 'lon': (-124.8, -116.9)},
        'West Virginia': {'lat': (37.2, 40.6), 'lon': (-82.6, -77.7)},
        'Wisconsin': {'lat': (42.5, 47.1), 'lon': (-92.9, -86.8)},
        'Wyoming': {'lat': (41.0, 45.0), 'lon': (-111.1, -104.0)}
    }
    
    bounds = state_bounds.get(state, {'lat': (30.0, 48.0), 'lon': (-125.0, -65.0)})
    
    # Create synthetic data
    schools = []
    random.seed(42)  # For reproducibility
    
    for i, nces_id in enumerate(nces_ids):
        # Generate location within state bounds
        lat = random.uniform(bounds['lat'][0], bounds['lat'][1])
        lon = random.uniform(bounds['lon'][0], bounds['lon'][1])
        
        # Create school record
        schools.append({
            'NCESSCH': nces_id,
            'School Name': f'School {nces_id[-4:]}',
            'LAT': lat,
            'LON': lon,
            'City': f'City {i % 20}',
            'State': state[:2].upper(),
            'Students': random.randint(200, 2000),
            'Locale': random.choice(['City: Large', 'Suburb: Large', 'Town: Distant', 'Rural: Fringe'])
        })
    
    return pd.DataFrame(schools)

@st.cache_data(ttl=3600)
def load_arts_locations(state: str, n_facilities: int) -> pd.DataFrame:
    """
    Create synthetic arts venue location data
    """
    state_bounds = {
        'Texas': {'lat': (25.8, 36.5), 'lon': (-106.6, -93.5)},
        'California': {'lat': (32.5, 42.0), 'lon': (-124.5, -114.0)},
        'New York': {'lat': (40.5, 45.0), 'lon': (-79.8, -71.9)},
        # Add more states as needed
    }
    
    bounds = state_bounds.get(state, {'lat': (30.0, 48.0), 'lon': (-125.0, -65.0)})
    
    arts_venues = []
    random.seed(123)  # Different seed for variety
    
    for i in range(n_facilities):
        lat = random.uniform(bounds['lat'][0], bounds['lat'][1])
        lon = random.uniform(bounds['lon'][0], bounds['lon'][1])
        
        venue_types = ['Theater', 'Museum', 'Music Venue', 'Art Gallery', 'Dance Studio', 'Community Arts Center']
        
        arts_venues.append({
            'NCARID': f'ART{i:05d}',
            'OrgName': f'{random.choice(venue_types)} {i}',
            'Latitude': lat,
            'Longitude': lon,
            'City': f'City {i % 20}',
            'State': state[:2].upper(),
            'macro_sector': random.choice(['PA', 'VA', 'CA'])
        })
    
    return pd.DataFrame(arts_venues)

@st.cache_data(ttl=3600)
def load_hospital_locations(state: str, n_facilities: int) -> pd.DataFrame:
    """
    Create synthetic hospital location data
    """
    state_bounds = {
        'Texas': {'lat': (25.8, 36.5), 'lon': (-106.6, -93.5)},
        'California': {'lat': (32.5, 42.0), 'lon': (-124.5, -114.0)},
        'New York': {'lat': (40.5, 45.0), 'lon': (-79.8, -71.9)},
        # Add more states as needed
    }
    
    bounds = state_bounds.get(state, {'lat': (30.0, 48.0), 'lon': (-125.0, -65.0)})
    
    hospitals = []
    random.seed(456)  # Different seed
    
    for i in range(n_facilities):
        lat = random.uniform(bounds['lat'][0], bounds['lat'][1])
        lon = random.uniform(bounds['lon'][0], bounds['lon'][1])
        
        hospitals.append({
            'ID': f'HOSP{i:05d}',
            'NAME': f'Hospital {i}',
            'LATITUDE': lat,
            'LONGITUDE': lon,
            'CITY': f'City {i % 20}',
            'STATE': state[:2].upper(),
            'TYPE': 'GENERAL ACUTE CARE',
            'BEDS': random.randint(50, 500),
            'TRAUMA': random.choice(['LEVEL I', 'LEVEL II', 'LEVEL III', 'NOT AVAILABLE'])
        })
    
    return pd.DataFrame(hospitals)

def get_facility_data_for_map(state: str, service: str, results: dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get school and facility data for mapping
    Returns: (school_df, facility_df)
    """
    # Get metadata from results
    if results and 'metadata' in results:
        n_schools = results['metadata'].get('n_schools', 500)
        n_facilities = results['metadata'].get('n_facilities', 250)
    else:
        n_schools = 500
        n_facilities = 250
    
    # Get activated schools if available
    activated_schools = []
    if results and 'optimized' in results:
        for pct, data in results['optimized'].items():
            if 'activated_schools' in data:
                activated_schools.extend(data['activated_schools'])
    
    # Use first n activated schools or generate IDs
    if activated_schools:
        school_ids = list(set(activated_schools))[:n_schools]
    else:
        # Generate synthetic NCES IDs
        state_code = state[:2].upper()
        school_ids = [f'{state_code}{i:08d}' for i in range(n_schools)]
    
    # Load school data
    school_df = load_school_locations_from_nces(state, school_ids)
    
    # Load facility data
    if 'arts' in service.lower():
        facility_df = load_arts_locations(state, n_facilities)
    else:
        facility_df = load_hospital_locations(state, n_facilities)
    
    return school_df, facility_df