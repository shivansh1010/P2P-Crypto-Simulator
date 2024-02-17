"""module to create and handle events and event queue"""

from queue import PriorityQueue


class EventQueue:
    def __init__(self):
        self.queue = PriorityQueue()
    def push(self, event):
        self.queue.put(event)
    def pop(self):
        return self.queue.get(block=False)
    def print(self):
        print(self.queue)

class Event:
    def __init__(self, time, sender_id, receiver_id, type, data=None):
        self.time = time
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.type = type
        self.data = data

    def __lt__(self, other):
        return self.time < other.time

    def __str__(self):
        return f" Event -> time {round(self.time, 4)} sender {self.sender_id} receiver {self.receiver_id} type {self.type}"
