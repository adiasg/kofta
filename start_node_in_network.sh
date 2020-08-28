# $1 is the number of nodes in the network
NUM_NODES=$1
# $2 is the node_identity
NODE_ID=$2
# $3 is the start_time
START_TIME=$3
# $4 is the phase_duration
PHASE_DURATION=$4
# $5 is the byz_quorum
BYZ_QUORUM=$5

NODES="localhost:9000"
for i in $(seq 1 $(( $NUM_NODES - 1 )))
do
  NODES="$NODES,localhost:$(( 9000 + $i ))"
done

echo python3 ibft-simple.py \
  --nodes $NODES \
  --node_identity $NODE_ID \
  --store_id node$NODE_ID \
  --byz_quorum $BYZ_QUORUM \
  --phase_duration $PHASE_DURATION \
  --start_time $START_TIME \
  --port $(( 9000 + $NODE_ID ))

python3 ibft-simple.py \
  --nodes $NODES \
  --node_identity $NODE_ID \
  --store_id node$NODE_ID \
  --byz_quorum $BYZ_QUORUM \
  --phase_duration $PHASE_DURATION \
  --start_time $START_TIME \
  --port $(( 9000 + $NODE_ID ))
