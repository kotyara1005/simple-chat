import json, sys

import pika

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.exchange_declare(
        exchange='fanout_logs',
        exchange_type='fanout',
    )

    routing_key = 'anonymous.info'
    message = json.dumps(dict(a=1, b='asd'))
    channel.basic_publish(
        exchange='fanout_logs',
        routing_key=routing_key,
        body=message,
        properties=pika.BasicProperties(
            headers={'groupName': 'name'}
        ),
    )
    print(" [x] Sent %r:%r" % (routing_key, message))
    connection.close()


if __name__ == '__main__':
    main()
