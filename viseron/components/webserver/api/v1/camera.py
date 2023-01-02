"""Camera API Handler."""
from __future__ import annotations

import logging

import voluptuous as vol

from viseron.components.webserver.api import BaseAPIHandler
from viseron.components.webserver.const import (
    STATUS_ERROR_ENDPOINT_NOT_FOUND,
    STATUS_ERROR_INTERNAL,
)
from viseron.domains.camera.const import DOMAIN as CAMERA_DOMAIN
from viseron.exceptions import DomainNotRegisteredError

LOGGER = logging.getLogger(__name__)


class CameraAPIHandler(BaseAPIHandler):
    """Handler for API calls related to a camera."""

    routes = [
        {
            "path_pattern": r"/camera/(?P<camera_identifier>[A-Za-z0-9_]+)/snapshot",
            "supported_methods": ["GET"],
            "method": "get_snapshot",
            "request_arguments_schema": vol.Schema(
                {
                    vol.Optional("rand", default=None): vol.Maybe(str),
                    vol.Optional("width", default=None): vol.Maybe(vol.Coerce(int)),
                    vol.Optional("height", default=None): vol.Maybe(vol.Coerce(int)),
                },
            ),
        },
        {
            "path_pattern": r"/camera/(?P<camera_identifier>[A-Za-z0-9_]+)",
            "supported_methods": ["GET"],
            "method": "get_camera",
        },
        {
            "path_pattern": (
                r"/camera/(?P<camera_identifier>[A-Za-z0-9_]+)"
                r"/recording"
                r"/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
                r"/(?P<filename>.*\..*)"
            ),
            "supported_methods": ["DELETE"],
            "method": "delete_recording",
        },
        {
            "path_pattern": (
                r"/camera/(?P<camera_identifier>[A-Za-z0-9_]+)"
                r"/recording"
                r"/(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
            ),
            "supported_methods": ["DELETE"],
            "method": "delete_recording",
        },
        {
            "path_pattern": (
                r"/camera/(?P<camera_identifier>[A-Za-z0-9_]+)" r"/recording"
            ),
            "supported_methods": ["DELETE"],
            "method": "delete_recording",
        },
    ]

    def _get_camera(self, camera_identifier: str):
        """Get camera instance."""
        try:
            return self._vis.get_registered_domain(CAMERA_DOMAIN, camera_identifier)
        except DomainNotRegisteredError:
            return None

    def get_snapshot(self, camera_identifier: bytes):
        """Return camera snapshot."""
        camera = self._get_camera(camera_identifier.decode())

        if not camera or not camera.current_frame:
            self.response_error(
                STATUS_ERROR_ENDPOINT_NOT_FOUND,
                reason=f"Camera {camera_identifier.decode()} not found",
            )
            return

        ret, jpg = camera.get_snapshot(
            camera.current_frame,
            self.request_arguments["width"],
            self.request_arguments["height"],
        )

        if ret:
            self.response_success(response=jpg, headers={"Content-Type": "image/jpeg"})
            return
        self.response_error(
            STATUS_ERROR_INTERNAL, reason="Could not fetch camera snapshot"
        )
        return

    def get_camera(self, camera_identifier: bytes):
        """Return camera."""
        camera = self._get_camera(camera_identifier.decode())

        if not camera:
            self.response_error(
                STATUS_ERROR_ENDPOINT_NOT_FOUND,
                reason=f"Camera {camera_identifier.decode()} not found",
            )
            return

        self.response_success(camera.as_dict())
        return

    def delete_recording(
        self, camera_identifier: bytes, date: bytes = None, filename: bytes = None
    ):
        """Delete recording(s)."""
        camera = self._get_camera(camera_identifier.decode())

        if not camera:
            self.response_error(
                STATUS_ERROR_ENDPOINT_NOT_FOUND,
                reason=f"Camera {camera_identifier.decode()} not found",
            )
            return

        # Try to delete recording
        if camera.delete_recording(
            date.decode() if date else date,
            filename.decode() if filename else filename,
        ):
            self.response_success()
            return
        self.response_error(
            STATUS_ERROR_INTERNAL,
            reason=(f"Failed to delete recording. Date={date!r} filename={filename!r}"),
        )
        return
