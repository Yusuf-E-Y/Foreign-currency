from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import xml.etree.ElementTree as ET
from datetime import datetime
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3 as sql
import requests
import smtplib
import os

today = datetime.now().strftime("%Y-%m-%d")
load_dotenv(dotenv_path="password.env")  
sender_email = os.getenv("EMAİL")
receiver_email = os.getenv("EMAİL")
password = os.getenv("APP_PASSWORD")  
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
cursor.execute("SELECT sale FROM static WHERE currency='USD' ORDER BY date")
api_usd = cursor.fetchall()

cursor.execute("SELECT date, sale FROM static WHERE currency='EUR' ORDER BY date")
datas_eur = cursor.fetchall()
cursor.execute("SELECT sale FROM static WHERE currency='EUR' ORDER BY date")
api_eur = cursor.fetchall()

cursor.execute("SELECT date, sale FROM static WHERE currency='CHF' ORDER BY date")
datas_chf = cursor.fetchall()

dates_usd = [row[0] for row in datas_usd]
sales_usd = [row[1] for row in datas_usd]

dates_eur = [row[0] for row in datas_eur]
sales_eur = [row[1] for row in datas_eur]

dates_chf = [row[0] for row in datas_chf]
sales_chf = [row[1] for row in datas_chf]

def Create_graph(date, value, g_name):
    import io, base64
    import matplotlib
    matplotlib.use("Agg")
    date = [datetime.strptime(d, "%Y-%m-%d") if isinstance(d, str) else d for d in date]

    plt.figure(figsize=(12,6))
    plt.plot(date, value, marker="o", linestyle="-", color="blue", label=g_name)
    plt.xlabel("Date")
    plt.ylabel("Sale price (₺)")
    plt.title(g_name)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)

    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return img_base64

loop()
Create_graph(dates_usd, sales_usd,"USD sale price")
Create_graph(dates_eur, sales_eur,"EUR Sale price")
Create_graph(dates_chf, sales_chf,"CHF Sale price")
send_mail()
