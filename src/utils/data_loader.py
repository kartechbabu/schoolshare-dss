"""
Data loading utilities for SchoolShare DSS
"""

import streamlit as st
import pandas as pd
import pickle
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_state_data(state: str, service: str, activation_rate: int) -> Dict:
    """
    Load pre-computed optimization results for a given state and service
    
    Args:
        state: State name (e.g., "Texas")
        service: Service type ("Arts Facilities", "Hospitals", "Both")
        activation_rate: School activation percentage (0-50)
    
    Returns:
        Dictionary containing baseline and optimized data
    """
    
    # Map readable names to file conventions
    state_map = {
        "Texas": "TX",
        "California": "CA", 
        "New York": "NY"
    }
    
    service_map = {
        "Arts Facilities": "PA",
        "Hospitals": "HO",
        "Both": "combined"
    }
    
    state_abbr = state_map.get(state, state)
    service_code = service_map.get(service, service)
    
    # Try to load processed pickle file first
    data_dir = Path("data/processed")
    pickle_file = data_dir / f"{state_abbr}_{service_code}_processed.pkl"
    
    if pickle_file.exists():
        with open(pickle_file, 'rb') as f:
            data = pickle.load(f)
            
        # Extract specific activation rate data
        if activation_rate == 0:
            return {
                'baseline': data['baseline'],
                'optimized': data['baseline'],  # No change at 0%
                'metrics': calculate_metrics(data['baseline'], data['baseline'])
            }
        elif activation_rate in data['optimized']:
            return {
                'baseline': data['baseline'],
                'optimized': data['optimized'][activation_rate],
                'metrics': calculate_metrics(
                    data['baseline'], 
                    data['optimized'][activation_rate]
                )
            }
    
    # If no data found, return demo data
    return generate_demo_data(state, service, activation_rate)

def calculate_metrics(baseline: Dict, optimized: Dict) -> Dict:
    """
    Calculate improvement metrics between baseline and optimized scenarios
    """
    metrics = {}
    
    # Get summary stats
    baseline_stats = baseline.get('summary_stats', {})
    optimized_stats = optimized.get('summary_stats', {})
    
    # Distance reduction
    if 'mean_distance' in baseline_stats and 'mean_distance' in optimized_stats:
        baseline_dist = baseline_stats['mean_distance']
        optimized_dist = optimized_stats['mean_distance']
        
        metrics['distance_reduction'] = (baseline_dist - optimized_dist) / baseline_dist * 100
        metrics['km_saved'] = baseline_dist - optimized_dist
        metrics['mean_baseline_distance'] = baseline_dist
        metrics['mean_optimized_distance'] = optimized_dist
    
    # Population helped
    if 'total_population' in baseline_stats:
        total_pop = baseline_stats['total_population']
        # Estimate population helped (those with >1km reduction)
        metrics['pop_helped'] = int(total_pop * 0.3)  # Placeholder
        metrics['pop_helped_pct'] = 30.0
    
    # Service-specific metrics
    if 'pct_over_10km' in baseline_stats and 'pct_over_10km' in optimized_stats:
        baseline_desert = baseline_stats['pct_over_10km']
        optimized_desert = optimized_stats['pct_over_10km']
        metrics['new_access_10km'] = int(
            (baseline_desert - optimized_desert) / 100 * total_pop
        )
    
    # Equity gaps
    if 'rural_mean_distance' in baseline_stats:
        rural_gap_baseline = baseline_stats.get('rural_mean_distance', 0) - baseline_stats.get('urban_mean_distance', 0)
        rural_gap_optimized = optimized_stats.get('rural_mean_distance', 0) - optimized_stats.get('urban_mean_distance', 0)
        metrics['rural_urban_gap_reduction'] = (rural_gap_baseline - rural_gap_optimized) / rural_gap_baseline * 100
    
    return metrics

def generate_demo_data(state: str, service: str, activation_rate: int) -> Dict:
    """
    Generate demonstration data when actual results aren't available
    """
    import numpy as np
    
    # Create realistic demo data based on manuscript findings
    np.random.seed(42)
    
    n_cbgs = 5000  # Subset for demo
    
    # Baseline distances - following manuscript patterns
    rural_mask = np.random.random(n_cbgs) < 0.2  # 20% rural
    baseline_distances = np.where(
        rural_mask,
        np.random.lognormal(2.5, 0.8, n_cbgs),  # Rural: mean ~12km
        np.random.lognormal(1.5, 0.7, n_cbgs)   # Urban: mean ~4.5km
    )
    
    # Optimized distances - progressive improvement
    reduction_factor = 0.2 + (activation_rate / 100) * 0.4
    rural_reduction = reduction_factor * 1.2  # Rural areas benefit more
    urban_reduction = reduction_factor * 0.8
    
    optimized_distances = np.where(
        rural_mask,
        baseline_distances * (1 - rural_reduction),
        baseline_distances * (1 - urban_reduction)
    )
    
    # Create dataframes
    cbg_data = pd.DataFrame({
        'GEOID': [f'48{i:09d}' for i in range(n_cbgs)],  # Texas GEOIDs
        'population': np.random.randint(500, 5000, n_cbgs),
        'rural': rural_mask.astype(int),
        'distance_km': baseline_distances
    })
    
    optimized_data = cbg_data.copy()
    optimized_data['distance_km'] = optimized_distances
    
    # Calculate summary stats
    baseline_stats = {
        'mean_distance': baseline_distances.mean(),
        'median_distance': np.median(baseline_distances),
        'pct_over_10km': (baseline_distances > 10).mean() * 100,
        'total_population': cbg_data['population'].sum(),
        'rural_mean_distance': baseline_distances[rural_mask].mean(),
        'urban_mean_distance': baseline_distances[~rural_mask].mean()
    }
    
    optimized_stats = {
        'mean_distance': optimized_distances.mean(),
        'median_distance': np.median(optimized_distances),
        'pct_over_10km': (optimized_distances > 10).mean() * 100,
        'total_population': cbg_data['population'].sum(),
        'rural_mean_distance': optimized_distances[rural_mask].mean(),
        'urban_mean_distance': optimized_distances[~rural_mask].mean()
    }
    
    return {
        'baseline': {
            'cbg_data': cbg_data,
            'summary_stats': baseline_stats
        },
        'optimized': {
            'cbg_data': optimized_data,
            'summary_stats': optimized_stats
        },
        'metrics': calculate_metrics(
            {'summary_stats': baseline_stats},
            {'summary_stats': optimized_stats}
        )
    }

@st.cache_data
def load_available_states() -> list:
    """
    Get list of states with available data
    """
    data_dir = Path("data/processed")
    if data_dir.exists():
        # Look for processed files
        pkl_files = list(data_dir.glob("*_processed.pkl"))
        states = set()
        
        state_name_map = {
            "TX": "Texas",
            "CA": "California",
            "NY": "New York"
        }
        
        for f in pkl_files:
            state_abbr = f.stem.split('_')[0]
            state_name = state_name_map.get(state_abbr, state_abbr)
            states.add(state_name)
        
        return sorted(list(states))
    
    # Default if no data files found
    return ["Texas", "California", "New York"]