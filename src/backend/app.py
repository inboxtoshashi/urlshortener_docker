from flask import Flask, render_template, request
import os
import time
import MySQLdb

template_path = os.path.abspath('../frontend/templates')
app = Flask(__name__, template_folder='templates')

db = None
for i in range(10):
    try:
        db = MySQLdb.connect(
            host="mysql-db",
            user="appuser",
            passwd="appsecret",
            db="urlshortener"
        )
        print("DB connected successfully.")
        break
    except MySQLdb.OperationalError as e:
        print(f"Waiting for DB... attempt {i+1}/10 — {e}")
        time.sleep(3)
else:
    raise Exception("Database connection failed after 10 tries.")


@app.route('/', methods=['GET', 'POST'])
def short():
    cursor = db.cursor()
    if request.method == 'POST':
        url1 = request.form['url']
        converter = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

        # Insert the original URL first
        cursor.execute("INSERT INTO urls(original_url, short_code) VALUES (%s, '')", [url1])
        db.commit()

        # Get last inserted id
        cursor.execute("SELECT LAST_INSERT_ID()")
        data = cursor.fetchone()
        record_id = int(data[0])

        # Generate short code from ID
        short_code = ''
        while record_id:
            short_code += converter[record_id % 62]
            record_id //= 62
        short_code = ''.join(reversed(short_code))

        # Update the row with generated short code
        cursor.execute("UPDATE urls SET short_code = %s WHERE id = LAST_INSERT_ID()", [short_code])
        db.commit()

        short_url = f"http://127.0.0.1:5001/decode/{short_code}"
        return render_template('index.html', output=short_url)
    else:
        return render_template('index.html', output='')


@app.route('/decode', methods=['GET', 'POST'])
def decode():
    cursor = db.cursor()
    if request.method == 'POST':
        short_code = request.form['pattern']
        short_code = short_code.replace('/decode/', '')

        cursor.execute("SELECT original_url FROM urls WHERE short_code = %s", [short_code])
        result = cursor.fetchone()

        if result:
            return render_template('index.html', output1=result[0])
        else:
            return render_template('index.html', output1="Not Found")
    else:
        return render_template('index.html', output1='')


@app.route('/decode/<short_code>', methods=['GET'])
def redirect_short(short_code):
    cursor = db.cursor()
    cursor.execute("SELECT original_url FROM urls WHERE short_code = %s", [short_code])
    result = cursor.fetchone()

    if result:
        return render_template('redirect.html', url=result[0])
    else:
        return render_template('index.html', output='')


@app.route('/health')
def health():
    return "OK", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

