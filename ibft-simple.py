from cli import parser
import datetime
from consensus import ConsensusMessage, ConsensusNode, ConsensusStore, Consensus
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
import logging
import atexit

args = parser.parse_args()

peers = args.nodes.split(',')
store = ConsensusStore(args.store_id)
for peer in peers:
    store.add_peer(peer)

nodes = {}
for node in [ConsensusNode(i) for i in range(len(peers))]:
    nodes[node.node_index] = node
byz_quorum = args.byz_quorum
round_duration = 5*datetime.timedelta(seconds=args.phase_duration)
# This program must be running & able to receive messages at `start_time`
start_time = datetime.datetime.fromtimestamp(args.start_time)
print("start_time:", start_time)
node_identity = args.node_identity
if node_identity < 0:
    node_identity = None

consensus_instance = Consensus(nodes, byz_quorum, round_duration, start_time, store, node_identity)

app = Flask(__name__)

@app.route('/messages', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print(datetime.datetime.now().time(), "received message:", request.json)
        message = ConsensusMessage.from_dict(request.json)
        consensus_instance.receive_message(message)
        return "POST received"
    elif request.method == 'GET':
        return "Hello from Flask!"

scheduler = BackgroundScheduler()
if node_identity == 0:
    # If this node is the leader, then start at the beginning of NEW_ROUND, at `start_time`
    scheduler.add_job(func=consensus_instance.state_transition, trigger="interval", start_date=start_time, seconds=(round_duration/5).seconds)
else:
    # If this node is not the leader, then start at the end of NEW_ROUND, at `start_time + round_duration/5`
    scheduler.add_job(func=consensus_instance.state_transition, trigger="interval", start_date=start_time+round_duration/5, seconds=(round_duration/5).seconds)
scheduler.start()

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=args.port, use_reloader=False)

atexit.register(lambda: scheduler.shutdown())
