import argparse
import math
import datetime

# python3 ibft-simple.py --nodes localhost:9000 --node_identity 0 --store_id node0 --byz_quorum 1 --phase_duration 1 --start_time $(( $(date '+%s') + 2 )) --port 9000

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
    "--store_id",
    type = str,
    default = "node0",
    help = "Unique ID string to prepend to the Redis keys for this node"
)
parser.add_argument(
    "-b", "--byz_quorum",
    type = int,
    default = 1,
    help = "Weight corresponding to a Byzantine quorum"
)
parser.add_argument(
    "--phase_duration",
    type = int,
    default = 1,
    help = "Duration (in seconds) of one phase of the IBFT protocol round"
)
parser.add_argument(
    "--start_time",
    type = int,
    default = math.ceil(datetime.datetime.timestamp(datetime.datetime.now()))+2,
    help = "Start time (as UNIX timestamp) for the protocol"
)
parser.add_argument(
    "--port",
    type = int,
    default = 9000,
    help = "Port on which to start the Flask server"
)
