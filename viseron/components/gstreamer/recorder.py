"""Recorder."""
from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from viseron.components.ffmpeg.recorder import ConcatThreadsContext
from viseron.components.ffmpeg.segments import SegmentCleanup, Segments
from viseron.domains.camera.recorder import AbstractRecorder

from .const import COMPONENT, RECORDER

if TYPE_CHECKING:
    from viseron import Viseron
    from viseron.domains.camera import AbstractCamera
    from viseron.domains.camera.recorder import Recording
LOGGER = logging.getLogger(__name__)


class Recorder(AbstractRecorder):
    """Creates thumbnails and recordings."""

    def __init__(self, vis: Viseron, config, camera: AbstractCamera) -> None:
        super().__init__(vis, COMPONENT, config, camera)
        self._logger.debug("Initializing gstreamer recorder")
        self._recorder_config = config[RECORDER]

        self._segment_thread_context = ConcatThreadsContext()
        self._concat_thread_lock = threading.Lock()

        self._segmenter = Segments(
            self._logger, config, vis, camera, self.segments_folder
        )
        self._segment_cleanup = SegmentCleanup(
            vis,
            self._recorder_config,
            self._logger,
            self._segment_thread_context,
            self.segments_folder,
        )

    def concat_segments(self, recording: Recording) -> None:
        """Concatenate GStreamer segments to a single video."""
        with self._segment_thread_context:
            with self._concat_thread_lock:
                self._segment_cleanup.pause()
                self._segmenter.concat_segments(recording)

                # Dont resume cleanup if new recording started during encoding
                if not self.is_recording:
                    self._segment_cleanup.resume()

    def _start(self, recording, shared_frame, objects_in_fov, resolution) -> None:
        self._segment_cleanup.pause()

    def _stop(self, recording) -> None:
        concat_thread = threading.Thread(target=self.concat_segments, args=(recording,))
        concat_thread.start()
