from cli import parser
import datetime
from consensus import ConsensusMessage, ConsensusNode, ConsensusStore, Consensus
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request
import httpx
import logging
import atexit

# In each round of this example, the IBFT protocol will form consensus over drand randomness for the IBFT round number
# More information about drand can be found at https://drand.love/developer/http-api/#public-endpoints
# Since the drand protocol starts from round 1, we'll also start our IBFT protocol from round 1

class ConsensusDrand(Consensus):
    def __init__(self, nodes, byz_quorum, round_duration, start_time, store, node_identity=None, drand_source_url="https://drand.cloudflare.com/public"):
        self.drand_source_url = drand_source_url
        super().__init__(nodes, byz_quorum, round_duration, start_time, store, node_identity)
        # Start from round 1
        self.store.set_round(1)

    def create_proposal(self):
        round = self.store.get_round()
        # NOTE: Set `data` according to application-specific logic
        url = self.drand_source_url + '/' + str(round)
        response = httpx.get(url, timeout=1)
        if response.status_code != 200:
            print("Failed to GET", url, ", reponse status code:", response.status_code)
        response_json = response.json()
        data = response_json['randomness']
        sender = self.node_identity
        proposal = ConsensusMessage("PRE_PREPARE", round, data, sender)
        print(datetime.datetime.now().time(), "Proposing message:", proposal)
        return proposal

    def validate_message_data(self, message):
        # NOTE: Verify `message.data` according to application-specific logic by checking against local state
        url = self.drand_source_url + '/' + str(message.round)
        response = httpx.get(url, timeout=1)
        if response.status_code != 200:
            print("Failed to GET", url, ", reponse status code:", response.status_code)
        response_json = response.json()
        print(datetime.datetime.now().time(), "Validating message: ", message, " against drand randomness:", response_json['randomness'])
        return message.data == response_json['randomness']

parser.add_argument(
    "--drand_source",
    type = str,
    default = "https://drand.cloudflare.com/public/",
    help = "HTTP endpoint for accessing drand entropy"
)
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

consensus_instance = ConsensusDrand(nodes, byz_quorum, round_duration, start_time, store, node_identity, args.drand_source)

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
