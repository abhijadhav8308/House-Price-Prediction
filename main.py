from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from flask_mysqldb import MySQL
from datetime import date
import pandas as pd
from pycaret.regression import load_model, predict_model
from statsmodels.tsa.arima_model import ARIMA
from statsmodels.tsa.arima_model import ARIMAResults
import json

app = Flask(__name__)
app.secret_key = 'secret_key'
catboost_model = load_model('Models/Final_Catboost_Model')

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'smart_buy'

mysql = MySQL(app)

area_dict = {
    98001: "Auburn", 98002: "Auburn", 98003: "Federal Way", 98004: "Bellevue", 98005: "Bellevue", 98006: "Bellevue", 98007: "Bellevue", 98008: "Bellevue",
    98010: "Black Diamond", 98011: "Bothell", 98014: "Carnation", 98019: "Duvall", 98022: "Enumclaw", 98023: "Federal Way", 98024: "Fall City",
    98027: "Issaquah", 98028: "Kenmore", 98029: "Issaquah", 98030: "Kent", 98031: "Kent", 98032: "Kent", 98033: "Kirkland", 98034: "Kirkland",
    98038: "Maple Valley",    98039: "Medina", 98040: "Mercer Island", 98042: "Kent", 98045: "North Bend", 98052: "Redmond", 98053: "Redmond",
    98055: "Renton", 98056: "Renton", 98058: "Renton", 98059: "Renton", 98065: "Snoqualmie", 98070: "Vashon", 98072: "Woodinville", 98074: "Sammamish",
    98075: "Sammamish", 98077: "Woodinville", 98092: "Auburn", 98102: "Seattle", 98103: "Seattle", 98105: "Seattle", 98106: "Seattle", 98107: "Seattle",
    98108: "Seattle", 98109: "Seattle", 98112: "Seattle", 98115: "Seattle", 98116: "Seattle", 98117: "Seattle", 98118: "Seattle", 98119: "Seattle",
    98122: "Seattle", 98125: "Seattle", 98126: "Seattle", 98133: "Seattle", 98136: "Seattle", 98144: "Seattle", 98146: "Seattle", 98148: "Seattle",
    98155: "Seattle", 98166: "Seattle", 98168: "Seattle", 98177: "Seattle", 98178: "Seattle", 98188: "Seattle", 98198: "Seattle", 98199: "Seattle",
}


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        details = request.form
        email = details['email']
        password = details['pass']
        cur = mysql.connection.cursor()
        temp = cur.execute(
            "select * from users where email=%s and password=%s", (email, password))
        result = cur.fetchone()
        cur.close()
        if temp != 0:
            session['logged_in'] = True
            session['id'] = result[0]
            session['uname'] = result[1]
            return render_template('index.html')
        return ("Login failed")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        details = request.form
        uname = details['uname']
        fname = details['fname']
        email = details['email']
        password = details['pass']
        cur = mysql.connection.cursor()
        cur.execute("insert into users(username, fullname, email, password) values(%s,%s,%s,%s)",
                    (uname, fname, email, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/property/<id>', methods=['GET', 'POST'])
def property(id):
    future_values = []
    cur = mysql.connection.cursor()
    cur.execute("select * from house where id={}".format(id))
    result = cur.fetchall()
    cur.execute(
        "select monthly_avg from area where zipcode={}".format(result[0][-6]))
    result2 = cur.fetchone()
    cur.close()
    col = ['bedrooms', 'bathrooms', 'sqft_living', 'sqft_lot', 'floors', 'waterfront', 'view', 'condition', 'grade',
           'sqft_above', 'sqft_basement', 'yr_built', 'yr_renovated', 'lat', 'long', 'sqft_living15', 'sqft_lot15']
    data = [[result[0][3], result[0][4], result[0][5], result[0][6], result[0][7], result[0][8], result[0][9], result[0][10], result[0]
             [11], result[0][12], result[0][13], result[0][14], result[0][15], result[0][17], result[0][18], result[0][19], result[0][20]]]
    df = pd.DataFrame(list(data), columns=col)
    all_predictions = predict_model(catboost_model, data=df)
    pred_val = all_predictions['Label']
    pred_val = int(pred_val[0])
    diff = ((result2[0] - float(result[0][2])))
    ts_model = ARIMAResults.load('Models/'+str(result[0][-6])+'.pkl')
    for i in range(1, 25):
        pred = ts_model.get_forecast(steps=i)
        temp = pred.predicted_mean.to_numpy()[-1]
        temp = temp - diff
        future_values.append(temp)
    return render_template('property.html', data=result, area_dict=area_dict, pred_val=pred_val, future_values=future_values, model_name=result[0][-6], monthly_avg=result2[0])


@app.route('/search', methods=['POST'])
def search():
    searchkey = request.form['searchbar']
    return render_template('search.html', area_dict=area_dict, searchkey=searchkey)


@app.route('/filter_data', methods=['POST'])
def filter_data():
    cur = mysql.connection.cursor()
    data = request.get_json()
    bedrooms_sel = data['bedrooms_sel']
    bathrooms_sel = data['bathrooms_sel']
    floors_sel = data['floors_sel']
    view_sel = data['view_sel']
    cond_sel = data['cond_sel']

    query = "select * from house where zipcode in (select zipcode from area where area_name like '{}%' and price>={} and price<={} and sqft_living>={} and sqft_living<={})".format(
        data['searchkey'], data['minprice'], data['maxprice'], data['minarea'], data['maxarea'])

    if len(bedrooms_sel) != 0:
        query += " and bedrooms in ("+','.join(bedrooms_sel)+")"
        if "5" in bedrooms_sel:
            query += " or bedrooms > 5 "

    if len(bathrooms_sel) != 0:
        query += " and bathrooms in ("+','.join(bathrooms_sel)+")"
        if "5" in bathrooms_sel:
            query += " bathrooms >5 "

    if len(floors_sel) != 0:
        query += " and floors in ("+','.join(floors_sel)+")"

    if len(view_sel) != 0:
        query += " and view in ("+','.join(view_sel)+")"

    if len(cond_sel) != 0:
        query += " and cond in ("+','.join(cond_sel)+")"

    query += " order by date limit 15"
    cur.execute(query)
    result = cur.fetchall()
    cur.close()
    result_data = []
    result = [list(record) for record in result]
    for i in range(len(result)):
        result[i][2] = float(result[i][2])
        result[i][4] = float(result[i][4])
        result[i][7] = float(result[i][7])
        row_data = {
            'id': result[i][0],
            'price': result[i][2],
            'bedrooms': result[i][3],
            'sqft_living': result[i][5],
            'yr_built': result[i][-9],
            'cond': result[i][10],
            'added_by': result[i][-1],
            'zipcode': result[i][-6]
        }
        result_data.append(row_data)
    result = jsonify(res=result_data)
    return result


@app.route('/profile', methods=['GET', 'POST'])
def update_profile():
    if request.method == "POST":
        details = request.form
        uname = details['uname']
        fname = details['fname']
        email = details['email']
        cur = mysql.connection.cursor()
        cur.execute("update users set username='{}', fullname='{}', email='{}' where id='{}'".format(
            uname, fname, email, session['id']))
        mysql.connection.commit()
        cur.close()
        return str("Info updated successfully")
    else:
        cur = mysql.connection.cursor()
        cur.execute("select * from users where id={}".format(session['id']))
        result = cur.fetchone()
        cur.close()
        return render_template('profile.html', result=result)


@app.route('/add_property', methods=['GET', 'POST'])
def add_property():
    if request.method == "POST":
        details = request.form
        uname = session['uname']
        uid = session['id']
        today = date.today()
        today = today.strftime("%Y-%m-%d")
        id = uid + int(details['Sqft_living']) + int(details['Sqft_living15']
                                                     ) + int(details['Sqft_lot']) + int(details['Sqft_lot15'])
        cur = mysql.connection.cursor()
        cur.execute("insert into house(id,date,price,bedrooms,bathrooms,sqft_living,sqft_lot,floors,waterfront,view,cond,grade,sqft_above,sqft_basement,yr_built,yr_renovated,zipcode,lat,lng,sqft_living15,sqft_lot15,added_by) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (id, today, details['Price'], details['bedroom '], details[
                    'bathroom'], details['Sqft_living'], details['Sqft_lot'], details['floors'], details['Waterfront'], details['view'], details['condition'], details['grade'], details['Sqft_above'], details['Sqft_basement'], details['Year_Built'], details['Year_Renovated'], details['Zipcode'], details['lat'], details['lng'], details['Sqft_living15'], details['Sqft_lot15'], uname))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('my_properties'))
    return render_template('add_property.html')


@app.route('/my_properties', methods=['GET', 'POST'])
def my_properties():
    cur = mysql.connection.cursor()
    cur.execute(
        "select * from house having added_by='{}'".format(session['uname']))
    result = cur.fetchall()
    cur.close()
    return render_template('my_properties.html', result=result, area_dict=area_dict)


@app.route('/header')
def header():
    return render_template('header.html')


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=False, port=5000)
