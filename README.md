# kofta

An :heavy_exclamation_mark: ***experimental & WIP*** :heavy_exclamation_mark: implementation of the IBFT consensus protocol, written in Python. Uses Flask for networking, and Redis for storage.

This implementation is based on [EIP 650](https://github.com/ethereum/EIPs/issues/650).

## Requirements
- Python3
- Redis
  - Installing on Ubuntu:
    ```bash
      sudo apt install redis-server
      sudo systemctl start redis
    ```

## Installation
Run `make install` in the root directory of this repository.

## Testing
### ibft-simple.py
- To run a single node network, run:
  ```bash
  python3 ibft-simple.py \
    --nodes localhost:9000 \
    --node_identity 0 \
    --store_id node0 \
    --byz_quorum 1 \
    --phase_duration 1 \
    --start_time $(( $(date '+%s') + 2 )) \
    --port 9000
  ```

- To launch a testnet, run `./start_network.sh NUM_NODES PHASE_DURATION BYZ_QUORUM`, where:
  - `NUM_NODES` is the number of nodes in the network
  - `PHASE_DURATION` is the duration (in seconds) of each phase of the IBFT protocol round
  - `BYZ_QUORUM` is the number of nodes corresponding to a Byzantine quorum

  Only the output from the leader node's process will be displayed in the current terminal, and all other node's processes will run silently in the background. To exit, press `CTRL+C`, which will kill all spawned IBFT processes.

### ibft-drand.py
- In each round of this example, the IBFT protocol will form consensus over drand randomness for the IBFT round number. Eg. IBFT round 1 forms consensus over randomness for drand round 1, and so on.
- To launch a 4-node testnet, run `./start_drand_network.sh`
- There are 4 public HTTP endpoints to access drand randomness. The leader uses the first, and the other 3 nodes each use one of the rest:
  - (Cloudflare) https://drand.cloudflare.com/
  - (Protocol Labs) https://api.drand.sh
  - (Protocol Labs) https://api2.drand.sh
  - (Protocol Labs) https://api3.drand.sh
- Learn more about **drand** at https://drand.love/
