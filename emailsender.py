import smtplib

import json
import pika
import traceback, sys
import time

def consume(ch, method, properties, s):
    print(repr(s))
    try:
        link, email = json.loads(s)
    except Exception as e:
        print(repr(s))
        return
    print(email, link)
    
    try:
        smtp = smtplib.SMTP_SSL('smtp.bk.ru', 465)
        smtp.login('emailconf@bk.ru','fnocliamefnocliame')

        smtp.sendmail('emailconf@bk.ru', [email], "Please confirm your email address and visit http://emailconf.herokuapp.com/confirm/" + link)
        smtp.quit()
    except Exception as e:
        print(e)
    ch.basic_ack(delivery_tag = method.delivery_tag)

while True:
    credentials = pika.credentials.PlainCredentials(username='smausygr', password='j8gprHGwQWNY-sAyDrbMgTSj8hLu77eJ')
    conn_params = pika.ConnectionParameters(host='macaw.rmq.cloudamqp.com', virtual_host='smausygr', credentials=credentials)
    connection = pika.BlockingConnection(conn_params)
    channel = connection.channel()

    channel.queue_declare(queue='first-queue')
    channel.basic_consume('first-queue', consume)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        break
    except Exception:
        channel.stop_consuming()
        traceback.print_exc(file=sys.stdout)
    time.sleep(1)
