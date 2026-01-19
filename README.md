# SchoolShare DSS

**Decision Support System for Geographic Equity Optimization**

A Streamlit-based web application that helps policymakers explore the impact of activating public schools as shared service locations to reduce spatial inequality in access to arts facilities and hospitals.

🌐 **Live Demo**: [schoolsharedss.org](https://schoolsharedss.org)

## Overview

SchoolShare DSS visualizes optimization results from research analyzing how school infrastructure sharing can address geographic service deserts. The app provides:

- **Interactive State Analysis**: Select any US state and service type (arts or hospitals)
- **Choropleth Maps**: Visualize coverage improvements by Census Block Group
- **Impact Metrics**: Distance reductions, population helped, and equity improvements
- **Facility-School Pairings**: See which facilities are matched with activated schools
- **Implementation Resources**: Cost estimates and funding sources

## Key Findings

Our research shows that strategic school activation can:

- Reduce service access gaps by **62-78%**
- Eliminate **46%** of structural inequality
- Save an estimated **1,953 lives** annually (hospital access)
- Cost only **$61-$327** per person helped

## Installation

### Prerequisites

- Python 3.11+
- Docker (for deployment)

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/kartechbabu/schoolshare-dss.git
cd schoolshare-dss
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up data directory:
```bash
mkdir -p data/processed data/raw data/census
```

5. Run the app:
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

### Docker Deployment

```bash
docker build -t schoolshare-dss .
docker run -d -p 8501:8501 -v $(pwd)/data:/app/data:ro --name dss-app schoolshare-dss
```

## Data Requirements

This repository contains only the application code. To run with actual data, you need:

### Required Data Files

```
data/
├── processed/
│   ├── HS_gdf_meters_clipped_{STATE_FIPS}.pkl  # School locations
│   ├── OM_gdf_meters_clipped_{STATE_FIPS}.pkl  # Arts facility locations
│   └── HO_gdf_meters_clipped_{STATE_FIPS}.pkl  # Hospital locations
├── raw/
│   ├── result_arts_250425/                     # Arts optimization results
│   │   ├── {STATE}_{FIPS}_result_dist_*_reduced.csv
│   │   └── coverages/
│   └── result_hospital_250507/                 # Hospital optimization results
│       ├── {STATE}_{FIPS}_result_dist_*_reduced.csv
│       └── coverages/
└── census/
    └── cbg_shapes_2020.gpkg                    # CBG geometries
```

### Data Sources

- **School Locations**: NCES Public School Universe Survey
- **Arts Facilities**: DataArts OrgMap database
- **Hospitals**: HIFLD Open Data
- **Census Geometries**: US Census Bureau TIGER/Line Shapefiles

## Environment Variables

Configure paths via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DSS_BASE_PATH` | Application root | Auto-detected |
| `DSS_DATA_PATH` | Data directory | `{BASE}/data` |
| `DSS_CENSUS_PATH` | Census shapefiles | `{DATA}/census` |
| `DSS_PROCESSED_PATH` | Processed data | `{DATA}/processed` |
| `DSS_DEBUG` | Enable debug output | Not set |

## Project Structure

```
schoolshare-dss/
├── app.py                 # Main Streamlit application
├── src/
│   ├── config.py          # Path configuration
│   └── utils/
│       ├── csv_data_loader.py    # Load optimization results
│       ├── choropleth_map.py     # Map visualization
│       ├── data_loader.py        # Data utilities
│       ├── raw_data_loader.py    # Raw data handling
│       └── simple_map.py         # Simplified maps
├── .streamlit/
│   └── config.toml        # Streamlit configuration
├── docs/
│   ├── DEPLOYMENT.md      # Deployment guide
│   └── DOMAIN_SETUP.md    # DNS configuration
├── scripts/
│   └── deploy.sh          # Server deployment script
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Research Paper

This tool accompanies the research paper:

> **"Infrastructure Sharing as a Solution to Systemic Spatial Inequality"**
>
> Analyzing 222,783 Census Block Groups across 49 US states to demonstrate
> how cross-sector infrastructure sharing can reduce geographic disparities
> in access to essential services.

📄 **Paper**: [Available on SSRN](https://papers.ssrn.com/)

## Citation

If you use this tool in your research, please cite:

```bibtex
@article{schoolshare2025,
  title={Infrastructure Sharing as a Solution to Systemic Spatial Inequality},
  author={[Authors]},
  journal={[Journal]},
  year={2025}
}
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For questions or issues, please [open an issue](https://github.com/kartechbabu/schoolshare-dss/issues) on GitHub.
