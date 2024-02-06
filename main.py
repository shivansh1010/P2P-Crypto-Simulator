
import argparse
import numpy as np
from constants import *
from network import Network
from events import Event, EventQueue
import time


def start_simulation(n, z0, z1, txn_time, mining_time, simulation_until):
    network = Network(n, z0, z1)
    network.display_network()
    
    event_queue = EventQueue()
    # push initial timestamps of every peer to the queue
    for peer in network.peers:
        event_queue.push(Event(0, peer, "txn_generate"))
        event_queue.push(Event(0, peer, "blk_mine"))


    current_time = 0
    while True:
        # get next event
        if not event_queue.queue.empty():
            event = event_queue.pop()
        else:
            print("No more events")
            break

        # print(event)
        time.sleep(event.time - current_time)
        # process event
        if event.time > simulation_until:
            print ("Simulation time is up")
            break
        if event.type == "txn_generate":
            peer = event.peer
            peer.generate_transaction(event_queue, network.peers)
            delay = np.random.exponential(txn_time) # time to wait before generating next txn
            nxt_txn = Event(time.time() + delay, peer, "txn_generate")
            event_queue.push(nxt_txn)
            
            # print(f"Transaction event at time {event.time} for peer {event.peer.peer_id}")
        elif event.type == "block":
            # process block
            print(f"Block event at time {event.time} for peer {event.peer.peer_id}")
            pass
        else:
            print("Unknown event type")
            break
            
        # add to event queue
        event_queue.push(Event(event.time + event.peer.get_next_event_timestmp(), 
                            event.peer, "transaction"))
        current_time = event.time


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('n', type=int, help='No. of nodes')
    parser.add_argument('z1', type=float, help='Fraction of low cpu peers')
    parser.add_argument('txn_time', type=int, help='Transaction time in ms')
    parser.add_argument('mining_time', type=int, help='Mining time in ms')
    parser.add_argument('simulation_until', type=int, help='Simulation time units')

    args = parser.parse_args()
   
    if (5 <= len(vars(args)) < 5):
        parser.error("Provide 5 arguments:\n"
                     "No. of nodes\n"
                     "Fraction of low cpu peers\n"
                     "Transaction time in ms\n"
                     "Mining time in ms\n"
                     "Simulation time units\n"
                    )

    n = args.n
    z0 = 0.5 
    z1 = args.z1
    txn_time = args.txn_time
    mining_time = args.mining_time
    simulation_until = args.simulation_until

    print("n:", n)
    print("z1:", z1)
    print("txn_time:", txn_time)
    print("mining_time:", mining_time)
    print("simulation_until:", simulation_until)

    start_simulation(n, z0, z1, txn_time, mining_time, simulation_until)


