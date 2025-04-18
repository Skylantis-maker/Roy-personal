# Energy Storage Optimization Tool

A web-based tool for optimizing energy storage operations based on electricity price data.

## Features

- Upload Excel/CSV files containing 5-minute interval electricity price data
- Choose between one-charge-one-discharge or two-charge-two-discharge strategies
- Calculate optimal charging/discharging schedules for maximum profit
- Visualize results with interactive charts

## Project Structure

```
.
├── frontend/           # Web interface files
│   ├── index.html     # Main HTML file
│   ├── styles.css     # CSS styles
│   └── script.js      # Frontend JavaScript
├── backend/           # Python backend
│   ├── app.py         # Main application logic
│   └── utils.py       # Utility functions
├── requirements.txt   # Python dependencies
└── README.md         # Project documentation
```

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python backend/app.py
```

3. Open your browser and navigate to `http://localhost:5000`

## Data Format

Input files should be in Excel or CSV format with two columns:
- First row: Column headers (will be skipped)
- First column: Timestamp in format `DD/MM/YYYY HH:MM` or `YYYY-MM-DD HH:MM`
- Second column: Electricity price in AUD/MWh
- Data should be in 5-minute intervals (288 points per day)

## Update Log

### 2024-04-18
- Improved data processing:
  - Now properly handles monthly data (multiple days)
  - Skips header row in input files
  - Validates data points per day (should be 288)
  - Supports multiple date formats

- Enhanced profit calculation:
  - Implemented one-charge-one-discharge strategy
    - Finds optimal 2-hour windows for charging and discharging
    - Ensures charging happens before discharging
  - Added two-charge-two-discharge strategy
    - Finds two sets of optimal charging/discharging windows
    - Ensures proper sequence (charge-discharge-charge-discharge)
    - Prevents time window overlaps

- Improved error handling and logging:
  - Added data validation warnings
  - Better error messages for invalid data
  - Detailed logging of processing steps

## License

MIT License 