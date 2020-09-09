from consensus import Consensus, ConsensusMessage
import httpx
import logging

log = logging.getLogger(__name__)

class DrandConsensus(Consensus):
    def __init__(self, nodes, byz_quorum, rc_threshold, round_duration, start_time, store, node_identity=None, drand_api='https://drand.cloudflare.com/public', drand_round=1):
        self.drand_api = drand_api
        self.drand_round = drand_round
        url = self.drand_api+'/'+str(self.drand_round)
        response = httpx.get(url, timeout=2)
        if response.status_code != 200:
            log.warn(f'Failed GET from {url}, response status code: {response.status_code}')
        response_json = response.json()
        self.drand_value = response_json['randomness']
        super().__init__(nodes, byz_quorum, rc_threshold, round_duration, start_time, store, node_identity=node_identity)

    def get_drand_value(self):
        return self.drand_value

    def create_proposal(self, value=None, justification=[]):
        round = self.store.get_round()
        data = {}
        if value is None:
            data['value'] = self.get_drand_value()
        else:
            data['value'] = value
        data['justification'] = justification
        sender = self.node_identity
        return ConsensusMessage("PRE_PREPARE", round, data, sender)

    def validate_message_data(self, data):
        assert type(data['value']) == str, "Incorrect type for message data"
        return data['value'] == self.get_drand_value()
