# kofta

An :heavy_exclamation_mark: ***experimental & WIP*** :heavy_exclamation_mark: implementation of the IBFT consensus protocol, written in Python.

This implementation is based on [the Istanbul BFT Consensus Algorithm](https://arxiv.org/abs/2002.03613).

## Requirements
- Python3
  - Run `make deps` to install all the required Python packages
- RabbitMQ Server
  - Installing on Ubuntu:
    ```bash
      sudo apt-get install rabbitmq-server
    ```

## Examples

- **Even number consensus**
  - The base `Consensus` class attempts to form consensus on *some* even number
  - To launch a testnet of the base `Consensus` class, run `./start_network.sh NUM_NODES ROUND_DURATION BYZ_QUORUM RC_THRESHOLD`, where:
    - `NUM_NODES` is the number of nodes in the network
    - `ROUND_DURATION` is the duration (in seconds) of the IBFT protocol round
    - `BYZ_QUORUM` is the number of nodes corresponding to a Byzantine quorum
    - `RC_THRESHOLD` is the number of nodes corresponding to a round change threshold


- **drand consensus**
  - The IBFT protocol will form consensus over drand randomness for a given drand round number
  - To launch a 4-node testnet, run `./start_drand_network.sh ROUND_DURATION DRAND_ROUND`, where:
    - `ROUND_DURATION` is the duration (in seconds) of the IBFT protocol round
    - `DRAND_ROUND` is the drand round number on whose output consensus will be formed
  - There are 4 public HTTP endpoints to access drand randomness. The leader uses the first, and the other 3 nodes each use one of the rest:
    - (Cloudflare) https://drand.cloudflare.com
    - (Protocol Labs) https://api.drand.sh
    - (Protocol Labs) https://api2.drand.sh
    - (Protocol Labs) https://api3.drand.sh
  - Learn more about **drand** at https://drand.love/


- **Lighthouse Eth2 data consensus**
  - The IBFT protocol will form consensus over Eth2 data fetched from a Lighthouse client
  - To launch a testnet, run `./start_lighthouse_network.sh NUM_NODES ROUND_DURATION BYZ_QUORUM RC_THRESHOLD LIGHTHOUSE_API ETH2_SLOT`, where:
    - `LIGHTHOUSE_API` is the Ligthouse HTTP endpoint for fetching data
    - `ETH2_SLOT` is the Eth2 slot for which consensus will be formed on the corresponding block in the fork choice of the Lighthouse client
