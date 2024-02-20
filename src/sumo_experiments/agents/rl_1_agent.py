import random

from sumo_experiments.agents import Agent
import traci
import numpy as np
from keras.layers import Dense
from keras.models import Sequential
from keras.optimizers import RMSprop
from keras.losses import mean_squared_error


class RLAgent1(Agent):
    """
    Implements a RL agent, inspired by the Intellilight system described by Wei et al in [1].
    This system implement the same state representation as Intelillight, except the image representation of position of cars.
    The neural network used to predict the Q-value is a basic two fully connected layer network.
    The reward of the system is the delay on all lanes (see [1]), multiplied by the total amount of vehicules detected.


    [1] Wei, H., Zheng, G., Yao, H., & Li, Z. (2018, July). Intellilight: A reinforcement learning approach for intelligent traffic light control. In Proceedings of the 24th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining (pp. 2496-2505).
    """

    ACTION_DIMENSION = 2

    def __init__(self,
                 id_intersection,
                 id_tls_program,
                 intersection_relations,
                 length_detector,
                 yellow_time=None,
                 epsilon=1,
                 epsilon_updater=0.999,
                 min_epsilon=0.01,
                 decreasing_episode=30,
                 episode_length=60,
                 max_batch_size=30,
                 gamma=0.9,
                 nb_epochs=100,
                 frequence_target_network_update=5):
        """
        Init of class.
        :param id_intersection: The id of the intersection the agent will control
        :type id_intersection: str
        :param id_tls_program: The id of the traffic light program related to the intersection
        :type id_tls_program: str
        :param intersection_relations: The relations for this intersection.
        :type intersection_relations: dict
        :param yellow_time: The duration of yellow phases. If None, yellow phase will remain as declared in the network definition.
        :type yellow_time: dict
        :param epsilon: Epsilon value for the greedy action selection at the beginning of the simulation. Must be between 0 and 1 included.
        :type epsilon: float
        :param epsilon_updater: Coefficient that will be used to compute the new epsilon after each selection, if the episode number is greater than decreasing_episode. Must be between 0 and 1 included.
        :type epsilon_updater: float
        :param min_epsilon: Minimum value for epsilon. Must be between 0 and 1 included.
        :type min_epsilon: float
        :param decreasing_episode: The episode where epsilon value will start to decrease.
        :type decreasing_episode: int
        :param episode_length: Length of an episode, in number of simulation steps.
        :type episode_length: int
        :param max_batch_size: The maximum size of the batch to fit the model. Must be lower than the episode length.
        :type max_batch_size: int
        :param gamma: Discount factor to compute the Q value. Must be between 0 and 1 included.
        :type gamma: float
        :param nb_epochs: Number of epochs for main network fitting.
        :type nb_epochs: int
        :param frequence_target_network_update: Frequence (in number of episodes) when the target network will be updated with the main network weights.
        :type frequence_target_network_update: int
        """
        super().__init__()
        self.started = False
        self.id_intersection = id_intersection
        self.id_tls_program = id_tls_program
        self.relations = intersection_relations
        self.length_detector = length_detector
        self.yellow_time = yellow_time
        self.epsilon = epsilon
        self.epsilon_updater = epsilon_updater
        self.min_epsilon = min_epsilon
        self.decreasing_episode = decreasing_episode
        self.episode_length = episode_length
        self.max_batch_size = max_batch_size
        self.gamma = gamma
        self.nb_epochs = nb_epochs
        self.frequence_target_network_update = frequence_target_network_update

        self.current_phase = 0
        self.countdown = 0
        self.time_countdown = 0
        self.current_episode = 0
        self.replay_buffer = []
        self.previous_action = 0

    def choose_action(self):
        """
        Choose and perform the action selected for the current state.
        :return: True if the traffic light switched, False otherwise
        :rtype: bool
        """
        if not self.started:
            self._start_agent()
            return True
        self.countdown += 1
        if self.countdown >= self.episode_length:
            self._train_model()
            self.countdown = 0
            self.current_episode += 1
        if 'y' not in traci.trafficlight.getRedYellowGreenState(self.id_tls_program):
            reward = self._get_reward()
            current_state = self._get_state_values()
            self.replay_buffer.append((self.previous_state, self.previous_action, reward, current_state))
            self.previous_state = current_state

            # Select the action to perform : 0 means the phase remains the same, 1 means we pass to the next phase
            next_action = self._select_action()
            self.previous_action = next_action
            if next_action == 1:
                traci.trafficlight.setPhase(self.id_tls_program, traci.trafficlight.getPhase(self.id_tls_program) + 1)
                return True
        return False

    def get_weights(self):
        """
        Return the weights of the main network.
        :return: The weights of the main neural network
        """
        self.main_network.get_weights()

    def _select_action(self):
        """
        Select the action to perform, i.e. stay at the current phase or switch to another one.
        A epsilon-greedy approch is used to select the action.
        :return: The action to perform
        :rtype: int
        """
        state = self._get_state_values()
        if self.current_episode < 1:
            return np.random.choice(self.ACTION_DIMENSION)
        # Decreasing epsilon
        if self.current_episode > self.decreasing_episode and self.epsilon > self.min_epsilon:
            self.epsilon = self.epsilon_updater * self.epsilon
        # Select a random number between 0 and 1
        random_number = np.random.random()
        # Exploration choice
        if random_number < self.epsilon:
            # returns a random action selected from: 0,1,...,actionNumber-1
            return np.random.choice(self.ACTION_DIMENSION)
        # Exploitation choice
        else:
            Qvalues = self.main_network.predict(state.reshape(1, -1), verbose=0)
            return np.random.choice(np.where(Qvalues[0, :] == np.max(Qvalues[0, :]))[0])

    def _train_model(self):
        """
        Train the network with the given results stacked in the replay buffer.
        :return: None
        """
        batch_size = self.max_batch_size if len(self.replay_buffer) > self.max_batch_size else len(self.replay_buffer)
        # Create training batch from a replay buffer sampling
        randomized_batch = random.sample(self.replay_buffer, batch_size)
        current_state_batch = np.zeros(shape=(batch_size, self.state_dimension))
        next_state_batch = np.zeros(shape=(batch_size, self.state_dimension))
        # We add in the corresponding arrays the current states and next states
        for index, item in enumerate(randomized_batch):
            current_state_batch[index, :] = item[0]
            next_state_batch[index, :] = item[3]
        # We compute QValues of next states with the target network
        Q_next_state = self.target_network.predict(next_state_batch, verbose=0)
        # Creating data to fit neural networks
        input_data = current_state_batch
        output_data = np.zeros(shape=(batch_size, self.ACTION_DIMENSION))
        for index, (currentState, action, reward, nextState) in enumerate(randomized_batch):
            y = reward + self.gamma * np.max(Q_next_state[index])
            output_data[index, action] = y
        # Train model
        self.main_network.fit(input_data, output_data, batch_size=batch_size, verbose=0, epochs=self.nb_epochs)
        # Update target network occasionally
        if self.current_episode % self.frequence_target_network_update == 0:
            self.target_network.set_weights(self.main_network.get_weights())
        # Clear replay buffer
        self.replay_buffer = []

    def _get_state_values(self):
        """
        Get the values required to compute the current state of the agent, i.e. the demand for each phase and the current phase.
        :return: The current state
        :rtype: numpy.Array
        """
        queue_lengths = self._get_queue_lengths()
        vehicle_numbers = self._get_number_of_vehicles()
        waiting_times = self._get_waiting_time()
        phase = self._get_phase()
        state = np.array(queue_lengths + waiting_times + phase + vehicle_numbers)
        return state

    def _get_queue_lengths(self):
        """
        Get the queue length for each entry of the intersection.
        :return: The queue length for all entry
        :rtype: list
        """
        queue_lengths = []
        for edge in self.relations['related_edges']:
            index_edge = self.relations['related_edges'].index(edge)
            queue_length = 0
            for detector in self.relations['related_numerical_detectors'][index_edge]:
                queue_length += traci.lanearea.getJamLengthVehicle(detector.id)
            queue_lengths.append(queue_length)
        return queue_lengths

    def _get_number_of_vehicles(self):
        """
        Get the total number of vehicles detected on every entry
        :return: The number of vehicle for each entry
        :rtype: list
        """
        nb_vehicles = []
        for edge in self.relations['related_edges']:
            index_edge = self.relations['related_edges'].index(edge)
            nb = 0
            for detector in self.relations['related_numerical_detectors'][index_edge]:
                nb += traci.lanearea.getLastStepVehicleNumber(detector.id)
            nb_vehicles.append(nb)
        return nb_vehicles

    def _get_waiting_time(self):
        """
        Compute the waiting times for each entry of the intersection.
        :return: The waiting time
        :rtype: list
        """
        waiting_times = []
        for edge in self.relations['related_edges']:
            lane_number = traci.edge.getLaneNumber(edge)
            waiting_time = 0
            for lane in [edge + f'_{i}' for i in range(lane_number)]:
                waiting_time += int(traci.lane.getWaitingTime(lane))
            waiting_times.append(waiting_time)
        return waiting_times

    def _get_phase(self):
        """
        Get the phase in a vector form, where each number represents a lane and 1, 0 respectively indicate if TL is green or red.
        :return: The phase
        :rtype: list
        """
        current_phase = traci.trafficlight.getRedYellowGreenState(self.id_tls_program)
        phase = [1 if color == 'G' or color == 'g' else 0 for color in current_phase]
        return phase

    def _get_mean_delay(self):
        """
        Compute the mean entry lane delay of the intersection.
        :return: The mean delay
        :rtype: float
        """
        mean_speeds = []
        speed_limitations = []
        for detectors in self.relations['related_numerical_detectors']:
            for detector in detectors:
                mean_speeds.append(traci.lanearea.getLastStepMeanSpeed(detector.id))
        for edge in self.relations['related_edges']:
            nb_lanes = traci.edge.getLaneNumber(edge)
            for i in range(nb_lanes):
                lane = f'{edge}_{i}'
                speed_limitations.append(traci.lane.getMaxSpeed(lane))
        delays = [1 - (mean_speeds[i] / speed_limitations[i]) for i in range(len(mean_speeds))]
        return sum(delays)

    def _get_reward(self):
        """
        Compute the reward based on the condition from this step.
        :return: The reward
        :rtype: float
        """
        delay = self._get_mean_delay()
        number_of_vehicle = sum(self._get_number_of_vehicles())
        return - delay * number_of_vehicle

    def _create_network(self):
        """
        Create the neural network for the agent.
        :return: The neural network of the agent
        :rtype: keras.Sequential
        """
        model = Sequential()
        model.add(Dense(128, input_dim=self.state_dimension, activation='relu'))
        model.add(Dense(56, activation='relu'))
        model.add(Dense(self.ACTION_DIMENSION, activation='linear'))
        model.compile(optimizer=RMSprop(), loss=mean_squared_error, metrics=['accuracy'])
        return model

    def _start_agent(self):
        """
        Start an agent at the beginning of the simulation.
        """
        self.nb_phases = len(traci.trafficlight.getAllProgramLogics(self.id_tls_program)[0].phases)
        self.phases_index = {}
        tl_logic = traci.trafficlight.getAllProgramLogics(self.id_tls_program)[0]
        phase_index = 0
        nb_phase = 0
        for phase in tl_logic.phases:
            if 'y' in phase.state:
                if self.yellow_time is not None:
                    phase.duration = self.yellow_time
                    phase.minDur = self.yellow_time
                    phase.maxDur = self.yellow_time
            else:
                phase.duration = 10000
                phase.maxDur = 10000
                phase.minDur = 10000
                self.phases_index[nb_phase] = phase_index
                phase_index += 1
            nb_phase += 1
        traci.trafficlight.setProgramLogic(self.id_tls_program, tl_logic)
        traci.trafficlight.setPhase(self.id_tls_program, 0)
        traci.trafficlight.setPhaseDuration(self.id_tls_program, 10000)
        # Get number of inputs
        queue_lengths = self._get_queue_lengths()
        vehicle_numbers = self._get_number_of_vehicles()
        waiting_times = self._get_waiting_time()
        phase = self._get_phase()
        self.state_dimension = len(queue_lengths) + len(vehicle_numbers) + len(waiting_times) + len(phase)
        self.main_network = self._create_network()
        self.target_network = self._create_network()
        self.previous_state = self._get_state_values()
        self.started = True


if __name__ == "__main__":
    phase_1_is_current = [0, 0, 1, 0, 1]
    phase_2_is_current = []
