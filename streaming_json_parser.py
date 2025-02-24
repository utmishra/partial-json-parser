import json
from enum import Enum


class ParsingState(Enum):
    START = 0
    EXPECTING_KEY = 1
    EXPECTING_VALUE = 2
    EXPECTING_COLON = 3
    EXPECTING_PARTIAL_VALUE = 4


class StreamingJsonParser:
    def __init__(self):
        self.root: dict = {}
        self.stack: List[str] = []
        self.last_key: str | None = None
        self.partial_token = ""
        self.current_state: ParsingState = ParsingState.START

    def consume(self, buffer: str):
        pos = 0

        while pos < len(buffer):
            char = buffer[pos]

            if self.current_state == ParsingState.EXPECTING_PARTIAL_VALUE:
                if char == '"':
                    self.handle_completed_token()
                else:
                    self.partial_token += char
                    self.handle_partial_token()
                pos += 1
                continue

            match char:
                case " " | ",":
                    pos += 1
                case "{":
                    self.handle_start_quote()
                    pos += 1
                case ":":
                    if self.current_state == ParsingState.EXPECTING_COLON:
                        self.current_state = ParsingState.EXPECTING_VALUE
                    pos += 1
                case '"':
                    pos = self.parse_quotes(buffer, pos)
                case "}":
                    if self.current_state == ParsingState.EXPECTING_PARTIAL_VALUE:
                        raise ValueError(
                            f"Expecting {self.last_key}'s value. (Ending) curly brace passed"
                        )

                    pos += 1
                case "[" | "]":
                    raise ValueError("Array's are currently not supported")

    def handle_start_quote(self):
        if self.current_state == ParsingState.EXPECTING_PARTIAL_VALUE:
            raise ValueError(
                f"Expecting {self.last_key}'s value. (Starting) curly brace passed"
            )

        if not self.stack:
            self.stack = self.root
        else:
            # Nested object
            parent_obj = self.stack
            parent_obj[self.last_key] = {}
            self.stack = parent_obj[self.last_key]
            self.last_key = None
            self.current_state = ParsingState.EXPECTING_KEY

    def parse_quotes(self, buffer: str, pos: int) -> int:
        end_quote_pos = buffer.find('"', pos + 1)

        if end_quote_pos < 0:
            self.partial_token = buffer[pos + 1 :]
            self.handle_partial_token()

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

    def handle_partial_token(self) -> int:
        if not self.last_key:
            raise BufferError("Invalid symbol found, expecting value")

        self.current_state = ParsingState.EXPECTING_PARTIAL_VALUE

        self.stack[self.last_key] = self.partial_token

    def handle_completed_token(self):
        self.partial_token = None
        self.last_key = None
        self.current_state = ParsingState.EXPECTING_KEY

    def parse_key(self, key: str):
        self.last_key = key

        self.current_state = ParsingState.EXPECTING_COLON

        self.stack[key] = ""

    def parse_value(self, value: str):
        self.stack[self.last_key] = value

        self.last_key = None
        self.current_state = ParsingState.EXPECTING_KEY

    def get(self) -> dict:
        return self.root
