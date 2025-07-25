from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import xml.etree.ElementTree as ET
from datetime import datetime
import matplotlib.pyplot as plt
import sqlite3 as sql
import requests
import smtplib

today = datetime.now().strftime("%Y-%m-%d")
sender_email = "yusufefeyesil20@gmail.com"
receiver_email = "yusufefeyesil20@gmail.com" #<--- your e-mail
password = "" #<-- application password
subject = "Daily Foreign Currency information"

connection = sql.connect("Currency.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS static (
    date TEXT,
    currency TEXT,
    buy REAL,
    sale REAL
)
""")
connection.commit()

def loop():
    global msg
    url = "https://www.tcmb.gov.tr/kurlar/today.xml"
    response = requests.get(url)
    response.encoding = "utf-8"
    tree = ET.fromstring(response.text)
    
    html_context = """
        <html>
            <body>
                <h2>Foreign Currency information</h2>
                <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
                    <tr>
                        <th>Currency foreign</th>
                        <th>Buy</th>
                        <th>Sale</th>
                    </tr>
                """

    for currency in tree.findall("Currency"):
        code = currency.get("CurrencyCode")

        if code in ["USD", "EUR", "CHF"]:
            name = currency.find("Isim").text
            forex_buying = currency.find("ForexBuying").text
            forex_selling = currency.find("ForexSelling").text  

            html_context += f"""
                <tr>
                    <td>{name}</td>
                    <td>{forex_buying}</td>
                    <td>{forex_selling}</td>
                </tr>
            """

            cursor.execute("SELECT * FROM static WHERE date=? AND currency=?", (today, code))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO static VALUES (?, ?, ?, ?)", (today, code, forex_buying, forex_selling))
                connection.commit()

    html_context += """
            </table>
            </body>
        </html>
    """

    msg = MIMEMultipart('related')
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # Html graph embedded
    html_body = f"""
        <html>
            <body>
                {html_context}
                <br><h3>USD Graphic:</h3>
                <img src="cid:grafik_usd">
                <br><h3>EUR Graphic:</h3>
                <img src="cid:grafik_eur">
                <br><h3>CHF Graphic:</h3>
                <img src="cid:grafik_chf">
            </body>
        </html>
        """

    msg.attach(MIMEText(html_body, "html"))
    connection.close()

def send_mail():
    
    # Send mails
    with open("graph_usd.png", "rb") as f:
        img_usd = MIMEImage(f.read())
        img_usd.add_header('Content-ID', '<grafik_usd>')
        msg.attach(img_usd)

    with open("graph_eur.png", "rb") as f:
        img_eur = MIMEImage(f.read())
        img_eur.add_header('Content-ID', '<grafik_eur>')
        msg.attach(img_eur)

    with open("graph_chf.png", "rb") as f:
        img_chf = MIMEImage(f.read())
        img_chf.add_header('Content-ID', '<grafik_chf>')
        msg.attach(img_chf)

    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)


cursor.execute("SELECT date, sale FROM static WHERE currency='USD' ORDER BY date")
datas_usd = cursor.fetchall()

cursor.execute("SELECT date, sale FROM static WHERE currency='EUR' ORDER BY date")
datas_eur = cursor.fetchall()

cursor.execute("SELECT date, sale FROM static WHERE currency='CHF' ORDER BY date")
datas_chf = cursor.fetchall()

dates_usd = [row[0] for row in datas_usd]
sales_usd = [row[1] for row in datas_usd]

dates_eur = [row[0] for row in datas_eur]
sales_eur = [row[1] for row in datas_eur]

dates_chf = [row[0] for row in datas_chf]
sales_chf = [row[1] for row in datas_chf]

def Create_graph(date,value,file_name,g_name):
    plt.figure(figsize=(10,5))
    plt.plot(date, value, marker="o", linestyle="-", color="blue", label=g_name)
    plt.xlabel("Date")
    plt.ylabel("Sale price (₺)")
    plt.title(g_name)
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(file_name)
    plt.close()

loop()
Create_graph(dates_usd,sales_usd,"graph_usd.png","USD sale price")
Create_graph(dates_eur, sales_eur,"graph_eur.png","EUR Sale price")
Create_graph(dates_chf, sales_chf,"graph_chf.png","CHF Sale price")
send_mail()
