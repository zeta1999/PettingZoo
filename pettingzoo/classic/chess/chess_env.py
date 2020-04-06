from . import chess_utils
import chess
from pettingzoo import AECEnv
from gym import spaces
import numpy as np
import warnings
from pettingzoo.utils.agent_selector import agent_selector


class env(AECEnv):

    metadata = {'render.modes': ['human', 'ascii']}

    def __init__(self):
        super(env, self).__init__()

        self.board = chess.Board()

        self.agents = ["player_{}".format(i) for i in range(2)]

        self.agent_order = list(self.agents)
        self._agent_selector = agent_selector(self.agent_order)

        self.action_spaces = {name: spaces.Discrete(8 * 8 * 73) for name in self.agents}
        self.observation_spaces = {name: spaces.Box(low=0, high=1, shape=(8, 8, 20), dtype=np.float32) for name in self.agents}

        self.rewards = {name: 0 for name in self.agents}
        self.dones = {name: False for name in self.agents}
        self.infos = {name: {'legal_moves': []} for name in self.agents}

        self.agent_selection = self._agent_selector.reset()

        self.reset()

    def observe(self, agent):
        return chess_utils.get_observation(self.board, self.agents.index(agent))

    def reset(self, observe=True):
        self.board = chess.Board()

        self.agent_selection = self._agent_selector.reset()

        self.rewards = {name: 0 for name in self.agents}
        self.dones = {name: False for name in self.agents}
        self.infos = {name: {'legal_moves': []} for name in self.agents}
        self.infos[self.agent_selection]['legal_moves'] = chess_utils.legal_moves(self.board)

        if observe:
            return self.observe(self.agent_selection)
        else:
            return

    def set_game_result(self, result_val):
        for i, name in enumerate(self.agents):
            self.dones[name] = True
            result_coef = 1 if i == 0 else -1
            self.rewards[name] = result_val * result_coef
            self.infos[name] = {'legal_moves': []}

    def step(self, action, observe=True):
        current_agent = self.agent_selection
        current_index = self.agents.index(current_agent)
        self.agent_selection = next_agent = self._agent_selector.next()

        old_legal_moves = self.infos[current_agent]['legal_moves']

        if action not in old_legal_moves:
            warnings.warn("Bad chess move made, game terminating with current player losing. \nenv.infos[player]['legal_moves'] contains a list of all legal moves that can be chosen.")
            player_loses_val = -1 if current_index == 0 else 1
            self.set_game_result(player_loses_val)
            self.rewards[next_agent] = 0
        else:
            chosen_move = chess_utils.action_to_move(self.board, action, current_index)
            assert chosen_move in self.board.legal_moves
            self.board.push(chosen_move)

            next_legal_moves = chess_utils.legal_moves(self.board)

            is_stale_or_checkmate = not any(next_legal_moves)

            # claim draw is set to be true to allign with normal tournament rules
            is_repetition = self.board.is_repetition(3)
            is_50_move_rule = self.board.can_claim_fifty_moves()
            is_claimable_draw = is_repetition or is_50_move_rule
            game_over = is_claimable_draw or is_stale_or_checkmate

            if game_over:
                result = self.board.result(claim_draw=True)
                result_val = chess_utils.result_to_int(result)
                self.set_game_result(result_val)
            else:
                self.infos[current_agent] = {'legal_moves': []}
                self.infos[next_agent] = {'legal_moves': next_legal_moves}
                assert len(self.infos[next_agent]['legal_moves'])

        if observe:
            next_observation = self.observe(next_agent)
        else:
            next_observation = None
        return next_observation

    def render(self, mode='human'):
        print(self.board)

    def close(self):
        pass