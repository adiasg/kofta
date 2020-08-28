START_TIME=$(( $(date '+%s') + 2 ))

echo python3 ibft-drand.py --nodes localhost:9000,localhost:9001,localhost:9002,localhost:9003 --node_identity 1 --store_id node1 --byz_quorum 3 --phase_duration 2 --start_time $START_TIME --port 9001 --drand_source https://api.drand.sh/public \> /dev/null \&
python3 ibft-drand.py --nodes localhost:9000,localhost:9001,localhost:9002,localhost:9003 --node_identity 1 --store_id node1 --byz_quorum 3 --phase_duration 2 --start_time $START_TIME --port 9001 > /dev/null &

echo python3 ibft-drand.py --nodes localhost:9000,localhost:9001,localhost:9002,localhost:9003 --node_identity 2 --store_id node2 --byz_quorum 3 --phase_duration 2 --start_time $START_TIME --port 9002 --drand_source https://api2.drand.sh/public \> /dev/null \&
python3 ibft-drand.py --nodes localhost:9000,localhost:9001,localhost:9002,localhost:9003 --node_identity 2 --store_id node2 --byz_quorum 3 --phase_duration 2 --start_time $START_TIME --port 9002 > /dev/null &

echo python3 ibft-drand.py --nodes localhost:9000,localhost:9001,localhost:9002,localhost:9003 --node_identity 3 --store_id node3 --byz_quorum 3 --phase_duration 2 --start_time $START_TIME --port 9003 --drand_source https://api3.drand.sh/public \> /dev/null \&
python3 ibft-drand.py --nodes localhost:9000,localhost:9001,localhost:9002,localhost:9003 --node_identity 3 --store_id node3 --byz_quorum 3 --phase_duration 2 --start_time $START_TIME --port 9003 > /dev/null &

trap "echo 'Interrupted. Killing all other IBFT processes.'; pgrep -f 'python3 ibft-drand.py' | xargs kill" INT

echo python3 ibft-drand.py --nodes localhost:9000,localhost:9001,localhost:9002,localhost:9003 --node_identity 0 --store_id node0 --byz_quorum 3 --phase_duration 2 --start_time $START_TIME --port 9000 --drand_source https://drand.cloudflare.com/public
python3 ibft-drand.py --nodes localhost:9000,localhost:9001,localhost:9002,localhost:9003 --node_identity 0 --store_id node0 --byz_quorum 3 --phase_duration 2 --start_time $START_TIME --port 9000 --drand_source https://drand.cloudflare.com/public
