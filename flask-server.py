import argparse
import math
import datetime
import pika
import json
from consensus import ConsensusMessage
from flask import Flask, request
import logging

# python3 flask-server.py --node_identity 0 --port 9000

parser = argparse.ArgumentParser()
parser.add_argument(
    "--node_identity",
    type = int,
    default = -1,
    help = "Node index corresponding to this node"
)
parser.add_argument(
    "--port",
    type = int,
    default = 9000,
    help = "Port on which to start the Flask server"
)
args = parser.parse_args()

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(f'%(asctime)s - %(name)s - %(levelname)8s - Node:{args.node_identity} - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

logging.getLogger('werkzeug').setLevel(logging.WARNING)

node_identity = args.node_identity
if node_identity < 0:
    node_identity = None

app = Flask(__name__)

@app.route('/messages', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        log.debug(f'Received message: {request.json}')
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='ibft_node_'+str(node_identity))
        channel.basic_publish(exchange='', routing_key='ibft_node_'+str(node_identity), body=json.dumps(request.json))
        connection.close()
        return "POST received"
    elif request.method == 'GET':
        return "Hello from Flask!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=args.port, use_reloader=False, threaded=True)
