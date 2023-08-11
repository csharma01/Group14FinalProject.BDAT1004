from flask import Flask, jsonify, render_template
import requests
import mysql.connector as connector

app = Flask(__name__)

DATABASE_CONFIG = {
    'host': 'worldbankmysqlserver.mysql.database.azure.com',
    'user': 'csharma0115',
    'password': 'Admin$0115',
    'database': 'world_economic_dashboard',
    'ssl_ca': 'DigiCertGlobalRootCA.crt.pem'
}


def get_db_connection():
    return connector.connect(**DATABASE_CONFIG)

def update_database(year):
    countries_list = ['US', 'CN', 'JP', 'DE', 'IN', 'GB', 'FR', 'BR', 'IT', 'CA']
    url = f"http://api.worldbank.org/v2/country/{';'.join(countries_list)}/indicator/NY.GDP.MKTP.CD?date={year}&format=json"
    response = requests.get(url)
    data = response.json()
    countries_data = []

    for entry in data[1]:
        country_id = entry["country"]["id"]
        country_name = entry["country"]["value"]
        country_info = {
            "year": year,
            "country_id": country_id,  
            "country_name": country_name,
            "gdp": entry["value"] if entry["value"] else 0
        }
        countries_data.append(country_info)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM country_gdp WHERE year=%s", (year,))
    cursor.executemany('''
    INSERT INTO country_gdp (year, country_id, country_name, gdp) VALUES (%(year)s, %(country_id)s, %(country_name)s, %(gdp)s)
    ''', countries_data)
    conn.commit()
    conn.close()

def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS country_gdp (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        country_id VARCHAR(255) NOT NULL,
        country_name VARCHAR(255) NOT NULL,
        gdp FLOAT NOT NULL,
        year INT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS energy_consumption (
        id INTEGER PRIMARY KEY AUTO_INCREMENT,
        country_id VARCHAR(255) NOT NULL,
        year INT NOT NULL,
        energy_consumption FLOAT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

setup_database()

@app.route('/api/update/<int:year>', methods=['GET'])
def update_year_data(year):
    try:
        update_database(year)
        return jsonify({"success": True, "message": f"Data for {year} updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})

@app.route('/api/data/<int:year>', methods=['GET'])
def get_data(year):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM country_gdp WHERE year=%s", (year,))
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(data)

@app.route('/api/gdp_growth/<country_id>', methods=['GET'])
def get_gdp_growth(country_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT year, gdp FROM country_gdp WHERE country_id=%s ORDER BY year", (country_id,))
    data = cursor.fetchall()
    conn.close()
    growth_rates = []
    for i in range(1, len(data)):
        growth = ((data[i]["gdp"] - data[i-1]["gdp"]) / data[i-1]["gdp"]) * 100
        growth_rates.append({'year': data[i]["year"], 'growth_rate': growth})
    return jsonify(growth_rates)

@app.route('/api/countries', methods=['GET'])
def get_countries():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT DISTINCT country_name, country_id FROM country_gdp ORDER BY country_name")
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(data)

@app.route('/api/energy_consumption/<country_id>/<int:year>', methods=['GET'])
def get_energy_consumption(country_id, year):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT year, energy_consumption FROM energy_consumption WHERE country_id=%s AND year=%s", (country_id, year))
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(data)


@app.route('/')
def index():
    return render_template('index.html')
@app.route('/comparative')
def comparative():
    return render_template('comparative.html')
@app.route('/charts')
def charts():
    return render_template('charts.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80,debug=True)
