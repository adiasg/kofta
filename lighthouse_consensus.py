from consensus import Consensus, ConsensusMessage
import httpx
import logging

log = logging.getLogger(__name__)

class LighthouseConsensus(Consensus):
    def __init__(self, nodes, byz_quorum, rc_threshold, round_duration, start_time, store, node_identity=None, lighthouse_api='http://localhost:5052', eth2_slot=1):
        self.lighthouse_api = lighthouse_api
        self.eth2_slot = eth2_slot
        url = self.lighthouse_api + '/beacon/block'
        params = {'slot': self.eth2_slot}
        headers = {'Accept': 'application/json'}
        try:
            response = httpx.get(url, params=params, headers=headers, timeout=2)
            if response.status_code != 200:
                log.warn(f'Failed GET from {url}, response status code: {response.status_code}')
            response_json = response.json()
            self.lighthouse_value = f'slot{self.eth2_slot}:{response_json["root"]}'
        except:
            log.error(f'Lighthouse request to {url} failed', exc_info=True)

        super().__init__(nodes, byz_quorum, rc_threshold, round_duration, start_time, store, node_identity=node_identity)

    def get_lighthouse_value(self):
        return self.lighthouse_value

    def create_proposal(self, value=None, justification=[]):
        round = self.store.get_round()
        data = {}
        if value is None:
            data['value'] = self.get_lighthouse_value()
        else:
            data['value'] = value
        data['justification'] = justification
        sender = self.node_identity
        return ConsensusMessage("PRE_PREPARE", round, data, sender)

    def validate_message_data(self, data):
        assert type(data['value']) == str, "Incorrect type for message data"
        return data['value'] == self.get_lighthouse_value()
