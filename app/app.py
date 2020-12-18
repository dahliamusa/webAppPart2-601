from typing import List, Dict
import simplejson as json
from flask import Flask, request, Response, redirect, session
from flask import render_template
from flaskext.mysql import MySQL
from pymysql.cursors import DictCursor
import hashlib

app = Flask(__name__)
mysql = MySQL(cursorclass=DictCursor)

app.config['MYSQL_DATABASE_HOST'] = 'db'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_PORT'] = 3306
app.config['MYSQL_DATABASE_DB'] = 'citiesData'
mysql.init_app(app)

app.secret_key = "abc"


@app.route('/', methods=['GET'])
def index():
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblUsers WHERE email=%s', "admin@njit.edu")
    result = cursor.fetchall()
    if len(result) == 0:
        inputData = ("Admin", "NJIT", "admin@njit.edu", hashlib.sha256("admin".encode()).hexdigest())
        sql_insert_query = """INSERT INTO tblUsers (firstName, lastName, email, password) VALUES (%s, %s,%s, %s) """
        cursor.execute(sql_insert_query, inputData)
        mysql.get_db().commit()
    return render_template('index.html', title='Login')


@app.route('/', methods=['POST'])
def login():
    inputData = (request.form.get('loginEmail'), hashlib.sha256(request.form.get('loginPassword').encode()).hexdigest())
    # Check that variables aren't empty
    for data in inputData:
        if len(data) == 0:
            return render_template('index.html', title='Log in', message='Enter email and password')
    # Perform query
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblUsers WHERE email=%s AND password=%s', inputData)
    result = cursor.fetchall()
    if len(result) > 0:
        session['email'] = result[0]['email']
        session['firstName'] = result[0]['firstName']
        return redirect('/homepage', code=302)
    else:
        return render_template('index.html', title='Log in', message='Incorrect email or password')


@app.route('/homepage', methods=['GET'])
def homepage():
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblCitiesImport')
    result = cursor.fetchall()
    return render_template('homepage.html', title='Home', email=session['email'], user=session['firstName'], cities=result)


@app.route('/register', methods=['GET'])
def register_get():
    return render_template('register.html', title='Register')


@app.route('/register', methods=['POST'])
def register_post():
    cursor = mysql.get_db().cursor()
    inputData = (request.form.get('regFirstName'), request.form.get('regLastName'),
                 request.form.get('regEmail'), hashlib.sha256(request.form.get('regPassword').encode()).hexdigest())
    confirmPassword = hashlib.sha256(request.form.get('regPassword2').encode()).hexdigest()
    # Check that variables aren't empty
    for data in inputData:
        if len(data) == 0:
            return render_template('register.html', title='Register', message='Please complete all fields')
    if len(confirmPassword) == 0:
        return render_template('register.html', title='Register', message='Please complete all fields')
    # Check if there is an existing account associated with email
    cursor.execute('SELECT * FROM tblUsers WHERE email=%s', inputData[2])
    result = cursor.fetchall()
    if len(result) > 0:
        return render_template('register.html', title='Register', message='An account already exists with that email')
    # Check that passwords match
    if not inputData[3] == confirmPassword:
        return render_template('register.html', title='Register', message='The passwords do not match')
    # Insert data to table
    sql_insert_query = """INSERT INTO tblUsers (firstName, lastName, email, password) VALUES (%s, %s,%s, %s) """
    cursor.execute(sql_insert_query, inputData)
    mysql.get_db().commit()
    return render_template('index.html', title='Login')


@app.route('/users', methods=['GET'])
def users():
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblUsers')
    result = cursor.fetchall()
    return render_template('users.html', title='Users', email=session['email'], users=result)


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('email', None)
    session.pop('firstName', None)
    return render_template('index.html', title='Log out')


@app.route('/view/<int:city_id>', methods=['GET'])
def record_view(city_id):
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblCitiesImport WHERE id=%s', city_id)
    result = cursor.fetchall()
    return render_template('view.html', title='View Form', email=session['email'], city=result[0])


@app.route('/edit/<int:city_id>', methods=['GET'])
def form_edit_get(city_id):
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblCitiesImport WHERE id=%s', city_id)
    result = cursor.fetchall()
    return render_template('edit.html', title='Edit Form', email=session['email'], city=result[0])


@app.route('/edit/<int:city_id>', methods=['POST'])
def form_update_post(city_id):
    cursor = mysql.get_db().cursor()
    inputData = (request.form.get('fldName'), request.form.get('fldLat'), request.form.get('fldLong'),
                 request.form.get('fldCountry'), request.form.get('fldAbbreviation'),
                 request.form.get('fldCapitalStatus'), request.form.get('fldPopulation'), city_id)
    sql_update_query = """UPDATE tblCitiesImport t SET t.fldName = %s, t.fldLat = %s, t.fldLong = %s, t.fldCountry = 
    %s, t.fldAbbreviation = %s, t.fldCapitalStatus = %s, t.fldPopulation = %s WHERE t.id = %s """
    cursor.execute(sql_update_query, inputData)
    mysql.get_db().commit()
    return redirect("/homepage", code=302)


@app.route('/cities/new', methods=['GET'])
def form_insert_get():
    return render_template('new.html', title='New City Form', email=session['email'])


@app.route('/cities/new', methods=['POST'])
def form_insert_post():
    cursor = mysql.get_db().cursor()
    inputData = (request.form.get('fldName'), request.form.get('fldLat'), request.form.get('fldLong'),
                 request.form.get('fldCountry'), request.form.get('fldAbbreviation'),
                 request.form.get('fldCapitalStatus'), request.form.get('fldPopulation'))
    sql_insert_query = """INSERT INTO tblCitiesImport (fldName,fldLat,fldLong,fldCountry,fldAbbreviation,fldCapitalStatus,fldPopulation) VALUES (%s, %s,%s, %s,%s, %s,%s) """
    cursor.execute(sql_insert_query, inputData)
    mysql.get_db().commit()
    return redirect("/homepage", code=302)


@app.route('/delete/<int:city_id>', methods=['POST'])
def form_delete_post(city_id):
    cursor = mysql.get_db().cursor()
    sql_delete_query = """DELETE FROM tblCitiesImport WHERE id = %s """
    cursor.execute(sql_delete_query, city_id)
    mysql.get_db().commit()
    return redirect("/homepage", code=302)


@app.route('/api/v1/cities', methods=['GET'])
def api_browse() -> str:
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblCitiesImport')
    result = cursor.fetchall()
    json_result = json.dumps(result);
    resp = Response(json_result, status=200, mimetype='application/json')
    return resp


@app.route('/api/v1/cities/<int:city_id>', methods=['GET'])
def api_retrieve(city_id) -> str:
    cursor = mysql.get_db().cursor()
    cursor.execute('SELECT * FROM tblCitiesImport WHERE id=%s', city_id)
    result = cursor.fetchall()
    json_result = json.dumps(result);
    resp = Response(json_result, status=200, mimetype='application/json')
    return resp


@app.route('/api/v1/cities/<int:city_id>', methods=['PUT'])
def api_edit(city_id) -> str:
    cursor = mysql.get_db().cursor()
    content = request.json
    inputData = (content['fldName'], content['fldLat'], content['fldLong'],
                 content['fldCountry'], content['fldAbbreviation'],
                 content['fldCapitalStatus'], content['fldPopulation'], city_id)
    sql_update_query = """UPDATE tblCitiesImport t SET t.fldName = %s, t.fldLat = %s, t.fldLong = %s, t.fldCountry = 
        %s, t.fldAbbreviation = %s, t.fldCapitalStatus = %s, t.fldPopulation = %s WHERE t.id = %s """
    cursor.execute(sql_update_query, inputData)
    mysql.get_db().commit()
    resp = Response(status=200, mimetype='application/json')
    return resp


@app.route('/api/v1/cities', methods=['POST'])
def api_add() -> str:
    content = request.json

    cursor = mysql.get_db().cursor()
    inputData = (content['fldName'], content['fldLat'], content['fldLong'],
                 content['fldCountry'], content['fldAbbreviation'],
                 content['fldCapitalStatus'], request.form.get('fldPopulation'))
    sql_insert_query = """INSERT INTO tblCitiesImport (fldName,fldLat,fldLong,fldCountry,fldAbbreviation,fldCapitalStatus,fldPopulation) VALUES (%s, %s,%s, %s,%s, %s,%s) """
    cursor.execute(sql_insert_query, inputData)
    mysql.get_db().commit()
    resp = Response(status=201, mimetype='application/json')
    return resp


@app.route('/api/v1/cities/<int:city_id>', methods=['DELETE'])
def api_delete(city_id) -> str:
    cursor = mysql.get_db().cursor()
    sql_delete_query = """DELETE FROM tblCitiesImport WHERE id = %s """
    cursor.execute(sql_delete_query, city_id)
    mysql.get_db().commit()
    resp = Response(status=200, mimetype='application/json')
    return resp
@app.route('/calendar', methods=['GET'])
def calendar_display():
    return render_template('calendar.html', title='Calendar Display')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
