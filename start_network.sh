# $1 is the number of nodes in the network
NUM_NODES=$1
# $2 is the duration (in seconds) of each phase of the IBFT round
ROUND_DURATION=$2
# $3 is the number of nodes corresponding to a Byzantine quorum
BYZ_QUORUM=$3
# $4 is the weight of the ROUND_CHANGE threshold
RC_THRESHOLD=$4

START_TIME=$(( $(date '+%s') + 5 ))

NODES="localhost:9000"
for i in $(seq 1 $(( $NUM_NODES - 1 )))
do
  NODES="$NODES,localhost:$(( 9000 + $i ))"
done

for NODE_ID in $(seq 1 $(( $NUM_NODES - 1 )))
do
  echo python3 flask-server.py \
  --node_identity $NODE_ID \
  --port $(( 9000 + $NODE_ID ))
  python3 flask-server.py \
  --node_identity $NODE_ID \
  --port $(( 9000 + $NODE_ID )) > /dev/null &
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
    --start_time $START_TIME > /dev/null &
done

trap "echo 'Interrupted. Killing all other IBFT processes.'; pkill -f 'python3 consensus-worker.py|python3 flask-server.py'" INT

echo python3 flask-server.py \
--node_identity 0 \
--port $(( 9000 + 0 ))
python3 flask-server.py \
--node_identity 0 \
--port $(( 9000 + 0 )) > /dev/null &
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
