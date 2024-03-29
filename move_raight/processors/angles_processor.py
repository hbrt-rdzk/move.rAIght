import os

import numpy as np
import pandas as pd
from models.angle import ANGLE_PARAMETERS_NUM, Angle
from models.joint import Joint
from processors.base import Processor


class AnglesProcessor(Processor):
    def __init__(self, angle_names: dict) -> None:
        super().__init__()
        self.angle_names = angle_names

    def __len__(self) -> int:
        return len(self.data) * ANGLE_PARAMETERS_NUM

    def process(self, data: list[Joint]) -> list[Angle]:
        frame_number = data[0].frame
        joint_dict = {joint.id: [joint.x, joint.y, joint.z] for joint in data}

        angles = []
        for angle_name, joint_ids in self.angle_names.items():
            coords = np.array([joint_dict[joint_id] for joint_id in joint_ids])
            angle = self.__calculate_3D_angle(*coords)
            angles.append(Angle(frame_number, angle_name, angle))

        return angles

    def update(self, data: list[Angle]) -> None:
        self.data.extend(data)

    @staticmethod
    def to_df(data: list[Angle]) -> pd.DataFrame:
        return pd.DataFrame(data)

    @staticmethod
    def from_df(data: pd.DataFrame) -> list[Angle]:
        angles = []
        for _, angle in data.iterrows():
            angles.append(Angle(angle["frame"], angle["name"], angle["value"]))
        return angles

    def save(self, output_dir: str) -> None:
        output = self._validate_output(output_dir)
        angles_df = self.to_df(self.data)

        results_path = os.path.join(output, "angles.csv")
        angles_df.to_csv(results_path, index=False)

    @staticmethod
    def __calculate_3D_angle(A: np.ndarray, B: np.ndarray, C: np.ndarray) -> float:
        if not (A.shape == B.shape == C.shape == (3,)):
            raise ValueError("Input arrays must all be of shape (3,).")

        ba = A - B
        bc = C - B

        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        cosine_angle = np.clip(cosine_angle, -1, 1)
        angle = np.arccos(cosine_angle)

        return np.degrees(angle)
