# $1 is the duration (in seconds) of each phase of the IBFT round
ROUND_DURATION=$1
# $2 is the drand round number on whose output to form consensus
DRAND_ROUND=$2

# $NUM_NODES is the number of nodes in the network
NUM_NODES=4
# $BYZ_QUORUM is the number of nodes corresponding to a Byzantine quorum
BYZ_QUORUM=3
# $RC_THRESHOLD is the weight of the ROUND_CHANGE threshold
RC_THRESHOLD=2

START_TIME=$(( $(date '+%s') + 5 ))

PORT_START_ADDR=10000
NODES="localhost:$PORT_START_ADDR"
for i in $(seq 1 $(( $NUM_NODES - 1 )))
do
  NODES="$NODES,localhost:$(( $PORT_START_ADDR + $i ))"
done

trap "echo 'Interrupted. Killing all IBFT processes.'; pkill -f 'python3 drand-consensus-worker.py|python3 flask-server.py'" INT

NODE_ID=1
echo python3 flask-server.py \
--node_identity $NODE_ID \
--port $(( $PORT_START_ADDR + $NODE_ID ))
python3 flask-server.py \
--node_identity $NODE_ID \
--port $(( $PORT_START_ADDR + $NODE_ID )) > /dev/null &
echo python3 drand-consensus-worker.py \
  --nodes $NODES \
  --node_identity $NODE_ID \
  --byz_quorum $BYZ_QUORUM \
  --rc_threshold $RC_THRESHOLD \
  --round_duration $ROUND_DURATION \
  --start_time $START_TIME \
  --drand_api https://api.drand.sh/public \
  --drand_round $DRAND_ROUND
python3 drand-consensus-worker.py \
  --nodes $NODES \
  --node_identity $NODE_ID \
  --byz_quorum $BYZ_QUORUM \
  --rc_threshold $RC_THRESHOLD \
  --round_duration $ROUND_DURATION \
  --start_time $START_TIME \
  --drand_api https://api.drand.sh/public \
  --drand_round $DRAND_ROUND > /dev/null &
#---------------------------------------------
NODE_ID=2
echo python3 flask-server.py \
--node_identity $NODE_ID \
--port $(( $PORT_START_ADDR + $NODE_ID ))
python3 flask-server.py \
--node_identity $NODE_ID \
--port $(( $PORT_START_ADDR + $NODE_ID )) > /dev/null &
echo python3 drand-consensus-worker.py \
  --nodes $NODES \
  --node_identity $NODE_ID \
  --byz_quorum $BYZ_QUORUM \
  --rc_threshold $RC_THRESHOLD \
  --round_duration $ROUND_DURATION \
  --start_time $START_TIME \
  --drand_api https://api2.drand.sh/public \
  --drand_round $DRAND_ROUND
python3 drand-consensus-worker.py \
  --nodes $NODES \
  --node_identity $NODE_ID \
  --byz_quorum $BYZ_QUORUM \
  --rc_threshold $RC_THRESHOLD \
  --round_duration $ROUND_DURATION \
  --start_time $START_TIME \
  --drand_api https://api2.drand.sh/public \
  --drand_round $DRAND_ROUND > /dev/null &
#---------------------------------------------
NODE_ID=3
echo python3 flask-server.py \
--node_identity $NODE_ID \
--port $(( $PORT_START_ADDR + $NODE_ID ))
python3 flask-server.py \
--node_identity $NODE_ID \
--port $(( $PORT_START_ADDR + $NODE_ID )) > /dev/null &
echo python3 drand-consensus-worker.py \
  --nodes $NODES \
  --node_identity $NODE_ID \
  --byz_quorum $BYZ_QUORUM \
  --rc_threshold $RC_THRESHOLD \
  --round_duration $ROUND_DURATION \
  --start_time $START_TIME \
  --drand_api https://api3.drand.sh/public \
  --drand_round $DRAND_ROUND
python3 drand-consensus-worker.py \
  --nodes $NODES \
  --node_identity $NODE_ID \
  --byz_quorum $BYZ_QUORUM \
  --rc_threshold $RC_THRESHOLD \
  --round_duration $ROUND_DURATION \
  --start_time $START_TIME \
  --drand_api https://api3.drand.sh/public \
  --drand_round $DRAND_ROUND > /dev/null &
#---------------------------------------------
NODE_ID=0
echo python3 flask-server.py \
--node_identity $NODE_ID \
--port $(( $PORT_START_ADDR + $NODE_ID ))
python3 flask-server.py \
--node_identity $NODE_ID \
--port $(( $PORT_START_ADDR + $NODE_ID )) > /dev/null &
echo python3 drand-consensus-worker.py \
  --nodes $NODES \
  --node_identity $NODE_ID \
  --byz_quorum $BYZ_QUORUM \
  --rc_threshold $RC_THRESHOLD \
  --round_duration $ROUND_DURATION \
  --start_time $START_TIME \
  --drand_api https://drand.cloudflare.com/public \
  --drand_round $DRAND_ROUND
python3 drand-consensus-worker.py \
  --nodes $NODES \
  --node_identity $NODE_ID \
  --byz_quorum $BYZ_QUORUM \
  --rc_threshold $RC_THRESHOLD \
  --round_duration $ROUND_DURATION \
  --start_time $START_TIME \
  --drand_api https://drand.cloudflare.com/public \
  --drand_round $DRAND_ROUND
