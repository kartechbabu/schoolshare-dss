"""
CSV Data Loading utilities for SchoolShare DSS
Handles the optimization result CSV files
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import ast

@st.cache_data(ttl=3600)
def load_optimization_results(state: str, service: str) -> Dict:
    """
    Load optimization results from CSV files
    
    Args:
        state: State abbreviation (e.g., "TX")
        service: Service type ("arts" or "hospitals")
    
    Returns:
        Dictionary containing optimization results
    """
    
    # Map state names to codes and FIPS
    state_mapping = {
        "Alabama": ("AL", "01"), "Arkansas": ("AR", "05"), "Arizona": ("AZ", "04"),
        "California": ("CA", "06"), "Colorado": ("CO", "08"), "Connecticut": ("CT", "09"),
        "District of Columbia": ("DC", "11"), "Delaware": ("DE", "10"), "Florida": ("FL", "12"),
        "Georgia": ("GA", "13"), "Iowa": ("IA", "19"), "Idaho": ("ID", "16"),
        "Illinois": ("IL", "17"), "Indiana": ("IN", "18"), "Kansas": ("KS", "20"),
        "Kentucky": ("KY", "21"), "Louisiana": ("LA", "22"), "Massachusetts": ("MA", "25"),
        "Maryland": ("MD", "24"), "Maine": ("ME", "23"), "Michigan": ("MI", "26"),
        "Minnesota": ("MN", "27"), "Missouri": ("MO", "29"), "Mississippi": ("MS", "28"),
        "Montana": ("MT", "30"), "North Carolina": ("NC", "37"), "North Dakota": ("ND", "38"),
        "Nebraska": ("NE", "31"), "New Hampshire": ("NH", "33"), "New Jersey": ("NJ", "34"),
        "New Mexico": ("NM", "35"), "Nevada": ("NV", "32"), "New York": ("NY", "36"),
        "Ohio": ("OH", "39"), "Oklahoma": ("OK", "40"), "Oregon": ("OR", "41"),
        "Pennsylvania": ("PA", "42"), "Rhode Island": ("RI", "44"), "South Carolina": ("SC", "45"),
        "South Dakota": ("SD", "46"), "Tennessee": ("TN", "47"), "Texas": ("TX", "48"),
        "Utah": ("UT", "49"), "Virginia": ("VA", "51"), "Vermont": ("VT", "50"),
        "Washington": ("WA", "53"), "Wisconsin": ("WI", "55"), "West Virginia": ("WV", "54"),
        "Wyoming": ("WY", "56")
    }
    
    # Get state code and FIPS
    if state in state_mapping:
        state_code, state_fips = state_mapping[state]
    else:
        # Try using state as code directly
        state_code = state
        # Find FIPS by searching mapping
        state_fips = None
        for name, (code, fips) in state_mapping.items():
            if code == state:
                state_fips = fips
                break
    
    # Determine file path based on service
    if service.lower() == "arts" or service.lower() == "arts facilities":
        data_dir = Path("data/raw/result_arts_250425")
        # Find the file for this state
        pattern = f"{state_code}_{state_fips}_result_dist_*_reduced.csv"
    else:  # hospitals
        data_dir = Path("data/raw/result_hospital_250507")
        pattern = f"{state_code}_{state_fips}_result_dist_16093_32187_reduced.csv"
    
    # Find matching file
    files = list(data_dir.glob(pattern))
    if not files:
        return generate_demo_data_from_csv(state, service)
    
    # Load the CSV file
    file_path = files[0]
    df = pd.read_csv(file_path, index_col=0)
    
    # Extract data
    results = parse_optimization_csv(df, state, service)
    
    return results

def parse_optimization_csv(df: pd.DataFrame, state: str, service: str) -> Dict:
    """
    Parse the transposed CSV format into structured data
    """
    # Get activation percentages available
    activation_cols = [col for col in df.columns if col.startswith('p=')]
    percentages = [int(col.replace('p=', '').replace('%', '')) for col in activation_cols]
    
    # Extract key metrics
    results = {
        'state': state,
        'service': service,
        'metadata': {
            'n_cbgs': int(df.loc['|I|', activation_cols[0]] if activation_cols else 0),
            'n_schools': int(df.loc['|J|', activation_cols[0]] if activation_cols else 0),
            'n_facilities': int(df.loc['|Q|', activation_cols[0]] if activation_cols else 0),
            'primary_dist_m': float(df.loc['delta1 threshold', activation_cols[0]] if activation_cols else 0),
            'secondary_dist_m': float(df.loc['delta2 threshold', activation_cols[0]] if activation_cols else 0),
        },
        'baseline': {
            'primary_coverage': float(df.loc['Primary coverage', 'existing']),
            'secondary_coverage': float(df.loc['Secondary coverage', 'existing']),
            'avg_distance_m': float(df.loc['Customer Avg dist to fac', 'existing']),
            'max_distance_m': float(df.loc['Customer Max dist to fac', 'existing']),
        },
        'optimized': {}
    }
    
    # Extract data for each activation percentage
    for pct, col in zip(percentages, activation_cols):
        try:
            results['optimized'][pct] = {
                'n_schools_activated': int(df.loc['num facility to open', col]),
                'primary_coverage': float(df.loc['Primary coverage', col]),
                'secondary_coverage': float(df.loc['Secondary coverage', col]),
                'avg_distance_m': float(df.loc['Customer Avg dist to fac', col]),
                'max_distance_m': float(df.loc['Customer Max dist to fac', col]),
                'min_distance_m': float(df.loc['Customer Min dist to fac', col]),
                'nonwhite_pct': float(df.loc['Nonwhite % (secondary cover)', col]),
                'nonbach_pct': float(df.loc['NonBach % (secondary cover)', col]),
                'computation_time': float(df.loc['Total Time (sec)', col]),
            }
            
            # Extract school list if available
            if 'open facility NCESSCH' in df.index:
                school_list_str = df.loc['open facility NCESSCH', col]
                if pd.notna(school_list_str) and school_list_str != '0.0':
                    try:
                        results['optimized'][pct]['activated_schools'] = ast.literal_eval(school_list_str)
                    except:
                        results['optimized'][pct]['activated_schools'] = []
                        
        except Exception as e:
            print(f"Error parsing {col}: {e}")
            continue
    
    return results

def calculate_metrics_from_csv(results: Dict, activation_rate: int) -> Dict:
    """
    Calculate improvement metrics from CSV results
    """
    if activation_rate not in results['optimized']:
        # Find closest available rate
        available_rates = list(results['optimized'].keys())
        if not available_rates:
            return {}
        activation_rate = min(available_rates, key=lambda x: abs(x - activation_rate))
    
    baseline = results['baseline']
    optimized = results['optimized'][activation_rate]
    metadata = results['metadata']
    
    # Convert distances from meters to kilometers
    baseline_km = baseline['avg_distance_m'] / 1000
    optimized_km = optimized['avg_distance_m'] / 1000
    
    # Calculate metrics
    metrics = {
        'activation_rate': activation_rate,
        'n_schools_activated': optimized['n_schools_activated'],
        'distance_reduction': (baseline_km - optimized_km) / baseline_km * 100 if baseline_km > 0 else 0,
        'km_saved': baseline_km - optimized_km,
        'mean_baseline_distance': baseline_km,
        'mean_optimized_distance': optimized_km,
    }
    
    # Coverage improvement
    if metadata['n_cbgs'] > 0:
        baseline_coverage_pct = baseline['primary_coverage'] / metadata['n_cbgs'] * 100
        optimized_coverage_pct = optimized['primary_coverage'] / metadata['n_cbgs'] * 100
        
        metrics['baseline_coverage_pct'] = baseline_coverage_pct
        metrics['optimized_coverage_pct'] = optimized_coverage_pct
        metrics['coverage_improvement'] = optimized_coverage_pct - baseline_coverage_pct
        
        # Population helped (CBGs gaining primary coverage)
        cbgs_helped = optimized['primary_coverage'] - baseline['primary_coverage']
        metrics['cbgs_helped'] = int(cbgs_helped)
        
        # Estimate population (assume average 1500 per CBG)
        metrics['pop_helped'] = int(cbgs_helped * 1500)
        metrics['pop_helped_pct'] = cbgs_helped / metadata['n_cbgs'] * 100
    
    # Service-specific metrics
    if 'hospitals' in results['service'].lower():
        # Estimate lives saved based on response time improvement
        # Rough estimate: 1 life per 100,000 people per km reduction in response time
        pop_total = metadata['n_cbgs'] * 1500
        metrics['lives_saved'] = int(metrics['km_saved'] * pop_total / 100000)
    else:
        # New access within 10km for arts
        if metadata['primary_dist_m'] <= 10000:  # If primary threshold is ≤10km
            metrics['new_access_10km'] = metrics['pop_helped']
        else:
            # Estimate based on coverage improvement
            metrics['new_access_10km'] = int(metrics['pop_helped'] * 0.7)
    
    # Add demographic info
    metrics['nonwhite_pct_served'] = optimized.get('nonwhite_pct', 0)
    metrics['nonbach_pct_served'] = optimized.get('nonbach_pct', 0)
    
    return metrics

def get_available_states(service: str) -> List[str]:
    """
    Get list of states with available data for the service
    """
    if service.lower() == "arts" or service.lower() == "arts facilities":
        data_dir = Path("data/raw/result_arts_250425")
    else:
        data_dir = Path("data/raw/result_hospital_250507")
    
    if not data_dir.exists():
        return ["Texas", "California", "New York"]  # Demo states
    
    # Parse state codes from filenames
    files = list(data_dir.glob("*_result_dist_*_reduced.csv"))
    
    # State code to name mapping
    code_to_name = {
        "AL": "Alabama", "AR": "Arkansas", "AZ": "Arizona", "CA": "California",
        "CO": "Colorado", "CT": "Connecticut", "DC": "District of Columbia",
        "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "IA": "Iowa",
        "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "MA": "Massachusetts", "MD": "Maryland",
        "ME": "Maine", "MI": "Michigan", "MN": "Minnesota", "MO": "Missouri",
        "MS": "Mississippi", "MT": "Montana", "NC": "North Carolina", "ND": "North Dakota",
        "NE": "Nebraska", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
        "NV": "Nevada", "NY": "New York", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VA": "Virginia", "VT": "Vermont", "WA": "Washington", "WI": "Wisconsin",
        "WV": "West Virginia", "WY": "Wyoming"
    }
    
    states = []
    for f in files:
        state_code = f.stem.split('_')[0]
        state_name = code_to_name.get(state_code, state_code)
        if state_name not in states:
            states.append(state_name)
    
    return sorted(states)

def generate_demo_data_from_csv(state: str, service: str) -> Dict:
    """
    Generate demo data when actual results aren't available
    """
    # Use realistic values based on manuscript
    return {
        'state': state,
        'service': service,
        'metadata': {
            'n_cbgs': 5000,
            'n_schools': 500,
            'n_facilities': 250 if 'arts' in service.lower() else 150,
            'primary_dist_m': 3553 if 'arts' in service.lower() else 16093,
            'secondary_dist_m': 9060 if 'arts' in service.lower() else 32187,
        },
        'baseline': {
            'primary_coverage': 2500,
            'secondary_coverage': 3500,
            'avg_distance_m': 9438 if 'arts' in service.lower() else 6450,
            'max_distance_m': 178202 if 'arts' in service.lower() else 95000,
        },
        'optimized': {
            25: {
                'n_schools_activated': 125,
                'primary_coverage': 3250,
                'secondary_coverage': 4200,
                'avg_distance_m': 6500 if 'arts' in service.lower() else 4500,
                'max_distance_m': 150000 if 'arts' in service.lower() else 80000,
                'min_distance_m': 10.2,
                'nonwhite_pct': 0.35,
                'nonbach_pct': 0.65,
                'computation_time': 1.5,
                'activated_schools': []
            }
        }
    }

def load_coverage_data(state: str, service: str, activation_rate: int) -> Optional[pd.DataFrame]:
    """
    Load CBG-level coverage data for mapping
    """
    # Map state to codes
    state_mapping = {"Texas": ("TX", "48"), "California": ("CA", "06"), "New York": ("NY", "36")}
    
    if state not in state_mapping:
        return None
        
    state_code, state_fips = state_mapping[state]
    
    if service.lower() == "arts" or service.lower() == "arts facilities":
        data_dir = Path("data/raw/result_arts_250425/coverages")
    else:
        data_dir = Path("data/raw/result_hospital_250507/coverages")
    
    # Find coverage file
    pattern = f"{state_code}_{state_fips}_coverage_mindist_numfacility_{activation_rate}perc.csv"
    files = list(data_dir.glob(pattern))
    
    if not files:
        return None
    
    # Load coverage data
    df = pd.read_csv(files[0])
    
    # Convert distances from meters to kilometers
    df['mindist_current_km'] = df['mindist_current'] / 1000
    df['mindist_sol_km'] = df['mindist_sol'] / 1000
    df['distance_reduction_km'] = df['mindist_current_km'] - df['mindist_sol_km']
    
    return df