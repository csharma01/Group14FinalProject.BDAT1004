from flask import Flask, jsonify, render_template
import requests
import sqlite3



app = Flask(__name__)

DATABASE = 'world_economic_dashboard.db'


def update_database(year):
    # List of top 10 countries by GDP
    countries_list = ['US', 'CN', 'JP', 'DE', 'IN', 'GB', 'FR', 'BR', 'IT', 'CA']

    # Fetch data from the World Bank API for the given year and list of countries
    url = f"http://api.worldbank.org/v2/country/{';'.join(countries_list)}/indicator/NY.GDP.MKTP.CD?date={year}&format=json"
    response = requests.get(url)
    data = response.json()

    # Extract relevant details
    countries_data = []

    for entry in data[1]:
        country_id = entry["country"]["id"]
        country_name = entry["country"]["value"]

        country_info = {
            "year": year,
            "country_id": country_id,  
            "country_name": country_name,
            "gdp": entry["value"] if entry["value"] else 0  # Set GDP to 0 if it's None
        }
        countries_data.append(country_info)

    # Connect to database and update data
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Clear the existing data for the given year and insert the new data
    cursor.execute("DELETE FROM country_gdp WHERE year=?", (year,))
    cursor.executemany('''
    INSERT INTO country_gdp (year, country_id, country_name, gdp) VALUES (:year, :country_id, :country_name, :gdp)
    ''', countries_data)

    conn.commit()
    conn.close()


def setup_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create the tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS country_gdp (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id TEXT NOT NULL,
        country_name TEXT NOT NULL,
        gdp REAL NOT NULL,
        year INTEGER NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS energy_consumption (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id TEXT NOT NULL,
        year INTEGER NOT NULL,
        energy_consumption REAL NOT NULL
    )
    ''')

    conn.commit()
    conn.close()


# Call this function before running the Flask app
setup_database()

@app.route('/api/update/<int:year>', methods=['GET'])
def update_year_data(year):
    try:
        update_database(year)
        print(f"Data for {year} updated successfully!")
        return jsonify({"success": True, "message": f"Data for {year} updated successfully!"})
    except Exception as e:
        print(f"Error updating data for {year}: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"})


@app.route('/api/data/<int:year>', methods=['GET'])
def get_data(year):
    # Fetch data for the given year from the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute("SELECT * FROM country_gdp WHERE year=?", (year,))
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(data)

@app.route('/api/gdp_growth/<country_id>', methods=['GET'])
def get_gdp_growth(country_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.row_factory = sqlite3.Row
    
    # Fetch GDP data for the given country from the database
    cursor.execute("SELECT year, gdp FROM country_gdp WHERE country_id=? ORDER BY year", (country_id,))
    data = cursor.fetchall()
    conn.close()
    
    # Calculate the growth rate
    growth_rates = []
    for i in range(1, len(data)):
        growth = ((data[i]["gdp"] - data[i-1]["gdp"]) / data[i-1]["gdp"]) * 100
        growth_rates.append({'year': data[i]["year"], 'growth_rate': growth})
    
    return jsonify(growth_rates)

@app.route('/api/countries', methods=['GET'])
def get_countries():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute("SELECT DISTINCT country_name, country_id FROM country_gdp ORDER BY country_name")
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(data)

@app.route('/api/energy_consumption/<country_id>/<int:year>', methods=['GET'])
def get_energy_consumption(country_id, year):
    # Fetch energy consumption data for the given country and year from the database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute("SELECT year, energy_consumption FROM energy_consumption WHERE country_id=? AND year=?", (country_id, year))
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(data)


@app.route('/')
def index():
    return render_template('index.html')
@app.route('/comparative')
def comparative():
    return render_template('comparative.html')


if __name__ == '__main__':
    app.run(debug=True)
