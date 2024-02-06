from queue import PriorityQueue


class EventQueue:
    def __init__(self):
        self.queue = PriorityQueue()
    def push(self, event):
        self.queue.put(event)
    def pop(self):
        return self.queue.get(block=False)

class Event:
    def __init__(self, time, peer, type, data):
        self.time = time
        self.peer = peer
        self.type = type
        self.data = data

    def __lt__(self, other):
        return self.time < other.time

    def __str__(self):
        return f"==Event(time {self.time}, peer {self.peer.peer_id}, type {self.type}=="
