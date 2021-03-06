# $1 is the number of nodes in the network
NUM_NODES=$1
# $2 is the duration (in seconds) of each phase of the IBFT round
ROUND_DURATION=$2
# $3 is the number of nodes corresponding to a Byzantine quorum
BYZ_QUORUM=$3
# $4 is the weight of the ROUND_CHANGE threshold
RC_THRESHOLD=$4

START_TIME=$(( $(date '+%s') + 5 ))

PORT_START_ADDR=10000
NODES="localhost:$PORT_START_ADDR"
for i in $(seq 1 $(( $NUM_NODES - 1 )))
do
  NODES="$NODES,localhost:$(( $PORT_START_ADDR + $i ))"
done

trap "echo 'Interrupted. Killing all IBFT processes.'; pkill -f 'python3 consensus-worker.py|python3 flask-server.py'" INT

for NODE_ID in $(seq 1 $(( $NUM_NODES - 1 )))
do
  echo python3 flask-server.py \
  --node_identity $NODE_ID \
  --port $(( $PORT_START_ADDR + $NODE_ID ))
  python3 flask-server.py \
  --node_identity $NODE_ID \
  --port $(( $PORT_START_ADDR + $NODE_ID )) &
  echo python3 consensus-worker.py \
    --nodes $NODES \
    --node_identity $NODE_ID \
    --byz_quorum $BYZ_QUORUM \
    --rc_threshold $RC_THRESHOLD \
    --round_duration $ROUND_DURATION \
    --start_time $START_TIME
  python3 consensus-worker.py \
    --nodes $NODES \
    --node_identity $NODE_ID \
    --byz_quorum $BYZ_QUORUM \
    --rc_threshold $RC_THRESHOLD \
    --round_duration $ROUND_DURATION \
    --start_time $START_TIME &
done

echo python3 flask-server.py \
--node_identity 0 \
--port $(( $PORT_START_ADDR + 0 ))
python3 flask-server.py \
--node_identity 0 \
--port $(( $PORT_START_ADDR + 0 )) &
echo python3 consensus-worker.py \
  --nodes $NODES \
  --node_identity 0 \
  --byz_quorum $BYZ_QUORUM \
  --rc_threshold $RC_THRESHOLD \
  --round_duration $ROUND_DURATION \
  --start_time $START_TIME
python3 consensus-worker.py \
  --nodes $NODES \
  --node_identity 0 \
  --byz_quorum $BYZ_QUORUM \
  --rc_threshold $RC_THRESHOLD \
  --round_duration $ROUND_DURATION \
  --start_time $START_TIME
