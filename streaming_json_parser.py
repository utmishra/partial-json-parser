import re
from enum import Enum


class ParsingState(Enum):
    """
    Machine States for different stages for (iterative) JSON parsing
    """

    START = 0
    EXPECTING_KEY = 1
    EXPECTING_VALUE = 2
    EXPECTING_COLON = 3
    EXPECTING_PARTIAL_VALUE = 4
    EXPECTING_PARTIAL_KEY = 5


class StreamingJsonParser:
    """
    Iterative JSON Parser tailor-made for consuming partial JSON chunks.
    Leverage state-machine like transitions to parse expected data based on the current state.
    The active state also helps in validating the incoming data.
    Currently works only for strings and objects.
    """

    WHITESPACE = re.compile(r"[ \t\n\r]+")

    WHITESPACE_ACCEPTING_STATES = [
        ParsingState.START,
        ParsingState.EXPECTING_KEY,
        ParsingState.EXPECTING_VALUE,
        ParsingState.EXPECTING_COLON,
    ]

    INVALID_CHARS_BY_STATE = {
        ParsingState.EXPECTING_VALUE: {","},
        ParsingState.EXPECTING_COLON: {",", "{", "}", '"'},
        ParsingState.EXPECTING_KEY: {"{"},
        ParsingState.EXPECTING_PARTIAL_KEY: {" "},
        ParsingState.EXPECTING_PARTIAL_VALUE: {"{", "}"},
    }

    _STATE_VALIDATORS = {
        ParsingState.EXPECTING_KEY: re.compile(r'^\s*["}]'),
        ParsingState.EXPECTING_COLON: re.compile(r"^\s*:"),
        ParsingState.EXPECTING_VALUE: re.compile(r'^\s*["{]'),
    }

    def __init__(self):
        self.root: dict[str, str] = {}
        self.object_stack: list[dict] = [self.root]
        self.last_key: str | None = None
        self.partial_token_value: str = ""
        self.partial_token_key: str = ""
        self.current_state: ParsingState = ParsingState.START

    def _regex_validate(self, buffer: str) -> None:
        """
        Validates the beginning of the buffer against a regex pattern
        based on the current state. If the pattern does not match,
        it raises a ValueError with context.
        """
        validator = self._STATE_VALIDATORS.get(self.current_state)
        if validator and not validator.match(buffer):
            raise ValueError(
                f"Invalid token for state {self.current_state} in buffer: {buffer!r}"
            )

    def consume(self, buffer: str):
        """
        Consumes a chunk of JSON data and updates the final JSON object.
        The currently parsed data is processed based on the `current_state`,
        which includes partial tokens (Key & Values)
        """
        pos = 0
        buf_len = len(buffer)

        if self.current_state in self.WHITESPACE_ACCEPTING_STATES:
            m = self.WHITESPACE.match(buffer, pos)
            if m:
                pos = m.end()

        while pos < buf_len:
            char = buffer[pos]

            if self.current_state in self.WHITESPACE_ACCEPTING_STATES and char in [
                " ",
                "\n",
                "\r",
                "\t",
            ]:
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
                    raise ValueError("Arrays are currently not supported")
                case _:
                    raise ValueError(
                        f"Unexpected character '{char}' encountered in state {self.current_state}"
                    )

    def validate_state_based_chars(self, char: str):
        """
        Certain characters shouldn't be allowed during specific states,
        example: If a value is expected after a key, a comma shouldn't occur
        """
        invalid_chars = self.INVALID_CHARS_BY_STATE.get(self.current_state, set())
        if char in invalid_chars:
            raise ValueError(
                f"Invalid symbol '{char}' during {self.current_state} state"
            )

    def handle_new_object(self):
        """
        Pushes a new object to stack in case of nested objects,
        when a `{` occurs during EXPECTING_PARTIAL_VALUE stage
        """
        if self.current_state == ParsingState.START:
            self.current_state = ParsingState.EXPECTING_KEY
            return

        if self.current_state in [ParsingState.EXPECTING_VALUE] and self.last_key:
            new_obj: dict[str, str] = {}
            self.object_stack[-1][self.last_key] = new_obj
            self.object_stack.append(new_obj)
            self.last_key = None
            self.current_state = ParsingState.EXPECTING_KEY

    def handle_close_object(self):
        """
        Handles closing of a JSON Object ('}').
        Pops the last object from the stack and updates the state
        """
        if len(self.object_stack) > 1:
            self.object_stack.pop()
            self.current_state = ParsingState.EXPECTING_KEY

    def parse_quotes(self, buffer: str, pos: int) -> int:
        """
        Parses a token expected in quotes (key or value).
        Delegates control to partial token handler if end quote is not found.
        Note: `.find` could be avoided to improve performance?

        Returns:
            Updated position to the end of complete or partial token.
        """
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
        """
        Updates (or finalizes) the partial token key
        """
        if char == '"':
            self.handle_completed_token_key()
        else:
            self.partial_token_key += char

    def handle_completed_token_key(self):
        """
        Marks the token key as complete and updates state
        """
        self.last_key = self.partial_token_key
        self.partial_token_key = ""
        self.current_state = ParsingState.EXPECTING_VALUE

    def handle_partial_token_value(self, char: str):
        """
        Updates (or finalizes) the partial token value
        """
        if char == '"':
            return self.handle_completed_token_value()
        else:
            self.partial_token_value += char

        if not self.last_key:
            raise ValueError("Invalid symbol found, expecting value")

        self.object_stack[-1][self.last_key] = self.partial_token_value

    def handle_completed_token_value(self):
        """
        Marks the token value as complete and updates state
        """
        self.partial_token_value = ""
        self.last_key = None
        self.current_state = ParsingState.EXPECTING_KEY

    def parse_key(self, key: str):
        """
        Saves the key in current object state and updates state
        """
        self.last_key = key

        self.current_state = ParsingState.EXPECTING_COLON

        self.object_stack[-1][key] = ""

    def parse_value(self, value: str):
        """
        Saves the value for the current key in object state and updates state
        """
        self.object_stack[-1][self.last_key] = value

        self.last_key = None
        self.current_state = ParsingState.EXPECTING_KEY

    def get(self) -> dict:
        """
        Returns the current state of the parsed JSON object
        """
        return self.root
