class StreamingJsonParser:
    def __init__(self):
        """
        buffer: Saves current buffer
        streamed_json: Saves completely parsed json
        stack: Maintains currently parsing (nested) object
        """
        self.buffer = None
        self.streamed_json = dict()
        self.stack = []
        self.last_key = None
        self.last_value = None

    def consume(self, buffer: str):
        self.__scan__once(buffer, 0)

    def __scan__once(self, chunk: str, index: int):
        try:
            chunk = chunk.strip()
            next_char = chunk[index]
            print(f"next_char: {next_char}")
        except IndexError:
            raise StopIteration(index) from None

        while index < len(chunk):
            next_char = chunk[index]
            print(f"Next char at index({index}): {next_char}")
            if next_char == " ":
                index += 1
                continue

            if next_char == "{":
                print("Found starting bracket, parsing object")
                index = self.parse_object(chunk, index + 1)
            if next_char == '"':
                print("Found quote, parsing string")
                index = self.__parse_quotes(chunk, index)
            elif next_char == "}":
                print("Found closing bracket, saving object")
                obj = self.stack.pop()
                self.streamed_json = obj
                self.last_key = None
                self.last_value = None
                index += 1
            else:
                raise IOError("Invalid character found")

    def parse_string(self, chunk: str, index: int):
        print(f"Parsing string: {chunk}")

    def parse_object(self, chunk: str, index: int) -> int:
        print(f"Parsing Object: {chunk}, index: {index}")

        while index < len(chunk) and chunk[index] == " ":
            index += 1

        next_char = chunk[index]

        print(f"Next char: {next_char}, index: {index}")
        if next_char == '"':
            return self.__parse_quotes(chunk, index)

    def __parse_quotes(self, chunk: str, index: int) -> int:
        print(f"Parsing quotes. Index: {index}")
        # is_key
        print(
            f"{"Parsing key" if not self.stack or self.last_key not in self.stack[-1] else "Parsing value"}"
        )
        if not self.stack or self.last_key not in self.stack[-1]:
            index = self.__parse_key(chunk, index + 1)
        else:
            index = self.__parse_value(chunk, index + 1)

        return index

    def __parse_key(self, chunk: str, index: int) -> int:
        # Current string is key
        last_occurrence = chunk.find('"', index + 1)
        if last_occurrence == -1:
            raise IOError("Closing quote not found")

        self.last_key = chunk[index:last_occurrence]
        print(f"Key found: {self.last_key}")
        self.stack.append({self.last_key: None})
        self.streamed_json = self.stack[-1]
        index = last_occurrence + 1

        print(f"Saved stack: {self.stack}")

        print(f"Saved value: {self.streamed_json}")

        # Look for colon (:)
        while index < len(chunk) and chunk[index] == " ":
            index += 1

        if chunk[index] != ":":
            raise IOError("Colon not found")

        print(f"Colon found at index: {index}")

        return index + 1

    def __parse_value(self, chunk: str, index: int):
        # Current string is value
        last_occurrence = chunk.find('"', index + 1)
        if last_occurrence == -1:
            raise JSONDecodeError
        obj = self.stack.pop()
        value = chunk[index : last_occurrence + 1]
        print(f"Value found: {value}")
        obj[self.last_key] = value
        self.streamed_json = obj
        self.last_key = None
        self.last_value = None

        return last_occurrence + 1

    def get(self):
        return self.streamed_json


sample_json = '{ "key": "value" }'
parser = StreamingJsonParser()
parser.consume(sample_json)
print(parser.get())
