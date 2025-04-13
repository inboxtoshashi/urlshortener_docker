from flask import Flask, render_template , request, redirect
import os
import MySQLdb

db = MySQLdb.connect(
    host=os.getenv("MYSQL_HOST", "db"),
    user=os.getenv("MYSQL_USER", "appuser"),
    passwd=os.getenv("MYSQL_PASSWORD", "appsecret"),
    db=os.getenv("MYSQL_DATABASE", "urlshortener"),
    port=3306
)
interface = MySQL(app)


@app.route('/' , methods = ['GET' , 'POST'])
def short():
	cursor = interface.connection.cursor()
	if request.method == 'POST':
		converter = ['a','b','c','d','e','f','g','h','i','j',\
					 'k','l','m','n','o','p','q','r','s','t',\
					 'u','v','w','x','y','z','A','B','C','D',\
					 'E','F','G','H','I','J','K','L','M','N',\
					 'O','P','Q','R','S','T','U','V','W','X',\
					 'Y','Z','0','1','2','3','4','5','6','7',\
					 '8','9']
		url1= request.form['url']
		cursor.execute('''INSERT INTO Url(url) VALUES(%s)''',[url1] )
		interface.connection.commit()
		cursor.execute(''' SELECT MAX(UrlId) FROM Url ''')
		data = cursor.fetchone()
		print(data[0])
		output= ''
		UrlId=int(data[0])

		while(UrlId):
			output= output+converter[UrlId%62]
			UrlId= int(UrlId/62)
		output = "".join(reversed(output))
		cursor.execute(''' UPDATE Url SET generatedUrl = (%s) WHERE UrlId= (%s) ''',(output, data))
		interface.connection.commit()
		output = "http://127.0.0.1:5001/decode/"+output

		return render_template('shortner.html', output=output)
	else:
		return render_template('shortner.html', output='')

@app.route('/decode', methods = ['GET', 'POST'])
def decode():
	cursor = interface.connection.cursor()
	if request.method == 'POST':
		UrlId= request.form['pattern']
		try:
			UrlId = UrlId[UrlId.find('/decode/'):]
			UrlId = UrlId.replace('/decode/', '')
		except:
			pass
		output=0
		for i in UrlId: 
			if 'a' <= i and 'z' >=i:
				output= (output*62)+(ord(i)-ord('a'))
			if 'A' <=i and 'Z' >=i:
				output= (output*62)+(ord(i)-ord('A'))+26
			if '0' <=i and '9' >=i:
				output= (output*62)+(ord(i)-ord('0'))+52
		cursor.execute(''' select url from Url where UrlId = (%s)''',(output,) )
		patternUrl = cursor.fetchone()[0]
		return render_template('shortner.html', output1=patternUrl)
	else:
		return render_template('shortner.html', output1='')

@app.route('/decode/<patternUrl>', methods = ['GET', 'POST'])
def redirect(patternUrl):
	cursor = interface.connection.cursor()
	if request.method == 'GET':
		UrlId= patternUrl
		output=0
		for i in UrlId: 
			if 'a' <= i and 'z' >=i:
				output= (output*62)+(ord(i)-ord('a'))
			if 'A' <=i and 'Z' >=i:
				output= (output*62)+(ord(i)-ord('A'))+26
			if '0' <=i and '9' >=i:
				output= (output*62)+(ord(i)-ord('0'))+52
		cursor.execute(''' select url from Url where UrlId = (%s)''',(output,) )
		try:
			patternUrl = cursor.fetchone()[0]
			return render_template('redirect.html', url=patternUrl)
		except:
			return render_template('shortner.html', output='')
		
	else:
		return render_template('shortner.html', output='')


if __name__ =='__main__':
	app.run(host='0.0.0.0', port=5001)
