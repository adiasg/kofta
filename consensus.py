import json
import httpx
import datetime
import math
import time
import logging

log = logging.getLogger(__name__)

class ConsensusNode:
    def __init__(self, node_index, weight=1, public_key=""):
        self.node_index = node_index
        self.weight = weight
        self.public_key = public_key

class ConsensusMessage:
    def __init__(self, type: str, round: int, data, sender: int, signature=""):
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
        d = {
            'type': self.type,
            'round': self.round,
            'sender': self.sender,
            'siganture': self.siganture
        }
        d['data'] = {}
        d['data']['justification'] = []
        for key in self.data:
            if key == 'justification':
                for msg in self.data['justification']:
                    d['data']['justification'].append(msg.to_dict())
            else:
                d['data'][key] = self.data[key]
        return d

    def to_string(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        # Useful for printing the object directly
        return self.to_string()

    @classmethod
    def from_dict(self, d):
        # TODO: Validate the dict `d`
        data = {}
        data['justification'] = []
        for key in d['data']:
            if key == 'justification':
                for msg in d['data']['justification']:
                    data['justification'].append(ConsensusMessage.from_dict(msg))
            else:
                data[key] = d['data'][key]
        return ConsensusMessage(
                d['type'],
                d['round'],
                data,
                d['sender'],
                d['siganture']
        )

    @classmethod
    def from_string(self, s):
        return ConsensusMessage.from_dict(json.loads(s))


class ConsensusStore:
    def __init__(self, node_id, peers):
        self.node_id = node_id
        self.peers = peers
        self.state = "PRE_PREPARED"
        self.round = 1
        self.prepared_round = 0
        self.prepared_value = None
        self.decided_value = None
        self.leader = 0
        self.messages = {}
        self.quorum_messages = {}

    def set_state(self, state: str):
        assert state in ["PRE_PREPARED", "PREPARED", "COMMITTED", "DECIDED", "ROUND_TIMEOUT", "ROUND_CHANGED"], "Setting unknown state:"+str(state)
        self.state = state

    def get_state(self):
        return self.state

    def set_round(self, round: int):
        self.round = round

    def get_round(self):
        return self.round

    def set_prepared_round(self, prepared_round: int):
        self.prepared_round = prepared_round

    def get_prepared_round(self):
        return self.prepared_round

    def set_prepared_value(self, prepared_value):
        self.prepared_value = prepared_value

    def get_prepared_value(self):
        return self.prepared_value

    def set_decided_value(self, decided_value):
        self.decided_value = decided_value

    def get_decided_value(self):
        return self.decided_value

    def set_leader(self, leader: int):
        self.leader = leader

    def get_leader(self):
        return self.leader

    def add_message(self, message: ConsensusMessage):
        round, type, sender = message.round, message.type, message.sender
        if round not in self.messages:
            self.messages[round] = {}
        if type not in self.messages[round]:
            self.messages[round][type] = []
        # Insert only one message of each type from each sender for each round
        if any(existing_message.sender==sender for existing_message in self.messages[round][type]):
            return False
        self.messages[round][type].append(message)
        return True


    def get_messages(self, round: int, type: str):
        if round in self.messages and type in self.messages[round]:
            return self.messages[round][type]
        return []

    def add_quorum_messages(self, round: int, type: str, messages):
        # type can be PREPARE_QUORUM or COMMIT_QUORUM
        if round not in self.quorum_messages:
            self.quorum_messages[round] = {}
        if type not in self.quorum_messages[round]:
            self.quorum_messages[round][type] = []
        assert self.quorum_messages[round][type] == [], "Trying to add quorum messages again:" + type + "for round:" + str(round)
        self.quorum_messages[round][type] = messages

    def get_quorum_messages(self, round: int, type: str):
        # type can be PREPARE_QUORUM or COMMIT_QUORUM
        if round in self.quorum_messages and type in self.quorum_messages[round]:
            return self.quorum_messages[round][type]
        return []

    def get_peers(self):
        return self.peers

def broadcast_message(msg, peers, timeout=1):
    # TODO: Move broadcast_message to the networking layer
    # TODO: POST in an async manner
    msg_dict = msg.to_dict()
    for peer in peers:
        url = 'http://'+peer+'/messages'
        try:
            log.info(f'Sending message to {peer}, message: {msg_dict}')
            response = httpx.post(url, json=msg_dict, timeout=timeout)
            if response.status_code != 200:
                log.warn(f'Failed POST to http://{peer}/messages, response status code: {response.status_code}')
        except httpx.ConnectError as e:
            log.error(f'Failed POST to http://{peer}/messages', exc_info=True)

class Consensus:
    def __init__(self, nodes, byz_quorum, rc_threshold, round_duration, start_time, store, node_identity=None):
        # `nodes` is a dict that maps node_index -> ConsensusNode
        self.nodes = nodes
        self.byz_quorum = byz_quorum
        self.rc_threshold = rc_threshold
        # `round_duration` is of type datetime.timedelta
        # Each phase of the round runs for time `round_duration/4`
        self.round_duration = round_duration
        # `start_time` is of type datetime.datetime
        self.start_time = start_time
        self.store = store
        # If this node is a participant in consensus, then `node_identity` is the `node_index` corresponding to this node. Else, it is None.
        self.node_identity = node_identity
        # Node 0 is the first leader
        self.store.set_leader(0)
        # Round 1 is the first round
        self.store.set_round(1)
        self.store.set_prepared_round(0)
        self.store.set_state("PRE_PREPARED")

    def create_proposal(self, value=None, justification=[]):
        round = self.store.get_round()
        # NOTE: Set `data` according to application-specific logic
        data = {}
        if value is None:
            data['value'] = 2*round
        else:
            data['value'] = value
        data['justification'] = justification
        sender = self.node_identity
        return ConsensusMessage("PRE_PREPARE", round, data, sender)

    def broadcast_proposal(self, value=None, justification=[]):
        broadcast_message(self.create_proposal(value, justification), self.store.get_peers())

    def broadcast_round_change(self):
        round = self.store.get_round()
        data = {}
        data['prepared_value'] = self.store.get_prepared_value()
        data['prepared_round'] = self.store.get_prepared_round()
        data['justification'] = self.store.get_quorum_messages(data['prepared_round'], "PREPARE_QUORUM")
        sender = self.node_identity
        rc_message = ConsensusMessage("ROUND_CHANGE", round, data, sender)
        broadcast_message(rc_message, self.store.get_peers())

    def round_timeout(self):
        log.info('Round timeout')
        current_round = self.store.get_round()
        self.store.set_round(current_round + 1)
        self.store.set_state("ROUND_TIMEOUT")
        self.broadcast_round_change()

    def validate_message_data(self, data):
        # NOTE: Verify the message data according to application-specific logic by checking against local state
        assert type(data['value']) == int, "Incorrect type for message data"
        return data['value']%2 == 0

    def validate_pre_prepare_message(self, message, round):
        # Assert will fail if the message is not well-formed
        # TODO: Make function to get leader from current round
        assert message.sender == self.store.get_leader(), "Incorrect sender for PRE_PREPARE message"
        assert message.round == round, "Incorrect round for PRE_PREPARE message"
        assert message.type == "PRE_PREPARE", "Incorrect message type for PRE_PREPARE message"
        assert message.verify_signature(), "Incorrect siganture for PRE_PREPARE message"
        assert self.validate_message_data(message.data), "Invalid data for PRE_PREPARE message"
        # FIXME: Shift all this into justify_pre_prepare. Implement that correctly.
        assert self.justify_pre_prepare(message, round), "justify_pre_prepare failed for PRE_PREPARE message"
        return True


    def validate_prepare_message(self, message, round):
        # Assert will fail if the message is not well-formed
        assert message.type == "PREPARE", "Incorrect message type for PREPARE message"
        assert message.sender in self.nodes, "Unknown sender for PREPARE message"
        assert message.round == round, "Incorrect round for PREPARE message"
        assert message.verify_signature(), "Incorrect siganture for PREPARE message"
        assert self.validate_message_data(message.data), "Invalid data for PREPARE message"
        return True


    def validate_commit_message(self, message, round):
        # Assert will fail if the message is not well-formed
        assert message.type == "COMMIT", "Incorrect message type for COMMIT message"
        assert message.sender in self.nodes, "Unknown sender for COMMIT message"
        assert message.round == round, "Incorrect round for COMMIT message"
        assert message.verify_signature(), "Incorrect siganture for COMMIT message"
        assert self.validate_message_data(message.data), "Invalid data for COMMIT message"
        return True

    def validate_round_change_message(self, message, round):
        # Assert will fail if the message is not well-formed
        assert message.type == "ROUND_CHANGE", "Incorrect message type for ROUND_CHANGE message"
        assert message.sender in self.nodes, "Unknown sender for ROUND_CHANGE message"
        assert message.round == round, "Incorrect round for ROUND_CHANGE message"
        assert 'prepared_round' in message.data and 'prepared_value' in message.data, "Incorrect data for ROUND_CHANGE message"
        assert type(message.data['prepared_round']) == int, "Incorrect type for prepared_round in ROUND_CHANGE message"
        assert message.data['prepared_round'] >= 0 and message.data['prepared_round'] < message.round, "0 <= prepared_round < round failed for ROUND_CHANGE message"
        assert message.verify_signature(), "Incorrect siganture for ROUND_CHANGE message"
        if message.data['prepared_round'] > 0 or message.data['prepared_value'] is not None:
            # TODO: The two conditions in the IF statement should both happen together, or none at all
            # Validate the justification of the message
            justification = [ConsensusMessage.from_dict(p_msg) for p_msg in message.data['justification']]
            prepare_message_quorum = 0
            seen_node = [False for node_id in self.nodes]
            for prepare_message in justification:
                assert not seen_node[prepare_message.sender], "Second message from same sender in the justification of ROUND_CHANGE message"
                assert prepare_message.value == message.data['prepared_value'], "Value of prepared message in justification is not prepared value in ROUND_CHANGE message"
                assert self.validate_prepare_message(prepare_message, message.data['prepared_round']), "validate_prepare_message failed for message in justification of ROUND_CHANGE message"
                seen_node[prepare_message.sender] = True
                prepare_message_quorum += self.nodes[prepare_message.sender].weight
            assert prepare_message_quorum >= self.byz_quorum, "Quorum weight not met by the justification of ROUND_CHANGE message"
        return True

    def justify_round_change(self, q_rc, round):
        rc_message_quorum = 0
        seen_node = [False for node_id in self.nodes]
        for rc_message in q_rc:
            assert not seen_node[rc_message.sender], "Second message from same sender in a quorum of ROUND_CHANGE messages"
            assert self.validate_round_change_message(rc_message, round), "ROUND_CHANGE message in quorum is not valid"
            seen_node[rc_message.sender] = True
            rc_message_quorum += self.nodes[rc_message.sender].weight
        if rc_message_quorum < self.byz_quorum:
            return False

        # The remaining logic is already covered in validate_round_change_message of the ROUND_CHANGE message in `q_rc` with highest prepared round
        return True

    def justify_pre_prepare(self, message, round):
        if message.round > 1:
            justification = message.data['justification']
            rc_message_quorum = 0
            rc_seen_node = [False for node_id in self.nodes]
            for rc_message in justification:
                # validate_round_change_message will also check that the rc_message is from round `message.round`
                assert not rc_seen_node[rc_message.sender], "Second ROUND_CHANGE message from same sender in the justification of PRE_PREPARE message"
                assert self.validate_round_change_message(rc_message, message.round), "ROUND_CHANGE message in justification of PRE_PREPARE is not valid"
                rc_seen_node[rc_message.sender] = True
                rc_message_quorum += self.nodes[rc_message.sender].weight
            assert rc_message_quorum >= self.byz_quorum, "Justification of PRE_PREPARE message does not satisfy the Byazntine threshold"

            highest_pr_rc_message = max(justification, key=lambda rc_msg: rc_msg.data['prepared_round'])
            if highest_pr_rc_message.data['prepared_round'] > 0 or highest_pr_rc_message.data['prepared_value'] is not None:
                # TODO: The two conditions in the IF statement should both happen together, or none at all
                p_message_quorum = 0
                p_seen_node = [False for node_id in self.nodes]
                for p_msg in highest_pr_rc_message.data['justification']:
                    assert not p_seen_node[p_msg.sender], "Second PREPARE message from same sender in the justification of highest_pr_rc_message"
                    assert p_msg.data['value'] == highest_pr_rc_message.data['value'], "PREPARE message in justification of highest_pr_rc_message does not have highest_pr_rc_message.data['value']"
                    assert self.validate_prepare_message(p_msg, highest_pr_rc_message.round), "PREPARE message in justification of highest_pr_rc_message is not from highest_pr_rc_message.round"
                    p_seen_node[p_msg.sender] = True
                    p_message_quorum += self.nodes[p_msg.sender].weight
                assert p_message_quorum >= self.byz_quorum, "Justification of highest_pr_rc_message does not meet quorum weight"
        return True

    def receive_message(self, message, round):
        # TODO: Verify signatures
        if message.type == "PRE_PREPARE":
            if self.validate_pre_prepare_message(message, round):
                return self.store.add_message(message)
        elif message.type == "PREPARE":
            if self.validate_prepare_message(message, round):
                return self.store.add_message(message)
        elif message.type == "COMMIT":
            if self.validate_commit_message(message, round):
                return self.store.add_message(message)
        elif message.type == "ROUND_CHANGE":
            if self.validate_round_change_message(message, round):
                return self.store.add_message(message)
        return False

    def process_message(self, message):
        """
        Returns:
            - "MESSAGE_REJECTED" if the message was not added to the store
            - "NOT_NEW_MESSAGE" if the message has already been seen before
            - "MSG_NOT_PROCESSED" if the message was added to store, but not processed
            - "FUTURE_MESSAGE" if the message is from a future round and is not processed right now
            - "NO_CHANGE" for no change to the timer
            - "START_TIMER" for starting/restarting the timer
            - "STOP_TIMER" for stopping the timer
        """
        current_round = self.store.get_round()
        current_state = self.store.get_state()
        log.info(f'Processing message in round: {current_round},  state: {current_state}')
        # FIXME: After round change, check if any upon conditions are already satisfied in the store

        if message.type not in ["PRE_PREPARE", "PREPARE", "COMMIT", "ROUND_CHANGE"]:
            log.error(f'Unknown message type: {message.type}')
            return "MESSAGE_REJECTED"

        if current_state == "DECIDED":
            # TODO: Send the decided value if ROUND_CHANGE message is received
            return "MESSAGE_REJECTED"

        if message.type != "COMMIT" and message.round < current_round:
            # Process COMMIT messages from any round
            return "MESSAGE_REJECTED"

        try:
            # Validate the message, then add to the store
            is_new_message = self.receive_message(message, current_round)
        except AssertionError as e:
            log.error('Message was invalid', exc_info=True)
            return "MESSAGE_REJECTED"

        if not is_new_message:
            return "NOT_NEW_MESSAGE"

        #-----------------------------------------------------------------------
        if message.type == "PRE_PREPARE":
            if message.round > current_round:
                return "FUTURE_MESSAGE"
            if current_state not in ["PRE_PREPARED", "ROUND_TIMEOUT", "ROUND_CHANGED"]:
                return "MSG_NOT_PROCESSED"
            self.store.set_state("PREPARED")
            if self.node_identity is not None:
                data = {'value': message.data['value']}
                sender = self.node_identity
                prepare_message = ConsensusMessage("PREPARE", current_round, data, sender)
                broadcast_message(prepare_message, self.store.get_peers())
            log.info(f'State set to PREPARED. Prepared for value: {message.data["value"]}')
            log.debug(f'PRE_PREPARE was: {message}')
            return "START_TIMER"
        #-----------------------------------------------------------------------
        elif message.type == "PREPARE":
            if message.round > current_round:
                return "FUTURE_MESSAGE"
            if current_state not in ["PRE_PREPARED", "PREPARED", "ROUND_TIMEOUT", "ROUND_CHANGED"]:
                return "MSG_NOT_PROCESSED"
            prepare_msgs = self.store.get_messages(current_round, "PREPARE")
            supporting_weights = {}
            for msg in prepare_msgs:
                value = msg.data['value']
                if value not in supporting_weights:
                    supporting_weights[value] = 0
                supporting_weights[value] += self.nodes[msg.sender].weight
            max_supporting_weight = max(supporting_weights.values())
            for value in supporting_weights:
                if supporting_weights[value] == max_supporting_weight:
                    best_value = value
            if max_supporting_weight >= self.byz_quorum:
                self.store.set_prepared_round(current_round)
                self.store.set_prepared_value(best_value)
                quorum_messages = []
                for msg in prepare_msgs:
                    if msg.data['value'] == best_value:
                        quorum_messages.append(msg)
                self.store.add_quorum_messages(current_round, "PREPARE_QUORUM", quorum_messages)
                self.store.set_state("COMMITTED")
                if self.node_identity is not None:
                    data = {'value': best_value}
                    sender = self.node_identity
                    commit_message = ConsensusMessage("COMMIT", current_round, data, sender)
                    broadcast_message(commit_message, self.store.get_peers())
                log.info(f'State set to COMITTED. Committed to value {best_value}')
                log.debug(f'PREPARE_QUORUM was: {[msg.to_string() for msg in quorum_messages]}')
            return "NO_CHANGE"
        #-----------------------------------------------------------------------
        elif message.type == "COMMIT":
            if current_state not in ["PRE_PREPARED", "PREPARED", "COMMITTED", "ROUND_TIMEOUT", "ROUND_CHANGED"]:
                # Process commit messages in any state
                return "MSG_NOT_PROCESSED"
            commit_msgs = self.store.get_messages(message.round, "COMMIT")
            supporting_weights = {}
            for msg in commit_msgs:
                value = msg.data['value']
                if value not in supporting_weights:
                    supporting_weights[value] = 0
                supporting_weights[value] += self.nodes[msg.sender].weight
            max_supporting_weight = max(supporting_weights.values())
            for value in supporting_weights:
                if supporting_weights[value] == max_supporting_weight:
                    best_value = value
            if max_supporting_weight >= self.byz_quorum:
                self.store.set_decided_value(best_value)
                quorum_messages = []
                for msg in commit_msgs:
                    if msg.data['value'] == best_value:
                        quorum_messages.append(msg)
                self.store.add_quorum_messages(message.round, "COMMIT_QUORUM", quorum_messages)
                self.store.set_state("DECIDED")
                log.info(f'State set to DECIDED. Decided on value: {best_value}')
                log.debug(f'COMMIT_QUORUM was: {[msg.to_string() for msg in quorum_messages]}')
                return "STOP_TIMER"
            return "NO_CHANGE"
        #-----------------------------------------------------------------------
        elif message.type == "ROUND_CHANGE":
            if current_state != "ROUND_CHANGED" and message.round > current_round:
                rc_quorum = []
                seen_node = [False for node in self.nodes]
                supporting_weight = 0
                # TODO: Don't access self.store.messages directly
                for round in self.store.messages:
                    if round > current_round:
                        if "ROUND_CHANGE" in self.store.messages[round]:
                            for rc_msg in self.store.messages[round]["ROUND_CHANGE"]:
                                if not seen_node[rc_msg.sender]:
                                    rc_quorum.append(rc_msg)
                                    seen_node[rc_msg.sender] = True
                                    supporting_weight += self.nodes[rc_msg.sender].weight
                if supporting_weight >= self.rc_threshold:
                    rc_quorum_round_nums = [rc_msg.round for rc_msg in rc_quorum]
                    new_round_num = min(rc_quorum_round_nums)
                    self.store.set_round(new_round_num)
                    self.store.set_state("ROUND_CHANGED")
                    self.broadcast_round_change()
                    log.info(f'State set to ROUND_CHANGED. rc_quorum was: {[msg.to_string() for msg in rc_quorum]}')
                    return "START_TIMER"
            elif message.round == current_round:
                rc_quorum = self.store.get_messages(current_round, "ROUND_CHANGE")
                supporting_weight = sum([self.nodes[rc_msg.sender].weight for rc_msg in rc_quorum])
                # TODO: Don't access self.store.messages directly
                if supporting_weight >= self.byz_quorum:
                    highest_pr_rc_message = max(rc_quorum, key=lambda rc_msg: rc_msg.data['prepared_round'])
                    self.store.set_state("PRE_PREPARED")
                    if self.store.get_leader() == self.node_identity:
                        self.broadcast_proposal(highest_pr_rc_message.data['prepared_value'], rc_quorum)
            return "NO_CHANGE"
        #-----------------------------------------------------------------------
        log.error(f'Unknown message type: {message.type}')
        return "MSG_NOT_PROCESSED"
