from flask import Flask
from flask_mysqldb import MySQL 

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'smart_buy'

mysql = MySQL(app)

area_dict = {
        98001:"Auburn", 98002:"Auburn", 98003:"Federal Way", 98004:"Bellevue", 98005:"Bellevue", 98006:"Bellevue", 98007:"Bellevue", 98008:"Bellevue",
		98010:"Black Diamond", 98011:"Bothell", 98014:"Carnation", 98019:"Duvall", 98022:"Enumclaw", 98023:"Federal Way", 98024:"Fall City",
		98027:"Issaquah", 98028:"Kenmore", 98029:"Issaquah", 98030:"Kent", 98031:"Kent", 98032:"Kent", 98033:"Kirkland", 98034:"Kirkland",
		98038:"Maple Valley",    98039:"Medina", 98040:"Mercer Island", 98042:"Kent", 98045:"North Bend", 98052:"Redmond", 98053:"Redmond", 
		98055:"Renton", 98056:"Renton", 98058:"Renton", 98059:"Renton", 98065:"Snoqualmie", 98070:"Vashon", 98072:"Woodinville", 98074:"Sammamish",
 		98075:"Sammamish", 98077:"Woodinville", 98092:"Auburn", 98102:"Seattle", 98103:"Seattle", 98105:"Seattle", 98106:"Seattle", 98107:"Seattle", 
		98108:"Seattle", 98109:"Seattle", 98112:"Seattle", 98115:"Seattle", 98116:"Seattle", 98117:"Seattle", 98118:"Seattle", 98119:"Seattle", 
		98122:"Seattle", 98125:"Seattle", 98126:"Seattle", 98133:"Seattle", 98136:"Seattle", 98144:"Seattle", 98146:"Seattle", 98148:"Seattle",
		98155:"Seattle", 98166:"Seattle", 98168:"Seattle", 98177:"Seattle", 98178:"Seattle", 98188:"Seattle", 98198:"Seattle", 98199:"Seattle",
}

with app.app_context():
    cur = mysql.connection.cursor()
    for zip in area_dict:
        cur = mysql.connection.cursor()
        cur.execute("insert into area values(%s,%s)",(str(zip), area_dict[zip]))
        mysql.connection.commit()
        cur.close()
    
