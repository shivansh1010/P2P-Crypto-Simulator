"""module to create and handle events and event queue"""

from queue import PriorityQueue


class EventQueue:
    """Class to represent a queue of events in the network simulation"""
    def __init__(self):
        self.queue = PriorityQueue()

    def push(self, event):
        """Add an event to the queue"""
        self.queue.put(event)

    def pop(self):
        """Remove and return the next event from the queue"""
        return self.queue.get(block=False)

    def print(self):
        """Print the event queue"""
        print(self.queue)


class Event:
    """Class to represent an event in the network simulation"""
    def __init__(self, time, sender_id, receiver_id, type, data=None):
        self.time = time
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.type = type
        self.data = data

    def __lt__(self, other):
        return self.time < other.time

    def __str__(self):
        return f"Event -> type={self.type} sender={self.sender_id} receiver={self.receiver_id}"
