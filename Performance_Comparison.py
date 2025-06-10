import concurrent.futures
import time


def cpu_task(n):
    """CPU-intensive task"""
    total = 0
    for i in range(n):
        total += i**2
    return total


def io_task(duration):
    """I/O simulation"""
    time.sleep(duration)
    return f"Slept for {duration} seconds"


def benchmark_approaches():
    # Test data
    cpu_data = [1000000] * 4
    io_data = [1] * 4

    results = {}

    # Sequential
    start = time.time()
    [cpu_task(n) for n in cpu_data]
    results["Sequential CPU"] = time.time() - start

    # Threading (CPU) - Should be slower due to GIL
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(executor.map(cpu_task, cpu_data))
    results["Threading CPU"] = time.time() - start

    # Multiprocessing (CPU) - Should be faster
    start = time.time()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        list(executor.map(cpu_task, cpu_data))
    results["Multiprocessing CPU"] = time.time() - start

    # Threading (I/O) - Should be much faster
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(executor.map(io_task, io_data))
    results["Threading I/O"] = time.time() - start

    return results


if __name__ == "__main__":
    results = benchmark_approaches()
    for approach, time_taken in results.items():
        print(f"{approach}: {time_taken:.2f} seconds")
