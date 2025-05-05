from flask import Flask, render_template, request, redirect
import os
import time
import MySQLdb

app = Flask(__name__, template_folder='../frontend/templates/')

for i in range(10):
    try:
        db = MySQLdb.connect(
            host="mysql-db",
            user="appuser",
            passwd="appsecret",
            db="urlshortener"
        )
        db.close()
        print("DB connected successfully.")
        break
    except MySQLdb.OperationalError as e:
        print(f"Waiting for DB... attempt {i+1}/10 — {e}")
        time.sleep(3)
else:
    raise Exception("Database connection failed after 10 tries.")


@app.route('/', methods=['GET', 'POST'])
def short():
    cursor = db_connection.cursor()
    if request.method == 'POST':
        converter = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        url1 = request.form['url']
        cursor.execute("INSERT INTO Url(url) VALUES(%s)", [url1])
        db_connection.commit()

        cursor.execute("SELECT MAX(UrlId) FROM Url")
        data = cursor.fetchone()
        UrlId = int(data[0])

        output = ''
        while UrlId:
            output += converter[UrlId % 62]
            UrlId = int(UrlId / 62)
        output = ''.join(reversed(output))

        cursor.execute("UPDATE Url SET generatedUrl = %s WHERE UrlId = %s", (output, data))
        db_connection.commit()

        short_url = f"http://127.0.0.1:5001/decode/{output}"
        return render_template('index.html', output=short_url)
    else:
        return render_template('index.html', output='')


@app.route('/decode', methods=['GET', 'POST'])
def decode():
    cursor = db_connection.cursor()
    if request.method == 'POST':
        UrlId = request.form['pattern']
        try:
            UrlId = UrlId[UrlId.find('/decode/'):]
            UrlId = UrlId.replace('/decode/', '')
        except:
            pass

        output = 0
        for i in UrlId:
            if 'a' <= i <= 'z':
                output = (output * 62) + (ord(i) - ord('a'))
            elif 'A' <= i <= 'Z':
                output = (output * 62) + (ord(i) - ord('A') + 26)
            elif '0' <= i <= '9':
                output = (output * 62) + (ord(i) - ord('0') + 52)

        cursor.execute("SELECT url FROM Url WHERE UrlId = %s", (output,))
        patternUrl = cursor.fetchone()[0]
        return render_template('index.html', output1=patternUrl)
    else:
        return render_template('index.html', output1='')


@app.route('/decode/<patternUrl>', methods=['GET'])
def redirect_short(patternUrl):
    cursor = db_connection.cursor()
    UrlId = patternUrl
    output = 0
    for i in UrlId:
        if 'a' <= i <= 'z':
            output = (output * 62) + (ord(i) - ord('a'))
        elif 'A' <= i <= 'Z':
            output = (output * 62) + (ord(i) - ord('A') + 26)
        elif '0' <= i <= '9':
            output = (output * 62) + (ord(i) - ord('0') + 52)

    cursor.execute("SELECT url FROM Url WHERE UrlId = %s", (output,))
    try:
        original_url = cursor.fetchone()[0]
        return render_template('redirect.html', url=original_url)
    except:
        return render_template('index.html', output='')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

@app.route('/health')
def health():
    return "OK", 200
