import numpy as np

from src.processors.abstract_handler import DataHandler


class RepetitionsHandler(DataHandler):
    def __init__(self, exercise: str) -> None:
        super().__init__()
        self.__exercise_phases = self._reference_table[exercise]["phases"]
        self.start_angles = self.__exercise_phases["start"]
        self.finish_angles = self.__exercise_phases["finish"]

        self.repetitions = 0
        self.progress = 0.0
        self.state = "up"

    def load_data(self, data: dict) -> list:
        reference_angle_names = [angle_name for angle_name in self.start_angles.keys()]
        start_reference_angles = np.array(
            [angle_name for angle_name in self.start_angles.values()]
        )
        finish_reference_angles = np.array(
            [angle_name for angle_name in self.finish_angles.values()]
        )

        data_angles = np.array(
            [data[angle_name] for angle_name in reference_angle_names]
        )

        reference_progress = start_reference_angles[0] - finish_reference_angles[0]

        progress = np.mean(start_reference_angles - data_angles)
        progress_normalized = progress / reference_progress
        return np.clip(progress_normalized, 0, 1)

    def update(self, progress) -> None:
        self.progress = progress

        if progress >= 1.0 and self.state == "up":
            self.state = "down"
        elif progress <= 0.0 and self.state == "down":
            self.repetitions += 1
            self.state = "up"

    def save(self) -> None:
        ...
