import argparse
import math
import datetime
import pika, sys
import json
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from consensus import ConsensusNode, ConsensusMessage, ConsensusStore, Consensus

# python3 consensus-worker.py --nodes localhost:9000 --node_identity 0 --byz_quorum 1 --round_duration 3 --start_time $(( $(date '+%s') + 2 ))

parser = argparse.ArgumentParser()
parser.add_argument(
    "-n", "--nodes",
    type = str,
    default = "localhost:9000",
    help = "Comma-separated list of IPs of all the nodes"
)
parser.add_argument(
    "--node_identity",
    type = int,
    default = -1,
    help = "Node index corresponding to this node"
)
parser.add_argument(
    "-b", "--byz_quorum",
    type = int,
    default = 1,
    help = "Weight corresponding to a Byzantine quorum"
)
parser.add_argument(
    "--rc_threshold",
    type = int,
    default = 1,
    help = "Weight of the ROUND_CHANGE threshold"
)
parser.add_argument(
    "--round_duration",
    type = int,
    default = 1,
    help = "Duration (in seconds) of one round of the IBFT protocol"
)
parser.add_argument(
    "--start_time",
    type = int,
    default = math.ceil(datetime.datetime.timestamp(datetime.datetime.now()))+2,
    help = "Start time (as UNIX timestamp) for the protocol"
)

if __name__ == '__main__':
    args = parser.parse_args()
    peers = args.nodes.split(',')

    nodes = {}
    for node in [ConsensusNode(i) for i in range(len(peers))]:
        nodes[node.node_index] = node
    byz_quorum = args.byz_quorum
    rc_threshold = args.rc_threshold
    round_duration = datetime.timedelta(seconds=args.round_duration)
    start_time = datetime.datetime.fromtimestamp(args.start_time)
    node_identity = args.node_identity
    if node_identity < 0:
        node_identity = None

    store = ConsensusStore(node_identity, peers)
    consensus_instance = Consensus(nodes, byz_quorum, rc_threshold, round_duration, start_time, store, node_identity=node_identity)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='ibft_node_'+str(node_identity))

    scheduler = BackgroundScheduler()
    atexit.register(lambda: scheduler.shutdown())
    scheduler.start()

    def start_timer(start_time):
        if scheduler.get_job('round_timeout') is not None:
            scheduler.remove_job('round_timeout')
        scheduler.add_job(func=consensus_instance.round_timeout, id='round_timeout', trigger="interval", start_date=start_time, seconds=round_duration.seconds)

    def stop_timer():
        if scheduler.get_job('round_timeout') is None:
            print("Attempting to stop unstarted timer")
            return
        scheduler.remove_job('round_timeout')

    start_timer(start_time+round_duration)

    def callback(ch, method, properties, body):
        print("---------------------------")
        print("STARTING NEW JOB")
        print("---------------------------")
        message = ConsensusMessage.from_dict(json.loads(body))
        print(datetime.datetime.now(), "Received message:", message)
        process_msg_result = consensus_instance.process_message(message)
        print("process_msg_result:", process_msg_result)
        if process_msg_result == "STOP_TIMER":
            print(datetime.datetime.now(), "This node has successfully DECIDED. Stopping timer.")
            stop_timer()
        elif process_msg_result == "START_TIMER":
            print(datetime.datetime.now(), "Starting/Restarting timer.")

    channel.basic_consume(queue='ibft_node_'+str(node_identity), on_message_callback=callback, auto_ack=True)

    try:
        print("Start time:", start_time)
        if consensus_instance.node_identity == 0:
            print("This node is leader. Scheduling proposal job.")
            scheduler.add_job(func=consensus_instance.broadcast_proposal, id='leader_proposal', trigger="date", run_date=start_time)
        print('[*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
