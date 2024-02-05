
import argparse
import numpy as np
from constants import *
from network import Network

def main(n, z0, z1, txn_time, mining_time, simulation_until):
    network = Network(n, z0, z1)
    network.display_network()

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

    main(n, z0, z1, txn_time, mining_time, simulation_until)


