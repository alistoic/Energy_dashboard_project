
# Energy Consumption Dashboard

This is an interactive web application built with Dash and Plotly to visualize global energy consumption trends from various renewable sources (wind, hydro, solar, etc.).

## Features

- Interactive choropleth map to display energy consumption by country and energy type.
- Dynamic charts showing energy trends, distribution, and cumulative consumption.
- Dropdown selections for years, countries, and energy types.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alistoic/Energy_dashboard_project.git
   cd Energy_dashboard_project
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To start the app locally, run:
```bash
python app.py
```

Then, open your browser and go to `http://127.0.0.1:8050/`.

## Deployment

To deploy this app on Heroku:
1. Ensure you have a `Procfile` and a `requirements.txt` file in the root directory.
2. Push the code to your Heroku repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
