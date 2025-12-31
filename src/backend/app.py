from flask import Flask, render_template, request, redirect
from prometheus_client import start_http_server, Summary, Counter
import time
import pymysql
import os
from urllib.parse import urlparse, urlunparse

# Prometheus metrics
REQUEST_LATENCY = Summary('http_request_duration_seconds', 'Request latency', ['endpoint'])
RESPONSE_COUNTER = Counter('http_response_status_total', 'HTTP response status count', ['code', 'endpoint'])

# Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')

# Get database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'mysql-db'),
    'user': os.getenv('MYSQL_USER', 'appuser'),
    'password': os.getenv('MYSQL_PASSWORD', 'appsecret'),
    'database': os.getenv('MYSQL_DATABASE', 'urlshortener'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Database connection with retry logic
def get_db_connection():
    """Establish database connection with retry logic."""
    max_retries = 10
    for attempt in range(max_retries):
        try:
            connection = pymysql.connect(**DB_CONFIG)
            print(f"✅ DB connected successfully on attempt {attempt + 1}")
            return connection
        except pymysql.OperationalError as e:
            print(f"❌ DB connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                raise Exception(f"Database connection failed after {max_retries} attempts")

# Initialize database connection
db = get_db_connection()

# Basic health check endpoint
@app.route('/health')
def health():
    RESPONSE_COUNTER.labels(code='200', endpoint='/health').inc()
    return "OK", 200

# API root - JSON response
@app.route('/api')
def read_root():
    with REQUEST_LATENCY.labels('/api').time():
        RESPONSE_COUNTER.labels(code='200', endpoint='/api').inc()
        return {"message": "URL Shortener Home"}

# Home page and URL submission
@app.route('/', methods=['GET', 'POST'])
def short():
    with REQUEST_LATENCY.labels('/').time():
        cursor = db.cursor()

        if request.method == 'POST':
            original_url = request.form.get('url', '').strip()
            
            if not original_url:
                RESPONSE_COUNTER.labels(code='400', endpoint='/').inc()
                return render_template('index.html', output='URL is required')
            
            charset = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

            # First, get the next auto-increment ID without inserting
            cursor.execute("SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'urls'", [os.getenv('MYSQL_DATABASE', 'urlshortener')])
            result = cursor.fetchone()
            row_id = int(result['AUTO_INCREMENT'])
            
            # Generate short code from the ID
            short_code = ''
            temp_id = row_id
            while temp_id:
                short_code += charset[temp_id % 62]
                temp_id //= 62
            short_code = ''.join(reversed(short_code))
            
            # Insert with the generated short code
            cursor.execute("INSERT INTO urls(original_url, short_code) VALUES (%s, %s)", [original_url, short_code])
            db.commit()

            # Dynamic URL generation: uses PUBLIC_URL if set, otherwise auto-detects from request
            public_url = os.getenv('PUBLIC_URL', '').strip()
            if public_url:
                base_url = public_url.rstrip('/')
            else:
                # Auto-detect from request (works for localhost, EC2 IP, or domain)
                base_url = request.host_url.rstrip('/')
            
            short_url = f"{base_url}/decode/{short_code}"

            RESPONSE_COUNTER.labels(code='200', endpoint='/').inc()
            return render_template('index.html', output=short_url)
        else:
            RESPONSE_COUNTER.labels(code='200', endpoint='/').inc()
            return render_template('index.html', output='')

# Decode short URL form
@app.route('/decode', methods=['GET', 'POST'])
def decode():
    with REQUEST_LATENCY.labels('/decode').time():
        cursor = db.cursor()

        if request.method == 'POST':
            input_val = request.form.get('pattern', '').strip()

            if '/decode/' in input_val:
                input_val = input_val.split('/decode/')[-1]

            if not input_val:
                RESPONSE_COUNTER.labels(code='400', endpoint='/decode').inc()
                return render_template('index.html', output1='Invalid input.')

            cursor.execute("SELECT original_url FROM urls WHERE short_code = %s", [input_val])
            result = cursor.fetchone()

            if result:
                RESPONSE_COUNTER.labels(code='200', endpoint='/decode').inc()
                return render_template('index.html', output1=result['original_url'])
            else:
                RESPONSE_COUNTER.labels(code='404', endpoint='/decode').inc()
                return render_template('index.html', output1='Not Found')
        else:
            RESPONSE_COUNTER.labels(code='200', endpoint='/decode').inc()
            return render_template('index.html', output1='')

# Redirect from short URL
@app.route('/decode/<short_code>', methods=['GET'])
def redirect_short(short_code):
    with REQUEST_LATENCY.labels('/decode/<short_code>').time():
        cursor = db.cursor()
        cursor.execute("SELECT original_url FROM urls WHERE short_code = %s", [short_code])
        result = cursor.fetchone()

        if result and result['original_url']:
            RESPONSE_COUNTER.labels(code='200', endpoint='/decode/<short_code>').inc()
            return render_template('redirect.html', url=result['original_url'])
        else:
            RESPONSE_COUNTER.labels(code='404', endpoint='/decode/<short_code>').inc()
            return render_template('index.html', output='Shortened URL not found.')

# Entry point
if __name__ == '__main__':
    prometheus_port = int(os.getenv('PROMETHEUS_PORT', 9100))
    start_http_server(prometheus_port)  # Prometheus metrics
    print(f"📊 Prometheus metrics server started on port {prometheus_port}")
    app.run(host='0.0.0.0', port=5001)
