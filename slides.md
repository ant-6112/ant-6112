---
theme: default
background: linear-gradient(135deg, #0F1419 0%, #1A202C 100%)
class: text-center
highlighter: shiki
lineNumbers: false
info: |
  ## Multithreading and Multiprocessing in Python

  A comprehensive guide to concurrent programming in Python
drawings:
  persist: false
transition: slide-left
title: Multithreading and Multiprocessing in Python
mdc: true
---

<style>
.slidev-layout {
  background: linear-gradient(135deg, #0F1419 0%, #1A202C 100%);
  color: #E2E8F0;
  font-family: 'Inter', sans-serif;
}

.palantir-accent {
  color: #4FACFE;
}

.palantir-secondary {
  color: #00F5FF;
}

.palantir-warning {
  color: #FFB020;
}

.palantir-success {
  color: #32D74B;
}

.code-block {
  background: rgba(15, 20, 25, 0.8);
  border: 1px solid #2D3748;
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
}

.highlight-box {
  background: rgba(79, 172, 254, 0.1);
  border-left: 4px solid #4FACFE;
  padding: 1rem;
  margin: 1rem 0;
  border-radius: 0 8px 8px 0;
}

.task-animation {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.slide-in-left {
  animation: slideInLeft 0.8s ease-out;
}

@keyframes slideInLeft {
  from { transform: translateX(-100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.slide-in-right {
  animation: slideInRight 0.8s ease-out;
}

@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.fade-in-up {
  animation: fadeInUp 1s ease-out;
}

@keyframes fadeInUp {
  from { transform: translateY(30px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>

# <span class="palantir-accent">Multithreading</span> and <span class="palantir-secondary">Multiprocessing</span>
## in Python

<div class="fade-in-up">
<div class="pt-12">
  <span @click="$slidev.nav.next" class="px-2 py-1 rounded cursor-pointer" hover="bg-white bg-opacity-10">
    Let's dive into concurrent programming! <carbon:arrow-right class="inline"/>
  </span>
</div>
</div>

<div class="abs-br m-6 text-xl">
  <carbon:arrow-right class="palantir-accent" />
</div>

<!--
Multithreading and Multiprocessing:

So What is Multithreading and Multiprocessing ?.

Both Multithreading and Multiprocessing at its core have the same concept which is running doing multiple tasks or computational operations at once or in parellel some might say.

Abstractions

I am gonna demo it how to do it in python but it can replicated across many others as well.
-->

---
transition: fade-out
---

# What Does "Multiple Tasks at Once" Really Mean?

<div class="grid grid-cols-2 gap-4">

<div v-click="1">

## For Humans 🧠
- We're actually **terrible** at true multitasking
- We rapidly switch between tasks (Context Switching)
- Limited by our Single-Threaded Brain
- Maximum ~2-3 tasks before quality degrades

</div>

<div v-click="2">

## For Computers 💻
- Modern Processors have multiple cores
- Can Truly Execute Tasks Simultaneously
- Operating systems manage resource allocation
- Hardware-Level parallelism support

</div>

</div>

<div v-click="3" class="mt-8 text-center">

### The Question: How can we harness this computational power? 🚀

</div>

<!--
From the Core of the machines that we use, Transistors - Circuits to what is being displayed on your laptop screen is powered by multithreading or parellel processing.

Let's say if your screen is full of lakhs of Micro-LEDs. how is it able to light up each LED with a different color at once so that you can see the complete picture.
-->

---
layout: default
---

# Modern Computer Architecture

<div v-click="1" class="mt-8 p-4 bg-gray-100 rounded-lg dark:bg-gray-800">

**Everything in your Computer is designed for Concurrency:**
- Multiple Processing Units with Shared Memory.
- Transistors switching at billions of cycles per second
- Low-level binary operations running in parallel
- Pixels being lit up simultaneously on your displays
- Multiple Programs/Windows/Chrome Tabs executing simultaneously

</div>

---
layout: two-cols
---

# Processes vs Threads

<div v-click="1">

## Process 🏠
- Independent execution environment
- Own memory space
- Heavy resource overhead
- Inter-process communication needed
- Crashes don't affect other processes

</div>

::right::

<div v-click="2">

## Thread 🧵
- Lightweight execution unit
- Shared memory space
- Lower resource overhead
- Direct memory communication
- One thread crash can affect others

</div>

image: "multithreading.png"

---
layout: default
---

# Multithreading vs Multiprocessing

<div class="grid grid-cols-2 gap-8">

<div v-click="1">

## Multithreading 🧵
**Multiple threads within a single process**

### Advantages:
- Fast communication (shared memory)
- Low overhead
- Quick thread creation/destruction

### Disadvantages:
- Shared state complications
- Potential race conditions
- GIL limitations in Python

</div>

<div v-click="2">

## Multiprocessing 🔄
**Multiple separate processes**

### Advantages:
- True parallelism
- Isolated memory spaces
- Better fault tolerance

### Disadvantages:
- Higher memory usage
- Slower inter-process communication
- More complex setup

</div>

</div>

<div v-click="3" class="mt-8 text-center">

### When to use which? It depends on your specific use case! 🤔

</div>

---
layout: center
class: text-center
---

# Let's See This in Action! 🎮

Time for some hands-on demonstrations with Python

<div v-click class="mt-8">

We'll start with **Turtle Graphics** to visualize the concepts,
then move to **real-world examples** with Pandas and file processing

</div>

---
layout: default
---

# Demo 1: Sequential vs Concurrent Drawing

<div class="grid grid-cols-2 gap-4">

<div>

## Sequential Approach
```python
import turtle
import time

def draw_square(t, size, x, y):
    t.penup()
    t.goto(x, y)
    t.pendown()
    for _ in range(4):
        t.forward(size)
        t.right(90)
    time.sleep(1)  # Simulate work

# Sequential execution
screen = turtle.Screen()
pen = turtle.Turtle()

start_time = time.time()
for i in range(4):
    draw_square(pen, 50, i*60, 0)
end_time = time.time()

print(f"Sequential: {end_time - start_time:.2f}s")
```

</div>

<div>

## Multithreaded Approach
```python
import turtle
import threading
import time

def draw_square_threaded(x, y, color):
    t = turtle.Turtle()
    t.color(color)
    t.penup()
    t.goto(x, y)
    t.pendown()
    for _ in range(4):
        t.forward(50)
        t.right(90)
    time.sleep(1)

# Multithreaded execution
screen = turtle.Screen()
threads = []
colors = ['red', 'blue', 'green', 'yellow']

start_time = time.time()
for i, color in enumerate(colors):
    thread = threading.Thread(
        target=draw_square_threaded,
        args=(i*60, 0, color)
    )
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
end_time = time.time()

print(f"Multithreaded: {end_time - start_time:.2f}s")
```

</div>

</div>

---
layout: default
---

# Demo 2: CPU-Intensive Tasks with Multiprocessing

```python
import multiprocessing
import time
import math

def cpu_intensive_task(n):
    """Simulate CPU-intensive work"""
    result = 0
    for i in range(n):
        result += math.sqrt(i) * math.sin(i)
    return result

def sequential_processing():
    start_time = time.time()
    results = []
    for i in range(4):
        results.append(cpu_intensive_task(1000000))
    end_time = time.time()
    return end_time - start_time, results

def multiprocess_processing():
    start_time = time.time()
    with multiprocessing.Pool() as pool:
        results = pool.map(cpu_intensive_task, [1000000] * 4)
    end_time = time.time()
    return end_time - start_time, results

if __name__ == "__main__":
    # Sequential
    seq_time, seq_results = sequential_processing()
    print(f"Sequential: {seq_time:.2f} seconds")

    # Multiprocessing
    mp_time, mp_results = multiprocess_processing()
    print(f"Multiprocessing: {mp_time:.2f} seconds")
    print(f"Speedup: {seq_time/mp_time:.2f}x")
```

---
layout: default
---

# Demo 3: Real-World Example - File Processing

<div class="grid grid-cols-2 gap-4">

<div>

## Threading for I/O Operations
```python
import threading
import pandas as pd
import requests
import time

def download_and_process(url, filename):
    """Download CSV and process it"""
    try:
        # Simulate download
        time.sleep(2)  # I/O wait

        # Create sample data
        data = pd.DataFrame({
            'A': range(1000),
            'B': range(1000, 2000),
            'C': [x**2 for x in range(1000)]
        })

        # Process data
        result = data.groupby('A').sum()
        result.to_csv(f"processed_{filename}")
        print(f"Processed {filename}")

    except Exception as e:
        print(f"Error processing {filename}: {e}")

# Threading for I/O-bound tasks
files = ['data1.csv', 'data2.csv', 'data3.csv', 'data4.csv']
urls = ['http://example.com/'] * 4

start_time = time.time()
threads = []

for url, filename in zip(urls, files):
    thread = threading.Thread(
        target=download_and_process,
        args=(url, filename)
    )
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

threading_time = time.time() - start_time
print(f"Threading time: {threading_time:.2f}s")
```

</div>

<div>

## Multiprocessing for CPU Operations
```python
import multiprocessing
import pandas as pd
import numpy as np

def heavy_computation(data_chunk):
    """CPU-intensive data processing"""
    df = pd.DataFrame(data_chunk)

    # Heavy computations
    df['complex_calc'] = (
        df['A'] * np.sin(df['B']) +
        np.sqrt(df['C']) *
        np.log(df['A'] + 1)
    )

    # Statistical operations
    result = {
        'mean': df['complex_calc'].mean(),
        'std': df['complex_calc'].std(),
        'max': df['complex_calc'].max(),
        'min': df['complex_calc'].min()
    }

    return result

def process_large_dataset():
    # Create large dataset
    large_data = {
        'A': np.random.randint(1, 100, 100000),
        'B': np.random.randint(1, 1000, 100000),
        'C': np.random.randint(1, 50, 100000)
    }

    # Split data into chunks
    chunk_size = 25000
    chunks = []
    for i in range(0, 100000, chunk_size):
        chunk = {k: v[i:i+chunk_size]
                for k, v in large_data.items()}
        chunks.append(chunk)

    start_time = time.time()
    with multiprocessing.Pool() as pool:
        results = pool.map(heavy_computation, chunks)

    mp_time = time.time() - start_time
    print(f"Multiprocessing time: {mp_time:.2f}s")
    return results

if __name__ == "__main__":
    results = process_large_dataset()
    print("Processing completed!")
```

</div>

</div>

---
layout: center
class: text-center
---

# The Python Reality Check 🐍

<div v-click="1" class="text-xl mt-8">

Python doesn't have true multithreading!

</div>

<div v-click="2" class="mt-8">

It's like humans trying to multitask - we think we're doing multiple things,
but we're really just switching between tasks very quickly!

</div>

---
layout: default
---

# The Global Interpreter Lock (GIL) 🔒

<div v-click="1">

## What is the GIL?
- A mutex or lock that protects access to Python objects or variables.
- Prevents multiple native threads from executing Python Code simultaneously
- Only **one thread** can execute Python code at a time

</div>

<div v-click="3" class="mt-6">

```python
import threading
import time

def cpu_bound_task():
    count = 0
    for i in range(10000000):
        count += 1
    return count

threads = []
for _ in range(4):
    thread = threading.Thread(target=cpu_bound_task)
    threads.append(thread)
    thread.start()
    thread.join()
```

</div>

---
layout: default
---

# When to Use Threading vs Multiprocessing

<div class="grid grid-cols-2 gap-8">

<div v-click="1">

## Use Threading For: 🧵

### I/O-Bound Tasks
- File operations
- Network requests
- Database queries
- User interface responsiveness

```python
# Good use case
import threading
import requests

def fetch_url(url):
    response = requests.get(url)
    return response.status_code

# Multiple network requests
urls = ['http://site1.com', 'http://site2.com']
threads = []

for url in urls:
    thread = threading.Thread(target=fetch_url, args=(url,))
    threads.append(thread)
    thread.start()
```

</div>

<div v-click="2">

## Use Multiprocessing For: 🔄

### CPU-Bound Tasks
- Mathematical computations
- Data processing
- Image/video processing
- Machine learning algorithms

```python
# Good use case
import multiprocessing
import numpy as np

def matrix_multiply(matrices):
    a, b = matrices
    return np.dot(a, b)

# Heavy computation
large_matrices = [(np.random.rand(1000, 1000),
                  np.random.rand(1000, 1000))
                 for _ in range(4)]

with multiprocessing.Pool() as pool:
    results = pool.map(matrix_multiply, large_matrices)
```

</div>

</div>

<div v-click="3" class="mt-8 text-center">

### Rule of Thumb: Threading for waiting, Multiprocessing for computing! 🎯

</div>

---
layout: default
---

# Advanced Concepts: Thread Safety & Communication

<div class="grid grid-cols-2 gap-6">

<div>

## Thread Safety Issues
```python
import threading
import time

# Dangerous: Race condition!
counter = 0

def unsafe_increment():
    global counter
    for _ in range(100000):
        counter += 1  # Not atomic!

# This will give inconsistent results
threads = []
for _ in range(5):
    thread = threading.Thread(target=unsafe_increment)
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

print(f"Counter: {counter}")  # Not 500000!
```

## Safe Version with Lock
```python
import threading

counter = 0
lock = threading.Lock()

def safe_increment():
    global counter
    for _ in range(100000):
        with lock:  # Acquire lock
            counter += 1  # Now it's safe!

# This will give consistent results
threads = []
for _ in range(5):
    thread = threading.Thread(target=safe_increment)
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

print(f"Counter: {counter}")  # Always 500000!
```

</div>

<div>

## Process Communication
```python
import multiprocessing
import time

def producer(queue):
    """Produce data and put in queue"""
    for i in range(5):
        data = f"Data item {i}"
        queue.put(data)
        print(f"Produced: {data}")
        time.sleep(1)

def consumer(queue):
    """Consume data from queue"""
    while True:
        try:
            data = queue.get(timeout=2)
            print(f"Consumed: {data}")
            time.sleep(0.5)
        except:
            break

if __name__ == "__main__":
    # Create a queue for communication
    queue = multiprocessing.Queue()

    # Create processes
    prod = multiprocessing.Process(
        target=producer, args=(queue,))
    cons = multiprocessing.Process(
        target=consumer, args=(queue,))

    # Start processes
    prod.start()
    cons.start()

    # Wait for completion
    prod.join()
    cons.join()
```

</div>

</div>

---
layout: default
---

# Best Practices & Common Pitfalls

<div class="grid grid-cols-2 gap-6">

<div v-click="1">

## ✅ Best Practices

### For Threading:
- Use `threading.Lock()` for shared resources
- Prefer `with` statements for locks
- Use `Queue` for thread communication
- Keep critical sections small

### for Multiprocessing:
- Use `if __name__ == "__main__":` guard
- Prefer `multiprocessing.Pool` for simple tasks
- Use `Queue` or `Pipe` for communication
- Be mindful of pickling limitations

</div>

<div v-click="2">

## ❌ Common Pitfalls

### Threading Issues:
- Race conditions (unsynchronized access)
- Deadlocks (circular waiting)
- Forgetting to join threads
- Using threading for CPU-bound tasks

### Multiprocessing Issues:
- Forgetting the main guard
- Trying to share unpicklable objects
- Creating too many processes
- Not handling process cleanup

</div>

</div>

<div v-click="3" class="mt-8 p-4 bg-blue-100 rounded-lg dark:bg-blue-900">

**Pro Tip:** Start simple, measure performance, then optimize.
Not every program needs concurrency!

</div>

---
layout: default
---

# Performance Comparison Demo

```python
import time
import threading
import multiprocessing
import concurrent.futures

def cpu_task(n):
    """CPU-intensive task"""
    total = 0
    for i in range(n):
        total += i ** 2
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
    results['Sequential CPU'] = time.time() - start

    # Threading (CPU) - Should be slower due to GIL
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(executor.map(cpu_task, cpu_data))
    results['Threading CPU'] = time.time() - start

    # Multiprocessing (CPU) - Should be faster
    start = time.time()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        list(executor.map(cpu_task, cpu_data))
    results['Multiprocessing CPU'] = time.time() - start

    # Threading (I/O) - Should be much faster
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(executor.map(io_task, io_data))
    results['Threading I/O'] = time.time() - start

    return results

if __name__ == "__main__":
    results = benchmark_approaches()
    for approach, time_taken in results.items():
        print(f"{approach}: {time_taken:.2f} seconds")
```

---
layout: default
---

# Choosing the Right Approach

<div class="overflow-x-auto">

| Task Type | Best Approach | Why? | Example |
|-----------|---------------|------|---------|
| **CPU-Intensive** | Multiprocessing | Bypasses GIL, uses multiple cores | Mathematical calculations, image processing |
| **I/O-Intensive** | Threading or AsyncIO | Threads can wait while others work | File operations, web requests |
| **Network Operations** | AsyncIO | Most efficient for many concurrent connections | Web scraping, API calls |
| **Mixed Workload** | Combination | Use appropriate tool for each part | Data pipeline with I/O and computation |

</div>

---
layout: center
class: text-center
---

# Key Takeaways 🎯

<div class="grid grid-cols-2 gap-8 mt-8">

<div v-click="1">

## Remember the GIL! 🔒
- Python threading ≠ true parallelism
- Great for I/O, limited for CPU tasks
- Multiprocessing bypasses this limitation

</div>

<div v-click="2">

## Choose Wisely 🤔
- **I/O-bound**: Threading or AsyncIO
- **CPU-bound**: Multiprocessing
- **Simple tasks**: Use libraries like `concurrent.futures`

</div>

<div v-click="3">

## Best Practices 📋
- Measure before optimizing
- Handle errors and cleanup properly
- Start simple, then scale complexity

</div>

<div v-click="4">

## Modern Python 🚀
- AsyncIO for modern async programming
- `concurrent.futures` for simplified APIs
- Consider alternative Python implementations (PyPy, etc.)

</div>

</div>

---
layout: center
class: text-center
---

# Thank You! 🙏

## Questions & Discussion

<div class="mt-8">

### Resources for Further Learning:
- [Python Official Documentation](https://docs.python.org/3/library/concurrent.futures.html)
- [Real Python Concurrency Guide](https://realpython.com/python-concurrency/)
- [AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)

</div>

<div class="mt-8">

**Remember:** Concurrency is a tool, not a goal.
Use it when it solves a real problem! 🎯

</div>
