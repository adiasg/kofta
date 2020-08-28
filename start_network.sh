# $1 is the number of nodes in the network
NUM_NODES=$1
# $2 is the duration (in seconds) of each phase of the IBFT round
PHASE_DURATION=$2
# $3 is the number of nodes corresponding to a Byzantine quorum
BYZ_QUORUM=$3

START_TIME=$(( $(date '+%s') + 5 ))

for node_id in $(seq 1 $(( $NUM_NODES - 1 )))
do
  echo ./start_node_in_network.sh $NUM_NODES $node_id $START_TIME $PHASE_DURATION $BYZ_QUORUM \> /dev/null \&
  ./start_node_in_network.sh $NUM_NODES $node_id $START_TIME $PHASE_DURATION $BYZ_QUORUM > /dev/null &
done

trap "echo 'Interrupted. Killing all other IBFT processes.'; pgrep -f 'python3 ibft-simple.py' | xargs kill" INT

echo ./start_node_in_network.sh $NUM_NODES 0 $START_TIME $PHASE_DURATION $BYZ_QUORUM
./start_node_in_network.sh $NUM_NODES 0 $START_TIME $PHASE_DURATION $BYZ_QUORUM
