import simpy
import random

# Constants
SIMULATION_TIME = 1 * 24 * 60  # Simulation time (in minutes)
# Average arrival time of vessels (in minutes)
VESSEL_AVG_ARRIVAL_INTERVAL = 5 * 60
CONTAINERS_PER_VESSEL = 150  # Number of containers per vessel
AVAIL_BERTHS = 2  # Number of berths available
AVAIL_CRANES = 2  # Number of cranes in service
AVAIL_TRUCKS = 3  # Number of trucks in service
# Time for crane to move container to truck (in minutes)
MOVE_CONTAINER_TIME = 3
# Time for truck to move container to yard and return (in minutes)
TRUCK_TRIP_ROUND_TIME = 6
RANDOM_SEED = 11


class ContainerSimulation:
    def __init__(self, env, berths, cranes, trucks):
        self.env = env
        self.berths = simpy.Resource(env, berths)
        self.cranes = simpy.Resource(env, cranes)
        self.trucks = simpy.Resource(env, trucks)

    def now(self):
        return self.env.now

    def move_containers_from_vessels(self, vessel_id):
        arrival = self.now()
        print(f"\nvessel: Vessel {vessel_id} arriving at time {arrival:.2f}")

        berth_request = self.berths.request()
        yield berth_request

        vessel_waiting_time = self.now() - arrival
        print(
            f'vessel: Vessel {vessel_id} waited to berth for {vessel_waiting_time:.2f}')
        print(
            f"vessel: Vessel {vessel_id} berthing at time {self.now():.2f}\n")

        for container_no in range(1, CONTAINERS_PER_VESSEL + 1):
            crane_req = self.cranes.request()
            yield crane_req
            truck_req = self.trucks.request()

            yield truck_req | self.env.timeout(0)

            if truck_req.triggered:
                print(
                    f"crane: Quay crane moving container {container_no} from vessel {vessel_id} at time {self.now():.2f}")
                yield self.env.timeout(MOVE_CONTAINER_TIME)
                self.env.process(self.move_container_to_yard(
                    vessel_id, container_no))
                self.trucks.release(truck_req)
            else:
                yield crane_req
                self.env.process(self.move_containers_from_vessels(vessel_id))

            self.cranes.release(crane_req)

        self.berths.release(berth_request)
        vessel_turn_around_time = self.now() - arrival
        print(f"\nvessel: Vessel {vessel_id} leaving at time {self.now():.2f}")
        print(
            f"vessel: Vessel {vessel_id} turn_around time is {vessel_turn_around_time:.2f}\n")

    def move_container_to_yard(self, vessel_id, container_no):
        print(
            f"truck: Truck moving container {container_no} from vessel {vessel_id} at time {self.now():.2f}")
        yield self.env.timeout(TRUCK_TRIP_ROUND_TIME)
        print(
            f"truck: Truck returned after moving container {container_no} from vessel {vessel_id} at time {self.now():.2f}")


def vessel_generator(env):
    vessel = ContainerSimulation(env, AVAIL_BERTHS, AVAIL_CRANES, AVAIL_TRUCKS)
    vessel_id = 0
    while True:
        yield env.timeout(random.expovariate(1 / VESSEL_AVG_ARRIVAL_INTERVAL))
        vessel_id += 1
        env.process(vessel.move_containers_from_vessels(vessel_id))


if __name__ == '__main__':
    random.seed(RANDOM_SEED)
    simulation_days = int(input('Enter Simulation time(in days): '))
    SIMULATION_TIME = simulation_days * 24 * 60  # Converting to minutes
    print("Container Simulation: ")

    env = simpy.Environment()
    env.process(vessel_generator(env))

    env.run(until=SIMULATION_TIME)
