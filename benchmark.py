import time
import json
import ijson
from streaming_json_parser import StreamingJsonParser
from memory_profiler import memory_usage
import cProfile, pstats

profiler = cProfile.Profile()
profiler.enable()


FILENAME = "large_test_data.json"
# FILENAME = "test_json_64kb.json"
# FILENAME = "sample-conversation.json"
CHUNK_SIZE = 4096


def benchmark_streaming_json_parser(filename, chunk_size=CHUNK_SIZE):
    """Benchmark StreamingJsonParser (Your Implementation)."""
    parser = StreamingJsonParser()
    start = time.time()

    with open(filename, "r") as f:
        while chunk := f.read(chunk_size):
            parser.consume(chunk)

    end = time.time()
    print(f"StreamingJsonParser: {end - start:.4f} sec")
    return [parser.get(), end - start]


def benchmark_streaming_json_parser_complete(filename, chunk_size=CHUNK_SIZE):
    """Benchmark StreamingJsonParser (Your Implementation)."""
    parser = StreamingJsonParser()
    start = time.time()

    buffer = ""
    with open(filename, "r") as f:
        while chunk := f.read(chunk_size):
            buffer += chunk

    parser.consume(buffer)
    end = time.time()
    # print(f"StreamingJsonParser: {end - start:.4f} sec")
    return [parser.get(), end - start]


def benchmark_ijson(filename):
    """Benchmark ijson (Incremental JSON Parsing)."""
    start = time.time()

    with open(filename, "rb") as f:
        objects = list(ijson.items(f, "item"))  # Streams JSON elements

    end = time.time()
    # print(f"ijson: {end - start:.4f} sec")
    return [objects, end - start]


def benchmark_json_loads(filename):
    """
    This is not technically an iterative parsing benchmark
    However this is extremely fast (while using a lot more memory)
    """
    start = time.time()

    with open(filename) as f:
        objects = json.load(f)

    end = time.time()
    # print(f"json.loads: {end - start:.4f} sec")
    return [objects, end - start]


def run_benchmark(benchmark_func, *args, **kwargs):
    """
    Run a benchmark function and report its peak memory usage.
    The memory_usage call will run the function and return memory snapshots.
    """
    mem_usage = memory_usage((benchmark_func, args, kwargs), interval=0.1, timeout=None)
    result = benchmark_func(*args, **kwargs)
    peak_memory = max(mem_usage)
    print(f"{benchmark_func.__name__} peak memory usage: {peak_memory:.2f} MB")
    return result + [peak_memory]


if __name__ == "__main__":
    print("\n=== Benchmarking JSON Parsers ===")

    streaming_result = run_benchmark(benchmark_streaming_json_parser, FILENAME)
    sjp_full_result = run_benchmark(benchmark_streaming_json_parser_complete, FILENAME)
    ijson_result = run_benchmark(benchmark_ijson, FILENAME)
    json_loads_result = run_benchmark(benchmark_json_loads, FILENAME)

    print("|        Approach      | Time taken | Memory usage |")
    print("|----------------------|------------|--------------|")
    print(
        f"|  SJP (partial)       |    {streaming_result[1]:.2f}    |    {streaming_result[2]:.2f}     |"
    )
    print(
        f"|  SJP (complete)      |    {sjp_full_result[1]:.2f}    |    {sjp_full_result[2]:.2f}     |"
    )
    print(
        f"|      ijson           |    {ijson_result[1]:.2f}    |    {ijson_result[2]:.2f}     |"
    )
    print(
        f"|     json_loads       |    {json_loads_result[1]:.2f}    |    {json_loads_result[2]:.2f}    |"
    )

benchmark_streaming_json_parser(FILENAME)

# profiler.disable()
# stats = pstats.Stats(profiler).sort_stats("cumulative")
# stats.print_stats(10)
