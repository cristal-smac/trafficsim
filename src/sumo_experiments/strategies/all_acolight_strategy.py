from sumo_experiments.strategies import Strategy
from sumo_experiments.agents import AcolightAgent


class AcolightStrategy(Strategy):
    """
    Implement a acolight agent for all intersections of the network.
    """

    def __init__(self,
                 infrastructures,
                 detectors,
                 min_phases_durations,
                 max_phases_durations,
                 delta,
                 yellow_times,
                 activate_asymetric_saturation=True):
        """
        Init of class.
        :param infrastructures: The infrastructures of the network
        :type infrastructures: InfrastructureBuilder
        :param detectors: The detectors of the network
        :type detectors: DetectorBuilder
        :param min_phases_durations: The minimum durations of each traffic light phase (except yellow phases). Can't be None.
        :type min_phases_durations: dict
        :param max_phases_durations: Maximum duration of each phases for all intersections
        :type max_phases_durations: dict
        :param delta: The time added or removed from the maximum phase duration when conditions are met.
        :type delta: dict
        :param yellow_times: Yellow phases duration for all intersections
        :type yellow_times: dict
        :param activate_asymetric_saturation: True to activate the asymetric saturation behaviour
        :type: bool
        """
        super().__init__(infrastructures, detectors)
        self.agents = self._generate_agents(min_phases_durations, max_phases_durations, delta, yellow_times, activate_asymetric_saturation)

    def run_all_agents(self):
        """
        Process agents to make one action each.
        :return: Nothing
        """
        for agent in self.agents:
            agent.choose_action()

    def _generate_agents(self, min_phases_durations, max_phases_durations, delta, yellow_times, activate_asymetric_saturation):
        """
        Generate all agents for the strategy.
        :param min_phases_durations: The minimum durations of each traffic light phase (except yellow phases). Can't be None.
        :type min_phases_durations: dict
        :param max_phases_durations: The maximum duration for each green phases for all traffic light nodes
        :type max_phases_durations: dict
        :param delta: The time added or removed from the maximum phase duration when conditions are met.
        :type delta: dict
        :param yellow_times: Yellow phases duration for all intersections
        :type yellow_times: dict
        :param activate_asymetric_saturation: True to activate the asymetric saturation behaviour
        :type: bool
        :return: All the agents of the network
        :rtype: list
        """
        agents = []
        for intersection in self.relations:
            agent = AcolightAgent(id_intersection=intersection,
                                  id_tls_program=self.relations[intersection]['node_infos'].tl,
                                  min_phases_durations=min_phases_durations[intersection],
                                  max_phases_durations=max_phases_durations[intersection],
                                  delta=delta[intersection],
                                  yellow_time=yellow_times[intersection],
                                  intersection_relations=self.relations[intersection],
                                  activate_asymetric_saturation=activate_asymetric_saturation)
            agents.append(agent)
        return agents