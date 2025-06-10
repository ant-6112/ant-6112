import threading


def cpu_bound_task():
    count = 0
    for i in range(10000000):
        count += 1
    print(count)
    return count


threads = []
for _ in range(4):
    thread = threading.Thread(target=cpu_bound_task)
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
