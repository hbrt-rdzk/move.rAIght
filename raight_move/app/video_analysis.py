import os

import cv2
import pandas as pd
from app.base import POSE_ESTIMATION_MODEL_NAME, App
from processors.angles_processor import AnglesProcessor
from processors.joints_processor import JointsProcessor
from processors.results_processor import ResultsProcessor
from processors.segments_processor import SegmentsProcessor

PATH_TO_REFERENCE = "data/{exercise}/features/reference"


class VideoAnalysisApp(App):
    """
    More advanced whole video analysis.
    """

    def __init__(self, exercise: str) -> None:
        super().__init__()
        self.segmentation_parameters = self._config_data["segmentation_parameters"]
        model_config_data = self._config_data[POSE_ESTIMATION_MODEL_NAME]

        self.angle_names = model_config_data["angles"]
        self.joint_names = model_config_data["joints"]
        self.connections = model_config_data["connections"]["torso"]

        reference_joints = pd.read_csv(
            os.path.join(PATH_TO_REFERENCE.format(exercise=exercise), "joints.csv")
        )
        reference_angles = pd.read_csv(
            os.path.join(PATH_TO_REFERENCE.format(exercise=exercise), "angles.csv")
        )
        self.reference_segment = SegmentsProcessor.from_df(
            (reference_joints, reference_angles)
        )

    def run(self, input: str, output: str, save_results: bool) -> None:
        joints_processor = JointsProcessor(self.joint_names)
        angles_processor = AnglesProcessor(self.angle_names)
        results_processor = ResultsProcessor()

        cap = cv2.VideoCapture(input)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        segments_processor = SegmentsProcessor(fps, self.segmentation_parameters)

        if not cap.isOpened():
            self.logger.critical("❌ Error on opening video stream or file! ❌")
            return

        self.logger.info("Starting features extraction from video... 🎬")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = self._pose_estimation_model.process(frame)
            world_landmards = results.pose_world_landmarks

            if world_landmards:
                # Joints processing
                joints = joints_processor.process(world_landmards)
                joints_processor.update(joints)

                # Angle processing
                angles = angles_processor.process(joints)
                angles_processor.update(angles)
        cap.release()

        analysis_info = (
            f"Analyzed {video_length} frames 🖼️"
            f", extracted {len(joints_processor)} joint features 💪 and"
            f" {len(angles_processor)} angle features 📐"
        )
        self.logger.info(analysis_info)

        segments = segments_processor.process(
            data=(joints_processor.data, angles_processor.data)
        )
        segments_processor.update(segments)

        segments_info = {
            f"repetition {segment.rep}": f"frames: [{segment.start_frame}; {segment.finish_frame}]"
            for segment in segments
        }
        self.logger.info(f"Segmented video frames: {segments_info}")

        for segment in segments:
            self.logger.info(
                f"Starting comparison with reference video for rep: {segment.rep}... 🔥"
            )
            results = segments_processor.compare_segments(
                segment, self.reference_segment
            )
            fine_results = results_processor.process(results)
            results_processor.update(fine_results)
        self.logger.info("Analysis complete! ✅")
        if save_results:
            try:
                results_processor.save(output)
                self.logger.info(f"Results here: {output} 💽")
            except ValueError as error:
                self.logger.critical(f"Error on trying to save results:\n{error}")
