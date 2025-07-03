from flask import Flask, render_template, request, redirect
from prometheus_client import start_http_server, Summary, Counter
import time
import MySQLdb
from urllib.parse import urlparse, urlunparse

# Prometheus metrics
REQUEST_LATENCY = Summary('http_request_duration_seconds', 'Request latency', ['endpoint'])
RESPONSE_COUNTER = Counter('http_response_status_total', 'HTTP response status count', ['code', 'endpoint'])

# Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')

# Attempt DB connection with retries
db = None
for i in range(10):
    try:
        db = MySQLdb.connect(
            host="mysql-db",
            user="appuser",
            passwd="appsecret",
            db="urlshortener"
        )
        print("✅ DB connected successfully.")
        break
    except MySQLdb.OperationalError as e:
        print(f"❌ Waiting for DB... attempt {i+1}/10 — {e}")
        time.sleep(3)
else:
    raise Exception("Database connection failed after 10 tries.")

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
            original_url = request.form['url']
            charset = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

            # Insert URL with placeholder short code
            cursor.execute("INSERT INTO urls(original_url, short_code) VALUES (%s, '')", [original_url])
            db.commit()

            cursor.execute("SELECT LAST_INSERT_ID()")
            row_id = int(cursor.fetchone()[0])

            short_code = ''
            while row_id:
                short_code += charset[row_id % 62]
                row_id //= 62
            short_code = ''.join(reversed(short_code))

            cursor.execute("UPDATE urls SET short_code = %s WHERE id = LAST_INSERT_ID()", [short_code])
            db.commit()

            parsed_url = urlparse(request.host_url)
            short_url = urlunparse((
                parsed_url.scheme,
                f"{parsed_url.hostname}:9090",
                f"/decode/{short_code}",
                '', '', ''
            ))

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
                return render_template('index.html', output1=result[0])
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

        if result and result[0]:
            RESPONSE_COUNTER.labels(code='200', endpoint='/decode/<short_code>').inc()
            return render_template('redirect.html', url=result[0])
        else:
            RESPONSE_COUNTER.labels(code='404', endpoint='/decode/<short_code>').inc()
            return render_template('index.html', output='Shortened URL not found.')

# Entry point
if __name__ == '__main__':
    start_http_server(9100)  # Prometheus metrics exposed on port 9100
    app.run(host='0.0.0.0', port=5001)
