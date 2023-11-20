from agent import Agent
import traci


class FixedTimeAgent(Agent):
    """
    Implements a fixed time agent. The agent has fixed time for each phase and switch to the next phase when this
    time is over.
    """

    def __init__(self, id_intersection, id_tls_program, phases_durations):
        """
        Init of class.
        :param id_intersection: The id of the intersection the agent will control
        :type id_intersection: str
        :param id_tls_program: The id of the traffic light program related to the intersection
        :type id_tls_program: str
        :param phases_durations: The durations of each traffic light phase (length = number of phases)
        :type phases_durations: iterable object
        """
        super().__init__()
        self.id_intersection = id_intersection
        self.phases_durations = phases_durations
        self.current_phase = 0
        self.countdown = 0
        self.nb_phases = len(phases_durations)
        self.id_tls_program = id_tls_program

    def choose_action(self):
        """
        Switch to the next phase when countdown is equal to the current phase duration.
        :return: True if the agent switched to another phase, False otherwise
        :rtype: bool
        """
        if self.countdown >= self.phases_durations[self.current_phase]:
            self.current_phase += 1
            self.countdown = 0
            traci.trafficlight.setPhase(self.id_tls_program, self.current_phase % self.nb_phases)
            traci.trafficlight.setPhaseDuration(self.id_tls_program, self.phases_durations[self.current_phase + 5])
        else:
            self.countdown += 1

