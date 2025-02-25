import json
from enum import Enum


class ParsingState(Enum):
    START = 0
    EXPECTING_KEY = 1
    EXPECTING_VALUE = 2
    EXPECTING_COLON = 3
    EXPECTING_PARTIAL_VALUE = 4
    EXPECTING_PARTIAL_KEY = 5


class StreamingJsonParser:
    WHITESPACE_ACCEPTING_STATES = [
        ParsingState.START,
        ParsingState.EXPECTING_KEY,
        ParsingState.EXPECTING_VALUE,
        ParsingState.EXPECTING_COLON,
    ]

    INVALID_CHARS_BY_STATE = {
        ParsingState.EXPECTING_VALUE: {","},
        ParsingState.EXPECTING_COLON: {","},
        ParsingState.EXPECTING_PARTIAL_KEY: {" "},
    }

    def __init__(self):
        self.root: dict[str, str] = {}
        self.object_stack: list[dict[str, any]] = [self.root]
        self.last_key: str | None = None
        self.partial_token_value: str = ""
        self.partial_token_key: str = ""
        self.current_state: ParsingState = ParsingState.START

    def consume(self, buffer: str):
        pos = 0

        while pos < len(buffer):
            char = buffer[pos]

            if self.current_state in self.WHITESPACE_ACCEPTING_STATES:
                if char in [" ", "\n", "\r", "\t"]:
                    pos += 1
                    continue

            self.validate_state_based_chars(char)

            if self.current_state == ParsingState.EXPECTING_PARTIAL_KEY:
                self.handle_partial_token_key(char)
                pos += 1
                continue

            if self.current_state == ParsingState.EXPECTING_PARTIAL_VALUE:
                self.handle_partial_token_value(char)
                pos += 1
                continue

            match char:
                case " " | ",":
                    pos += 1
                case "{":
                    self.handle_new_object()
                    pos += 1
                case ":":
                    if self.current_state == ParsingState.EXPECTING_COLON:
                        self.current_state = ParsingState.EXPECTING_VALUE
                    pos += 1
                case '"':
                    pos = self.parse_quotes(buffer, pos)
                case "}":
                    self.handle_close_object()
                    pos += 1
                case "[" | "]":
                    raise ValueError("Array's are currently not supported")

    def validate_state_based_chars(self, char: str):
        invalid_chars = self.INVALID_CHARS_BY_STATE.get(self.current_state, set())
        if char in invalid_chars:
            raise ValueError(
                f"Invalid symbol '{char}' during {self.current_state} state"
            )

    def handle_new_object(self):
        if self.current_state == ParsingState.EXPECTING_PARTIAL_VALUE:
            raise ValueError(
                f"Expecting {self.last_key}'s value. (Starting) curly brace passed"
            )

        if self.current_state in [ParsingState.START, ParsingState.EXPECTING_KEY]:
            if self.current_state == ParsingState.START:
                self.current_state = ParsingState.EXPECTING_KEY
            else:
                raise ValueError("Unexpected '{'. Expecting a key")
        elif self.current_state in [ParsingState.EXPECTING_VALUE] and self.last_key:
            new_obj: Dict[str, str] = {}
            self.object_stack[-1][self.last_key] = new_obj
            self.object_stack.append(new_obj)
            self.last_key = None
            self.current_state = ParsingState.EXPECTING_KEY
        else:
            raise ValueError("Unexpected '{'")

    def handle_close_object(self):
        if len(self.object_stack) > 1:
            self.object_stack.pop()
            self.current_state = ParsingState.EXPECTING_KEY

    def parse_quotes(self, buffer: str, pos: int) -> int:
        end_quote_pos = buffer.find('"', pos + 1)

        if end_quote_pos < 0:
            partial_token = buffer[pos + 1 :]
            if not self.last_key:
                self.current_state = ParsingState.EXPECTING_PARTIAL_KEY
                self.handle_partial_token_key(partial_token)
            else:
                self.current_state = ParsingState.EXPECTING_PARTIAL_VALUE
                self.handle_partial_token_value(partial_token)

            return len(buffer)

        quote_token = buffer[pos + 1 : end_quote_pos]
        if (
            self.current_state != ParsingState.EXPECTING_PARTIAL_VALUE
            and not self.last_key
        ):
            self.parse_key(quote_token)

        elif self.current_state == ParsingState.EXPECTING_VALUE:
            self.parse_value(quote_token)

        return end_quote_pos + 1

    def handle_partial_token_key(self, char: str):
        if char == '"':
            self.handle_completed_token_key()
        else:
            self.partial_token_key += char

    def handle_completed_token_key(self):
        self.last_key = self.partial_token_key
        self.partial_token_key = ""
        self.current_state = ParsingState.EXPECTING_VALUE

    def handle_partial_token_value(self, char: str):
        if char == '"':
            return self.handle_completed_token_value()
        else:
            self.partial_token_value += char

        if not self.last_key:
            raise ValueError("Invalid symbol found, expecting value")

        self.object_stack[-1][self.last_key] = self.partial_token_value

    def handle_completed_token_value(self):
        self.partial_token_value = ""
        self.last_key = None
        self.current_state = ParsingState.EXPECTING_KEY

    def parse_key(self, key: str):
        self.last_key = key

        self.current_state = ParsingState.EXPECTING_COLON

        self.object_stack[-1][key] = ""

    def parse_value(self, value: str):
        self.object_stack[-1][self.last_key] = value

        self.last_key = None
        self.current_state = ParsingState.EXPECTING_KEY

    def get(self) -> dict:
        return self.root
