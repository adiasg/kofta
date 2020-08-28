import redis
import json
import httpx
import datetime
import math
import time

class ConsensusNode:
    def __init__(self, node_index, weight=1, public_key=""):
        self.node_index = node_index
        self.weight = weight
        self.public_key = public_key

class ConsensusMessage:
    def __init__(self, type, round, data, sender, signature=""):
        # `type` can be "PRE_PREPARE", "PREPARE", "COMMIT", "ROUND_CHANGE"
        self.type = type
        self.round = int(round)
        self.data = data
        self.sender = int(sender)
        self.siganture = signature

    def verify_signature(self):
        # TODO: Implement siganture verification
        return True

    def to_dict(self):
        return {
            'type': self.type,
            'round': self.round,
            'data': self.data,
            'sender': self.sender,
            'siganture': self.siganture
        }

    def to_string(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(self, d):
        # TODO: Validate the dict `d`
        return ConsensusMessage(
                d['type'],
                d['round'],
                d['data'],
                d['sender'],
                d['siganture']
        )

    @classmethod
    def from_string(self, s):
        return ConsensusMessage.from_dict(json.loads(s))

class ConsensusStore:
    def __init__(self, id_string):
        self.redis = redis.Redis()
        # Prefix the redis keys for this store with `id_string`
        self.id_string = id_string + ":"
        # Delete all pre-existing keys with this prefix
        for key in self.redis.scan_iter(self.id_string+'*'):
            self.redis.delete(key)

    def prepare_key(self, key):
        return self.id_string + key

    def set_state(self, state):
        self.redis.set(self.prepare_key('state'), state)

    def get_state(self):
        return self.redis.get(self.prepare_key('state')).decode('utf-8')

    def set_round(self, round):
        # `round` can be "NEW_ROUND", "PRE_PREPARED", "PREPARED", "COMMITTED", "FINAL_COMMITTED", "ROUND_CHANGE"
        self.redis.set(self.prepare_key('round'), round)

    def get_round(self):
        return int(self.redis.get(self.prepare_key('round')).decode('utf-8'))

    def set_leader(self, node_index):
        self.redis.set(self.prepare_key('leader'), node_index)

    def get_leader(self):
        return int(self.redis.get(self.prepare_key('leader')).decode('utf-8'))

    def get_messages(self, round, type):
        key = 'round'+str(round)+":"+type
        set_members = self.redis.smembers(self.prepare_key(key))
        return [ConsensusMessage.from_string(s.decode('utf-8')) for s in set_members]

    def add_message(self, consensus_message):
        key = 'round'+str(consensus_message.round)+':'+consensus_message.type
        self.redis.sadd(self.prepare_key(key), consensus_message.to_string())

    def get_peers(self):
        return [peer.decode('utf-8') for peer in self.redis.smembers(self.prepare_key('peers'))]

    def add_peer(self, peer_ip):
        self.redis.sadd(self.prepare_key('peers'), peer_ip)

"""
async def post(url, post_json):
    timeout = aiohttp.ClientTimeout(total=0.7)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=post_json) as response:
            return response
"""

def broadcast_message(msg, peers):
    # TODO: Move broadcast_message to the networking layer
    msg_dict = msg.to_dict()
    # TODO: POST in an async, parallel manner
    """
    loop = asyncio.get_event_loop()
    coroutines = [post('http://'+peer_ip+'/messages', msg) for peer_ip in peers]
    results = loop.run_until_complete(asyncio.gather(*coroutines))
    for i in range(len(results)):
        if results[i].status != 200:
            print("Failed POST to", 'http://'+peers[i]+'/messages', msg, ", reponse status code:", results[i].status)
    """
    for peer in peers:
        url = 'http://'+peer+'/messages'
        try:
            response = httpx.post(url, json=msg_dict, timeout=0.2)
            if response.status_code != 200:
                print("Failed POST to", 'http://'+peer+'/messages', ", reponse status code:", response.status_code)
        except httpx.ConnectError as e:
            print("Failed POST to", 'http://'+peer+'/messages', ", httpx.ConnectError:", e)

class Consensus:
    def __init__(self, nodes, byz_quorum, round_duration, start_time, store, node_identity=None):
        # `nodes` is a dict that maps node_index -> ConsensusNode
        self.nodes = nodes
        self.byz_quorum = byz_quorum
        # `round_duration` is of type datetime.timedelta
        # Each phase of the round runs for time `round_duration/5`
        self.round_duration = round_duration
        # `start_time` is of type datetime.datetime
        self.start_time = start_time
        self.store = store
        # if this node is a participant in consensus, then `node_identity` is the `node_index` corresponding to this node. Else, it is None.
        self.node_identity = node_identity
        self.N = len(nodes)
        self.store.set_leader(0)
        self.store.set_round(0)
        self.store.set_state("NEW_ROUND")
        """
        If `leader_start_in_NEW_ROUND` is set, then the leader should execute
        state_transition in ROUND_CHANGE twice: in the beginning to broadcast
        PRE_PREPARE, and in the end to validate PRE_PREPARE as a normal node.
        """
        self.leader_start_in_NEW_ROUND = True

    def leader_change(self):
        # TODO: Implement leader change functionality
        pass

    def receive_message(self, message):
        # TODO: Verify signatures & timing before calling this
        self.store.add_message(message)

    def create_proposal(self):
        round = self.store.get_round()
        # NOTE: Set `data` according to application-specific logic
        data = round
        sender = self.node_identity
        return ConsensusMessage("PRE_PREPARE", round, data, sender)

    def broadcast_round_change(self):
        round = self.store.get_round()
        data = None
        sender = self.node_identity
        rc_message = ConsensusMessage("ROUND_CHANGE", round, data, sender)
        broadcast_message(rc_message, self.store.get_peers())

    def validate_message_data(self, message):
        # NOTE: Verify `message.data` according to application-specific logic by checking against local state
        return message.data == self.store.get_round()

    def validate_proposal_message(self, message):
        # Assert will fail if the message is not well-formed
        assert message.sender == self.store.get_leader(), "Incorrect sender for PRE_PREPARE message"
        assert message.round == self.store.get_round(), "Incorrect round for PRE_PREPARE message"
        assert message.type == "PRE_PREPARE", "Incorrect message type for PRE_PREPARE message"
        assert message.verify_signature(), "Incorrect siganture for PRE_PREPARE message"
        return self.validate_message_data(message)

    def validate_prepare_message(self, message):
        # Assert will fail if the message is not well-formed
        assert message.sender in self.nodes, "Unknown sender for PREPARE message"
        assert message.round == self.store.get_round(), "Incorrect round for PREPARE message"
        assert message.type == "PREPARE", "Incorrect message type for PREPARE message"
        assert message.verify_signature(), "Incorrect siganture for PREPARE message"
        return self.validate_message_data(message)

    def validate_commit_message(self, message):
        # Assert will fail if the message is not well-formed
        assert message.sender in self.nodes, "Unknown sender for COMMIT message"
        assert message.round == self.store.get_round(), "Incorrect round for COMMIT message"
        assert message.type == "COMMIT", "Incorrect message type for COMMIT message"
        assert message.verify_signature(), "Incorrect siganture for COMMIT message"
        return self.validate_message_data(message)

    """
    def validate_round_change_message(self, message):
        # Assert will fail if the message is not well-formed
        assert message.sender in self.nodes, "Unknown sender for ROUND_CHANGE message"
        assert message.round == self.store.get_round(), "Incorrect round for ROUND_CHANGE message"
        assert message.type == "ROUND_CHANGE", "Incorrect message type for ROUND_CHANGE message"
        assert message.verify_signature(), "Incorrect siganture for ROUND_CHANGE message"
        return True
    """

    def state_transition(self):
        state = self.store.get_state()
        print("----------------------")
        print(datetime.datetime.now().time(), "state_transition with state:", state)

        if state == "NEW_ROUND":
            firing_time = datetime.datetime.now()
            if self.leader_start_in_NEW_ROUND and self.store.get_leader() == self.node_identity:
                # NOTE: Leader executes in NEW_ROUND twice if `self.leader_start_in_NEW_ROUND` is set
                # Once in the beginning of NEW_ROUND to broadcast PRE_PREPARE
                # Second time at the end of NEW_ROUND to validate PRE_PREPARE as a normal node

                if (firing_time-self.start_time)%(self.round_duration) > (self.round_duration/5)/10:
                    # After ROUND_CHANGE, wait for the right time to begin the new round
                    print("[LEADER] Not the right phase for NEW_ROUND. Difference (abs.) from expected firing time:", (firing_time-self.start_time)%(self.round_duration))
                    return

                self.leader_start_in_NEW_ROUND = False
                proposal = self.create_proposal()
                broadcast_message(proposal, self.store.get_peers())
                return
            else:
                if (firing_time-self.round_duration/5-self.start_time)%(self.round_duration) > (self.round_duration/5)/10:
                    # After ROUND_CHANGE, wait for the right time to begin the new round
                    print("Not the right phase for NEW_ROUND. Difference (abs.) from expected firing time:", (firing_time-self.round_duration/5-self.start_time))
                    return

            # All nodes (including leader) validate the proposal
            try:
                proposals = self.store.get_messages(self.store.get_round(), "PRE_PREPARE")
                assert len(proposals) > 0, "No proposal was received"
                # TODO: Checking multiple proposals may not be necessary. If consensus is still formed, then this type of Byzantine behavior can be ignored.
                assert len(proposals) == 1, "Multiple proposals were recieved"
                assert self.validate_proposal_message(proposals[0]), "Proposal failed validation"

                # Proposal was successfully validated, go to "PRE_PREPARED"
                self.store.set_state("PRE_PREPARED")
                if self.node_identity is not None:
                    round = self.store.get_round()
                    # TODO: Save the proposal data in the store separately
                    data = proposals[0].data
                    sender = self.node_identity
                    prepare_message = ConsensusMessage("PREPARE", round, data, sender)
                    broadcast_message(prepare_message, self.store.get_peers())

            except AssertionError as e:
                # Something failed, go to round change
                print("Round failed. Error:", e)
                self.store.set_state("ROUND_CHANGE")
                if self.node_identity is not None:
                    self.broadcast_round_change()
        #-----------------------------------------------------------------------
        elif state == "PRE_PREPARED":
            try:
                prepare_msgs = self.store.get_messages(self.store.get_round(), "PREPARE")
                supporting_weight = 0
                for msg in prepare_msgs:
                    try:
                        if self.validate_prepare_message(msg):
                            supporting_weight += self.nodes[msg.sender].weight
                    except AssertionError as e:
                        # `msg` was not well-formed
                        print("validate_prepare_message failed. Error:", e)
                        pass
                # If we haven't seen a supporting weight of `self.byz_quorum`, then this round has timed out.
                assert supporting_weight >= self.byz_quorum, "Sufficient PREPARE messages not seen"

                self.store.set_state("PREPARED")
                if self.node_identity is not None:
                    # This node is a consensus participant. Send COMMIT for the proposal from this round.
                    round = self.store.get_round()
                    # TODO: Retreive the proposal data from a separate entry in the store
                    proposals = self.store.get_messages(self.store.get_round(), "PRE_PREPARE")
                    data = proposals[0].data
                    sender = self.node_identity
                    prepare_message = ConsensusMessage("COMMIT", round, data, sender)
                    broadcast_message(prepare_message, self.store.get_peers())

            except AssertionError as e:
                # This round has timed out, go to round change
                print("Round timed out. Error:", e)
                self.store.set_state("ROUND_CHANGE")
                if self.node_identity is not None:
                    self.broadcast_round_change()
        #-----------------------------------------------------------------------
        elif state == "PREPARED":
            try:
                commit_msgs = self.store.get_messages(self.store.get_round(), "COMMIT")
                supporting_weight = 0
                for msg in commit_msgs:
                    try:
                        if self.validate_commit_message(msg):
                            supporting_weight += self.nodes[msg.sender].weight
                    except AssertionError as e:
                        # `msg` was not well-formed
                        print("validate_commit_message failed. Error:", e)
                        pass
                # If we haven't seen a supporting weight of `self.byz_quorum`, then this round has timed out.
                assert supporting_weight >= self.byz_quorum, "Sufficient COMMIT messages not seen"

                self.store.set_state("COMMITTED")

            except AssertionError as e:
                # This round has timed out, go to round change
                print("Round timed out. Error:", e)
                self.store.set_state("ROUND_CHANGE")
                if self.node_identity is not None:
                    self.broadcast_round_change()
        #-----------------------------------------------------------------------
        elif state == "COMMITTED":
            self.store.set_state("FINAL_COMMITTED")
        #-----------------------------------------------------------------------
        elif state == "FINAL_COMMITTED":
            self.store.set_state("NEW_ROUND")
            round = self.store.get_round()
            self.store.set_round(round+1)
            if self.store.get_leader() == self.node_identity and not self.leader_start_in_NEW_ROUND:
                proposal = self.create_proposal()
                broadcast_message(proposal, self.store.get_peers())
        #-----------------------------------------------------------------------
        elif state == "ROUND_CHANGE":
            # TODO: Implement round change
            self.store.set_state("NEW_ROUND")
            round = self.store.get_round()
            self.store.set_round(round+1)
            self.leader_start_in_NEW_ROUND = True
            # assert False, "In ROUND_CHANGE state, logic is unimplemented"
        #-----------------------------------------------------------------------
        else:
            assert False, "In an unknown state: "+str(state)
