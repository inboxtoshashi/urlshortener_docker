from flask import Flask, render_template, request, redirect
import time
import MySQLdb

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


@app.route('/', methods=['GET', 'POST'])
def short():
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

        # ✅ Use dynamic IP from incoming request
        short_url = request.host_url.rstrip('/') + "/decode/" + short_code

        return render_template('index.html', output=short_url)
    else:
        return render_template('index.html', output='')


@app.route('/decode', methods=['GET', 'POST'])
def decode():
    cursor = db.cursor()
    if request.method == 'POST':
        input_val = request.form.get('pattern', '').strip()

        if '/decode/' in input_val:
            input_val = input_val.split('/decode/')[-1]

        if not input_val:
            return render_template('index.html', output1='Invalid input.')

        cursor.execute("SELECT original_url FROM urls WHERE short_code = %s", [input_val])
        result = cursor.fetchone()

        if result:
            return render_template('index.html', output1=result[0])
        else:
            return render_template('index.html', output1='Not Found')
    else:
        return render_template('index.html', output1='')


@app.route('/decode/<short_code>', methods=['GET'])
def redirect_short(short_code):
    cursor = db.cursor()
    cursor.execute("SELECT original_url FROM urls WHERE short_code = %s", [short_code])
    result = cursor.fetchone()

    if result and result[0]:
        return render_template('redirect.html', url=result[0])
    else:
        return render_template('index.html', output='Short URL not found.')


@app.route('/health')
def health():
    return "OK", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

