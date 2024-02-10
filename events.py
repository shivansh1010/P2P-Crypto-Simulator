from queue import PriorityQueue
# from node import Node


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
    def __init__(self, time, sender, receiver, type, data=None):
        self.time = time
        self.sender = sender
        self.receiver = receiver
        self.type = type
        self.data = data

    def __lt__(self, other):
        return self.time < other.time

    def __str__(self):
        return f" Event -> time {round(self.time, 4)} sender {self.sender.id} receiver {self.receiver.id} type {self.type}"
