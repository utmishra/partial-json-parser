import json

from streaming_json_parser import StreamingJsonParser

# from streaming_json_parser_refactored import StreamingJsonParser


def test_streaming_json_parser():
    parser = StreamingJsonParser()
    parser.consume('{"foo": "bar"}')
    result = parser.get()
    assert result == {"foo": "bar"}, f"Expected {{'foo': 'bar'}}, got {result}"
    print("Test 1 passed")


def test_chunked_streaming_json_parser():
    parser = StreamingJsonParser()
    # 1st chunk: key but no value yet.
    parser.consume('{"foo": ')
    result = parser.get()
    # At this point, the key "foo" exists with its placeholder value.
    assert result == {"foo": ""}, f"Expected {{'foo': ''}}, got {result}"
    # 2nd chunk: start of a nested object.
    parser.consume("{")
    result = parser.get()
    # Now "foo" should have a nested object.
    assert result == {"foo": {}}, f"Expected {{'foo': {{}}}}, got {result}"
    # 3rd chunk: add a key for the nested object.
    parser.consume(' "bar": ')
    result = parser.get()
    # In the nested object, "bar" exists with a placeholder.
    assert result == {
        "foo": {"bar": ""}
    }, f"Expected {{'foo': {{'bar': ''}}}}, got {result}"
    # 4th chunk: begin a nested object for "bar".
    parser.consume("{")
    result = parser.get()
    assert result == {
        "foo": {"bar": {}}
    }, f"Expected {{'foo': {{'bar': {{}}}}}}, got {result}"
    # 5th chunk: add key "baz" to the innermost object.
    parser.consume(' "baz": ')
    result = parser.get()
    assert result == {
        "foo": {"bar": {"baz": ""}}
    }, f"Expected {{'foo': {{'bar': {{'baz': ''}}}}}}, got {result}"
    # 6th chunk: complete the value "bat" and close all objects.
    parser.consume(' "bat" }}}')
    result = parser.get()
    assert result == {
        "foo": {"bar": {"baz": "bat"}}
    }, f"Expected {{'foo': {{'bar': {{'baz': 'bat'}}}}}}, got {result}"
    print("Test 2 passed")


def test_partial_streaming_json_parser():
    parser = StreamingJsonParser()
    # Partial value for key "foo"
    parser.consume('{"foo": "bar')
    result = parser.get()
    # Even though the closing quote isn’t received yet, the partial value is returned.
    assert result == {"foo": "bar"}, f"Expected {{'foo': 'bar'}}, got {result}"
    # Complete the value.
    parser.consume('"}')
    result = parser.get()
    assert result == {"foo": "bar"}, f"Expected {{'foo': 'bar'}}, got {result}"
    print("Test 3 passed")


def test_partial_string_values():
    parser = StreamingJsonParser()

    parser.consume('{ "foo": ')

    result = parser.get()

    assert result == {"foo": ""}, f"Expected {{'foo': ''}}, got {result}"

    parser.consume('"')

    result = parser.get()

    assert result == {"foo": ""}, f"Expected {{'foo': ''}}, got {result}"

    parser.consume("bar")

    result = parser.get()

    assert result == {"foo": "bar"}, f"Expected {{'foo': 'bar'}}, got {result}"

    parser.consume(" with a long")

    result = parser.get()

    assert result == {
        "foo": "bar with a long"
    }, f"Expected {{'foo': 'bar with a long'}}, got {result}"

    parser.consume(' string"')

    result = parser.get()

    assert result == {
        "foo": "bar with a long string"
    }, f"Expected {{'foo': 'bar with a long string'}}, got {result}"

    parser.consume(",")

    result = parser.get()

    assert result == {
        "foo": "bar with a long string"
    }, f"Expected {{'foo': 'bar with a long string'}}, got {result}"

    parser.consume(' "baz"')

    result = parser.get()

    assert result == {
        "foo": "bar with a long string",
        "baz": "",
    }, f"Expected {{'foo': 'bar with a long string', 'baz': ''}}, got {result}"

    parser.consume(': "bat"')

    result = parser.get()

    assert result == {
        "foo": "bar with a long string",
        "baz": "bat",
    }, f"Expected {{'foo': 'bar with a long string', 'baz': 'bat'}}, got {result}"

    parser.consume("}}")

    result = parser.get()

    assert result == {
        "foo": "bar with a long string",
        "baz": "bat",
    }, f"Expected {{'foo': 'bar with a long string', 'baz': 'bat'}}, got {result}"

    print("Test 4 passed")


def test_nested_and_outer_json_parser():
    parser = StreamingJsonParser()
    parser.consume('{ "foo": ')
    result = parser.get()
    assert result == {"foo": ""}, f"Expected {{'foo': ''}}, got {result}"

    parser.consume("{")
    result = parser.get()
    assert result == {"foo": {}}, f"Expected {{'foo': ''}}, got {result}"

    parser.consume('"subKey":')
    result = parser.get()
    assert result == {"foo": {"subKey": ""}}, f"Expected {{'foo': ''}}, got {result}"

    parser.consume("{")
    result = parser.get()
    assert result == {"foo": {"subKey": {}}}, f"Expected {{'foo': ''}}, got {result}"

    parser.consume(' "subSubKey": ')
    result = parser.get()
    assert result == {
        "foo": {"subKey": {"subSubKey": ""}}
    }, f"Expected {{'foo': ''}}, got {result}"

    parser.consume('"value"')
    result = parser.get()
    assert result == {
        "foo": {"subKey": {"subSubKey": "value"}}
    }, f"Expected {{'foo': ''}}, got {result}"

    parser.consume(', "subSubKey1": "value2"}')
    result = parser.get()
    assert result == {
        "foo": {"subKey": {"subSubKey": "value", "subSubKey1": "value2"}}
    }, f"Expected {{'foo': ''}}, got {result}"

    parser.consume(', "subKey2": "value3"}}')
    result = parser.get()
    assert result == {
        "foo": {
            "subKey": {"subSubKey": "value", "subSubKey1": "value2"},
            "subKey2": "value3",
        }
    }, f"Expected {{'foo':{{'subKey':{{'subSubKey': 'value','subSubKey1': 'value2'}},'subKey2' : 'value3'}}}}, got {result}"

    print("Test 5 passed")


def test_json_with_comma_in_value():
    parser = StreamingJsonParser()
    parser.consume('{ "foo": "Hello')
    result = parser.get()
    assert result == {"foo": "Hello"}, f"Expected {{'foo': 'Hello'}}, got {result}"

    parser.consume(', how are you?" }')
    result = parser.get()

    assert result == {
        "foo": "Hello, how are you?"
    }, f"Expected {{'foo': 'Hello, how are you?'}}, got {result}"


def test_empty_json_object():
    parser = StreamingJsonParser()
    parser.consume("{}")
    result = parser.get()
    assert result == {}, f"Expected {{}}, got {result}"
    print("test_empty_json_object passed")


def test_nested_json_objects():
    parser = StreamingJsonParser()
    parser.consume('{"foo": {"bar": {"baz": "qux"}}}')
    result = parser.get()
    assert result == {
        "foo": {"bar": {"baz": "qux"}}
    }, f"Expected {{'foo': {{'bar': {{'baz': 'qux'}}}}}}, got {result}"
    print("test_nested_json_objects passed")


def test_deeply_nested_json():
    parser = StreamingJsonParser()
    parser.consume('{"a": {"b": {"c": {"d": {"e": "value"}}}}}')
    result = parser.get()
    assert result == {
        "a": {"b": {"c": {"d": {"e": "value"}}}}
    }, f"Expected deeply nested structure, got {result}"
    print("test_deeply_nested_json passed")


def test_partial_json_key():
    parser = StreamingJsonParser()
    parser.consume('{"foo')
    result = parser.get()
    assert result == {}, f"Expected empty dict due to incomplete key, got {result}"
    parser.consume('": "bar"}')
    result = parser.get()
    assert result == {"foo": "bar"}, f"Expected completed key-value, got {result}"
    print("test_partial_json_key passed")


def test_partial_json_value():
    parser = StreamingJsonParser()
    parser.consume('{"foo": "ba')
    result = parser.get()
    assert result == {"foo": "ba"}, f"Expected partial value, got {result}"
    parser.consume('r"}')
    result = parser.get()
    assert result == {"foo": "bar"}, f"Expected completed value, got {result}"
    print("test_partial_json_value passed")


def test_invalid_json():
    parser = StreamingJsonParser()
    try:
        parser.consume('{ "foo": "bar", "baz", ')  # Missing closing brace
        assert False, "Expected ValueError but no exception was raised"
    except ValueError:
        print("test_invalid_json passed")


def test_invalid_open_brace_when_colon_expected():
    """
    Test that an opening brace ('{') is rejected when a colon is expected.
    After parsing a key, the parser should be waiting for a colon.
    """
    parser = StreamingJsonParser()
    try:
        parser.consume('{"foo" {')
        assert False, "Expected ValueError for unexpected '{' when colon is expected"
    except ValueError as e:
        assert "Invalid symbol '{' during ParsingState.EXPECTING_COLON state" in str(
            e
        ), f"Unexpected error message: {e}"
        print("test_invalid_open_brace_when_colon_expected passed")


def test_invalid_array_when_colon_expected():
    """
    Test that an array indicator ('[') is rejected when a colon is expected.
    Arrays are not supported in this parser, so a ValueError should be raised.
    """
    parser = StreamingJsonParser()
    try:
        parser.consume('{"foo" [')
        assert False, "Expected ValueError for array indicator when colon is expected"
    except ValueError as e:
        assert "Arrays are currently not supported" in str(
            e
        ), f"Unexpected error message: {e}"
        print("test_invalid_array_when_colon_expected passed")


def test_invalid_character_in_value_context():
    """
    Test that an unexpected character (e.g., 'a') is rejected in a value context.
    After a key and colon, encountering an unexpected token should trigger an error.
    """
    parser = StreamingJsonParser()
    try:
        parser.consume('{"foo": a')
        assert False, "Expected ValueError for unexpected character in value context"
    except ValueError as e:
        assert "Unexpected character 'a'" in str(e), f"Unexpected error message: {e}"
        print("test_invalid_character_in_value_context passed")


def test_invalid_comma_in_value_context():
    """
    Test that a comma encountered in a value context (when a value is expected)
    raises an error instead of being accepted.
    """
    parser = StreamingJsonParser()
    try:
        parser.consume('{"foo":,')
        assert False, "Expected ValueError for comma in value context"
    except ValueError as e:
        assert "Invalid symbol ','" in str(e), f"Unexpected error message: {e}"
        print("test_invalid_comma_in_value_context passed")


def test_invalid_character_in_key_context():
    """
    Test that an unexpected character (e.g., 'a') is rejected when a key is expected.
    After the opening brace, encountering a non-quote character should trigger an error.
    """
    parser = StreamingJsonParser()
    try:
        parser.consume("{a")
        assert False, "Expected ValueError for unexpected character in key context"
    except ValueError as e:
        assert "Unexpected character 'a'" in str(e), f"Unexpected error message: {e}"
        print("test_invalid_character_in_key_context passed")


def test_invalid_nested_object_during_partial_value():
    """
    Test that an opening brace ('{') encountered while a partial value is being accumulated
    raises an error. This ensures that once a partial token is detected, only valid characters
    are accepted until completion.
    """
    parser = StreamingJsonParser()
    # Begin a partial value for key "foo"
    parser.consume('{"foo": "bar')
    try:
        parser.consume("{")
        assert (
            False
        ), "Expected ValueError when '{' is encountered during partial value completion"
    except ValueError as e:
        assert (
            "Invalid symbol '{' during ParsingState.EXPECTING_PARTIAL_VALUE state"
            in str(e)
        ), f"Unexpected error message: {e}"
        print("test_invalid_nested_object_during_partial_value passed")


if __name__ == "__main__":
    test_streaming_json_parser()
    test_chunked_streaming_json_parser()
    test_partial_streaming_json_parser()
    test_partial_string_values()
    test_nested_and_outer_json_parser()
    test_empty_json_object()
    test_nested_json_objects()
    test_deeply_nested_json()
    test_partial_json_key()
    test_partial_json_value()
    test_invalid_json()
    test_invalid_open_brace_when_colon_expected()
    test_invalid_array_when_colon_expected()
    test_invalid_character_in_value_context()
    test_invalid_comma_in_value_context()
    test_invalid_character_in_key_context()
    test_invalid_nested_object_during_partial_value()
