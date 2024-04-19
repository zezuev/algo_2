
from dataclasses import dataclass
from typing import overload


type State = int | str
type Symbol = int | str
type Rule = dict[Symbol, State]
type Ruleset = dict[State, Rule]


@dataclass
class TuringMachine:
    q: list[State]
    sigma: list[Symbol]
    gamma: list[Symbol]
    space: Symbol
    start: State
    finish: State
    rules: Ruleset

    def __post_init__(self):
        self._validate_symbols(self.sigma, self.gamma, self.space, self.rules)
        self._validate_states(self.q, self.start, self.finish, self.rules)

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
            unknown_states.update(set(rule.values()).difference(q_set))
        raise ValueError(
            "The following states are referenced in the ruleset but are not present "
            f"in the gamma alphabet: {", ".join(unknown_states)}."
        )


class Tape:

    @overload
    def __init__(self, content: list[Symbol], space: Symbol): ...
    @overload
    def __init__(self, content: list[Symbol], space: Symbol, origin: int = 0): ...

    def __init__(self, content: list[Symbol], space: Symbol, origin: int = 0):
        self._content = content
        self._space = space
        self._origin = origin

        self._min = -origin
        self._max = (len(content) - 1) - origin

    def region(self, idx: int, span: int = 5) -> list[Symbol]:
        self._ensure_exists(idx-span)
        self._ensure_exists(idx+span)
        return self._content[idx+self._origin-span:idx+self._origin+span+1]

    def __getitem__(self, idx: int) -> Symbol:
        self._ensure_exists(idx)
        return self._content[idx+self._origin]

    def __setitem__(self, idx: int, symbol: Symbol):
        self._ensure_exists(idx)
        self._content[idx+self._origin] = symbol

    def _ensure_exists(self, idx: int):
        if idx < self._min:
            self._extend_left()
        elif idx > self._max:
            self._extend_right()

    def _extend_left(self):
        current_len = len(self._content)
        self._content[:0] = [self._space for _ in range(current_len)]
        self._min -= current_len
        self._origin += current_len

    def _extend_right(self):
        current_len = len(self._content)
        self._content += [self._space for _ in range(current_len)]
        self._max += current_len

    @property
    def content(self) -> list[Symbol]:
        return self._content


class Run:

    def __init__(self, tm: TuringMachine, tape: Tape): ...
