class StreamingJsonParser:
    def __init__(self):
        self.buffer = None
        self.streamed_json = dict()
        self.stack = []
        self.last_key_stack = []
        self.last_value_stack = []

    def consume(self, buffer: str):
        self.__scan__once(buffer, 0)

    def __scan__once(self, chunk: str, index: int):
        try:
            chunk = chunk.strip()
            next_char = chunk[index]
        except IndexError:
            raise StopIteration(index) from None

        while index < len(chunk):
            next_char = chunk[index]
            print(f"__scan__once: next_char: {next_char}, index: {index}")
            if next_char == " " or next_char == ",":
                index += 1
            elif next_char == "{":
                print("__scan__once: Parsing object")
                self.stack.append({})
                index = self.__parse__object__(chunk, index + 1)
            elif next_char == '"':
                print("__scan__once: Parsing string")
                index = self.__parse_quotes__(chunk, index)
            elif next_char == "}":
                obj = self.stack.pop()
                print(
                    f"__scan__once: Closing bracket. Saving obj: {obj} to {self.last_key_stack}"
                )
                if self.last_key_stack:
                    last_key = self.last_key_stack.pop()
                    self.stack[-1][last_key] = obj
                else:
                    self.streamed_json = obj

                index += 1
            else:
                raise IOError("Invalid character found")

    def parse_string(self, chunk: str, index: int):
        print(f"Parsing string: {chunk}")

    def __parse__object__(self, chunk: str, index: int) -> int:
        while index < len(chunk) and chunk[index] == " ":
            index += 1

        next_char = chunk[index]

        if next_char == '"':
            return self.__parse_quotes__(chunk, index)
        else:
            raise IOError("__parse__object__: Invalid symbol")

    def __parse_quotes__(self, chunk: str, index: int) -> int:
        if not self.stack or (
            len(self.last_key_stack) == 0
            or self.last_key_stack[-1] not in self.stack[-1]
        ):
            index = self.__parse_key__(chunk, index + 1)
        else:
            index = self.__parse_value__(chunk, index + 1)

        return index

    def __parse_key__(self, chunk: str, index: int) -> int:
        # Current string is key
        print("__parse_key__: Parsing key")
        last_occurrence = chunk.find('"', index + 1)
        if last_occurrence == -1:
            raise IOError("__parse__key__: Closing quote not found")

        self.last_key_stack.append(chunk[index:last_occurrence])
        print(f"__parse_key__: Key found: {self.last_key_stack}")
        obj = self.stack[-1]
        obj[self.last_key_stack[-1]] = None
        # TODO: Partial state needs to be saved later
        # self.streamed_json = obj
        index = last_occurrence + 1
        """
            { "key1": "value2" }
        """

        print(f"__parse_key__: Saved stack: {self.stack}")

        print(f"__parse_key__: Saved value: {self.streamed_json}")

        # Look for colon (:)
        while index < len(chunk) and chunk[index] == " ":
            index += 1

        if chunk[index] != ":":
            raise IOError("__parse_key__: Colon not found")

        print(f"__parse_key__: Colon found at index: {index}")

        return index + 1

    def __parse_value__(self, chunk: str, index: int):
        # Current string is value
        print("__parse_value__: Parsing value")
        last_occurrence = chunk.find('"', index + 1)
        if last_occurrence == -1:
            raise JSONDecodeError
        obj = self.stack[-1]
        value = chunk[index : last_occurrence + 1]
        print(f"__parse_value__: Stack: {self.stack}")
        print(f"__parse_value__: Value found: {value}")
        print(f"__parse_value__: Last key stack: {self.last_key_stack}")
        obj[self.last_key_stack[-1]] = value
        self.last_key_stack.pop()

        print(f"__parse_value__: Updated value: {self.stack}")

        return last_occurrence + 1

    def get(self):
        return self.streamed_json


# sample_json = '{ "key": "value" }'
# parser = StreamingJsonParser()
# parser.consume(sample_json)
# print(parser.get())

# sample_json = '{ "key": "value", "key2": "value2" }'
# parser2 = StreamingJsonParser()
# parser2.consume(sample_json)
# print(parser2.get())

# sample_json = '{ "key": "value", "key2": { "subKey": "subValue" } }'
# sample_json = '{ "key": "value", "key2": "value2" }'
sample_json = '{ "key": "value", "key2": { "subKey": { "subSubKey": "subSubValue" } } }'
parser3 = StreamingJsonParser()
parser3.consume(sample_json)
print(parser3.get())
