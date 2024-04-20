
from typing import Literal, Self, overload
from itertools import product


type State = int | str
type Symbol = int | str
type GoedelNumber = str
type Direction = Literal["L", "N", "R"]
type Action = tuple[State, Symbol, Direction]
type Rule = dict[Symbol, Action]
type Ruleset = dict[State, Rule]
type TapeView = tuple[list[Symbol], Symbol, list[Symbol]]


class TuringMachine:

    def __init__(
            self,
            q: list[State],
            sigma: list[Symbol],
            gamma: list[Symbol],
            space: Symbol,
            start: State,
            finish: State,
            rules: Ruleset,
            *,
            strict: bool = False,
    ):
        self._validate_symbols(sigma, gamma, space, rules)
        self._validate_states(q, start, finish, rules)
        if strict:
            self._validate_ruleset(q, gamma, finish, rules)

        self.q = q
        self.sigma = sigma
        self.gamma = gamma
        self.space = space
        self.start = start
        self.finish = finish
        self.rules = rules

    def action(self, state: State, symbol: Symbol) -> Action:
        if state not in self.rules:
            raise ValueError(f"State {state!r} is not in q.")
        if symbol not in self.rules[state]:
            raise ValueError(
                f"No action defined for symbol {symbol!r} in state {state!r}."
            )
        return self.rules[state][symbol]

    @property
    def goedel(self) -> GoedelNumber:
        q_map = dict(zip(self.q, range(1, len(self.q)+1)))
        gamma_map = dict(zip(self.gamma, range(1, len(self.gamma)+1)))
        d_map = {"L": 1, "N": 2, "R": 3}

        def goedel_part(state: State, symbol: Symbol) -> str:
            q_next, s_next, d = self.action(state, symbol)
            return "11" + "1".join((
                "0"*q_map[state],
                "0"*gamma_map[symbol],
                "0"*q_map[q_next],
                "0"*gamma_map[s_next],
                "0"*d_map[d],
            ))

        parts = [
            goedel_part(state, symbol)
            for state, symbol in product(self.q, self.gamma)
            if state != self.finish
        ]
        return "".join(parts) + "111"

    @classmethod
    def from_goedel(
            cls,
            goedel: GoedelNumber,
            q: list[State],
            sigma: list[Symbol],
            gamma: list[Symbol],
            space: Symbol,
            start: State,
            finish: State,
    ) -> Self:
        q_map: dict[int, State] = dict(zip(range(1, len(q)+1), q))
        gamma_map: dict[int, Symbol] = dict(zip(range(1, len(gamma)+1), gamma))
        d_map: dict[int, Direction] = {1: "L", 2: "N", 3: "R"}

        rules: Ruleset = {}
        goedel = goedel[2:-3]
        parts = goedel.split("11")
        for part in parts:
            i, j, k, l, m = [len(x) for x in part.split("1")]
            state = q_map[i]
            symbol = gamma_map[j]
            next_state = q_map[k]
            next_symbol = gamma_map[l]
            direction = d_map[m]

            rules.setdefault(state, {})[symbol] = (next_state, next_symbol, direction)

        return cls(q, sigma, gamma, space, start, finish, rules)

    @staticmethod
    def _validate_symbols(
            sigma: list[Symbol],
            gamma: list[Symbol],
            space: Symbol,
            rules: Ruleset,
    ):
        sigma_set = set(sigma)
        gamma_set = set(gamma)

        missing_symbols = sigma_set.difference(gamma_set)
        if missing_symbols:
            raise ValueError(
                "The following symbols are present in the sigma alphabet but not in "
                f"the gamma alphabet: {", ".join(missing_symbols)}."
            )

        if space not in gamma_set:
            raise ValueError(f"The space ({space!r}) is not in the gamma alphabet.")

        unknown_symbols: set[Symbol] = set()
        for rule in rules.values():
            unknown_symbols.update(set(rule.keys()).difference(gamma_set))
        if unknown_symbols:
            raise ValueError(
                "The following symbols are referenced in the ruleset but are not "
                f"present gamma alphabet: {", ".join(unknown_symbols)}."
            )

    @staticmethod
    def _validate_states(q: State, start: State, finish: State, rules: Ruleset):
        q_set = set(q)

        if start not in q_set:
            raise ValueError(f"The start state ({start!r}) is not in Q.")

        if finish not in q_set:
            raise ValueError(f"The finish state ({finish!r}) is not in Q.")

        unknown_states: set[State] = set()
        for state, rule in rules.items():
            if state not in q_set:
                unknown_states.add(state)
            unknown_states.update(set(v[0] for v in rule.values()).difference(q_set))
        if unknown_states:
            raise ValueError(
                "The following states are referenced in the ruleset but are not "
                f"present in the gamma alphabet: {", ".join(unknown_states)}."
            )

    @staticmethod
    def _validate_ruleset(
        q: list[State],
        gamma: list[Symbol],
        finish: State,
        rules: Ruleset,
    ):
        nonterminal_q = set(q)
        nonterminal_q.remove(finish)

        missing_states = nonterminal_q.difference(rules.keys())
        if missing_states:
            raise ValueError(
                "The following states are not accounted for in the ruleset: "
                f"{", ".join(missing_states)}."
            )

        gamma_set = set(gamma)
        missing_rules: set[tuple[State, Symbol]] = set()
        for state, rule in rules.items():
            missing_rules.update(
                (state, symbol)
                for symbol in gamma_set.difference(rule.keys())
            )
        if missing_rules:
            raise ValueError(
                "The following rules are missing in the ruleset: "
                f"{", ".join(str(r) for r in missing_rules)}"
            )


class Tape:

    @overload
    def __init__(self, space: Symbol, *, origin: int): ...
    @overload
    def __init__(self, space: Symbol, content: list[Symbol], *, origin: int): ...

    def __init__(
            self,
            space: Symbol,
            content: list[Symbol] | None = None,
            *,
            origin: int = 0,
    ):
        content = content or [space]
        self.content = content
        self.space = space
        self._origin = origin

        self._min = -origin
        self._max = (len(content) - 1) - origin

    def display(self, idx: int, span: int = 5) -> TapeView:
        self._ensure_exists(idx-span)
        self._ensure_exists(idx+span)
        return (
            self.content[idx+self._origin-span:idx+self._origin],
            self.content[idx+self._origin],
            self.content[idx+self._origin+1:idx+self._origin+span+1],
        )

    def __getitem__(self, idx: int) -> Symbol:
        self._ensure_exists(idx)
        return self.content[idx+self._origin]

    def __setitem__(self, idx: int, symbol: Symbol):
        self._ensure_exists(idx)
        self.content[idx+self._origin] = symbol

    def __eq__(self, other):
        raise NotImplementedError("Comparison of Tapes not yet implemented.")

    def __len__(self):
        raise NotImplementedError

    def _ensure_exists(self, idx: int):
        while idx < self._min:
            self._extend_left()
        while idx > self._max:
            self._extend_right()

    def _extend_left(self):
        current_len = len(self.content)
        self.content[:0] = [self.space for _ in range(current_len)]
        self._min -= current_len
        self._origin += current_len

    def _extend_right(self):
        current_len = len(self.content)
        self.content += [self.space for _ in range(current_len)]
        self._max += current_len


class Run:

    def __init__(self, tm: TuringMachine, tape: Tape):
        self.tm = tm
        self.tape = tape
        self.idx = 0
        self.state = tm.start

    def step(self):
        if not self.done():
            action = self.tm.action(self.state, self.tape[self.idx])
            self.state, self.tape[self.idx], direction = action
            if direction == "L":
                self.idx -= 1
            elif direction == "R":
                self.idx += 1

    def finish(self):
        while not self.done():
            self.step()

    def display(self, span: int = 5) -> tuple[State, TapeView]:
        return (self.state, self.tape.display(self.idx, span))

    def done(self) -> bool:
        return self.state == self.tm.finish

    def __bool__(self):
        return not self.done()
