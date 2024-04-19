
from dataclasses import dataclass
from typing import Literal, overload


type State = int | str
type Symbol = int | str
type Direction = Literal["L", "N", "R"]
type Action = tuple[State, Symbol, Direction]
type Rule = dict[Symbol, Action]
type Ruleset = dict[State, Rule]
type TapeView = tuple[list[Symbol], Symbol, list[Symbol]]


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

    def action(self, state: State, symbol: Symbol) -> Action:
        return self.rules[state][symbol]

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


class Tape:

    @overload
    def __init__(self, space: Symbol): ...
    @overload
    def __init__(self, space: Symbol, *, origin: int): ...
    @overload
    def __init__(self, space: Symbol, content: list[Symbol]): ...
    @overload
    def __init__(self, space: Symbol, content: list[Symbol], *, origin: int): ...

    def __init__(
            self,
            space: Symbol,
            content: list[Symbol] | None = None,
            *,
            origin: int = 0,
    ):
        self.content = content or [space]
        self.space = space
        self._origin = origin

        self._min = -origin
        self._max = (len(content) - 1) - origin

    def display(
            self,
            idx: int,
            span: int = 5,
    ) -> TapeView:
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

    def display(self, span: int = 5) -> tuple[State, TapeView]:
        return (self.state, self.tape.display(self.idx, span))

    def done(self) -> bool:
        return self.state == self.tm.finish
