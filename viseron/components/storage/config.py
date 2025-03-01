"""Storage component configuration."""
from __future__ import annotations

from typing import Any, Literal, TypedDict

import voluptuous as vol

from viseron.components.storage.const import (
    COMPONENT,
    CONFIG_CHECK_INTERVAL,
    CONFIG_CONTINUOUS,
    CONFIG_DAYS,
    CONFIG_EVENTS,
    CONFIG_FACE_RECOGNITION,
    CONFIG_GB,
    CONFIG_HOURS,
    CONFIG_MAX_AGE,
    CONFIG_MAX_SIZE,
    CONFIG_MB,
    CONFIG_MIN_AGE,
    CONFIG_MIN_SIZE,
    CONFIG_MINUTES,
    CONFIG_MOVE_ON_SHUTDOWN,
    CONFIG_OBJECT_DETECTION,
    CONFIG_PATH,
    CONFIG_POLL,
    CONFIG_RECORDER,
    CONFIG_SECONDS,
    CONFIG_SNAPSHOTS,
    CONFIG_TIERS,
    DEFAULT_CHECK_INTERVAL,
    DEFAULT_CHECK_INTERVAL_DAYS,
    DEFAULT_CHECK_INTERVAL_HOURS,
    DEFAULT_CHECK_INTERVAL_MINUTES,
    DEFAULT_CHECK_INTERVAL_SECONDS,
    DEFAULT_CONTINUOUS,
    DEFAULT_DAYS,
    DEFAULT_EVENTS,
    DEFAULT_FACE_RECOGNITION,
    DEFAULT_GB,
    DEFAULT_HOURS,
    DEFAULT_MAX_AGE,
    DEFAULT_MAX_SIZE,
    DEFAULT_MB,
    DEFAULT_MIN_AGE,
    DEFAULT_MIN_SIZE,
    DEFAULT_MINUTES,
    DEFAULT_MOVE_ON_SHUTDOWN,
    DEFAULT_OBJECT_DETECTION,
    DEFAULT_POLL,
    DEFAULT_RECORDER,
    DEFAULT_RECORDER_TIERS,
    DEFAULT_SNAPSHOTS,
    DEFAULT_SNAPSHOTS_TIERS,
    DESC_CHECK_INTERVAL,
    DESC_CHECK_INTERVAL_DAYS,
    DESC_CHECK_INTERVAL_HOURS,
    DESC_CHECK_INTERVAL_MINUTES,
    DESC_CHECK_INTERVAL_SECONDS,
    DESC_CONTINUOUS,
    DESC_DOMAIN_TIERS,
    DESC_EVENTS,
    DESC_FACE_RECOGNITION,
    DESC_MAX_AGE,
    DESC_MAX_DAYS,
    DESC_MAX_GB,
    DESC_MAX_HOURS,
    DESC_MAX_MB,
    DESC_MAX_MINUTES,
    DESC_MAX_SIZE,
    DESC_MIN_AGE,
    DESC_MIN_DAYS,
    DESC_MIN_GB,
    DESC_MIN_HOURS,
    DESC_MIN_MB,
    DESC_MIN_MINUTES,
    DESC_MIN_SIZE,
    DESC_MOVE_ON_SHUTDOWN,
    DESC_OBJECT_DETECTION,
    DESC_PATH,
    DESC_POLL,
    DESC_RECORDER,
    DESC_RECORDER_TIERS,
    DESC_SNAPSHOTS,
    DESC_SNAPSHOTS_TIERS,
)
from viseron.components.storage.util import calculate_age
from viseron.config import UNSUPPORTED
from viseron.const import TEMP_DIR
from viseron.helpers.validators import CoerceNoneToDict, Maybe


def custom_convert(value) -> dict[str, str] | object:
    """Convert custom validators for the script gen_docs."""
    if isinstance(value, CoerceEndsWithSlash):
        return {
            "type": "string",
        }
    return UNSUPPORTED


class CoerceEndsWithSlash:
    """Validate that a path ends with slash."""

    def __init__(self) -> None:
        pass

    def __call__(self, value: str) -> str:
        """Validate that a path ends with slash."""
        if value == "/":
            return value
        if value[-1] != "/":
            return value + "/"
        return value


def get_size_schema(
    age_type: Literal["min"] | Literal["max"],
) -> dict[vol.Optional, Maybe]:
    """Get size schema."""
    return {
        vol.Optional(
            CONFIG_GB,
            default=DEFAULT_GB,
            description=DESC_MIN_GB if age_type == "min" else DESC_MAX_GB,
        ): Maybe(vol.Coerce(float)),
        vol.Optional(
            CONFIG_MB,
            default=DEFAULT_MB,
            description=DESC_MIN_MB if age_type == "min" else DESC_MAX_MB,
        ): Maybe(vol.Coerce(float)),
    }


def get_age_schema(
    age_type: Literal["min"] | Literal["max"],
) -> dict[vol.Optional, Maybe]:
    """Get age schema."""
    return {
        vol.Optional(
            CONFIG_DAYS,
            default=DEFAULT_DAYS,
            description=DESC_MIN_DAYS if age_type == "min" else DESC_MAX_DAYS,
        ): Maybe(vol.Coerce(int)),
        vol.Optional(
            CONFIG_HOURS,
            default=DEFAULT_HOURS,
            description=DESC_MIN_HOURS if age_type == "min" else DESC_MAX_HOURS,
        ): Maybe(vol.Coerce(int)),
        vol.Optional(
            CONFIG_MINUTES,
            default=DEFAULT_MINUTES,
            description=DESC_MIN_MINUTES if age_type == "min" else DESC_MAX_MINUTES,
        ): Maybe(vol.Coerce(int)),
    }


TIER_SCHEMA_BASE = vol.Schema(
    {
        vol.Optional(
            CONFIG_MIN_SIZE,
            default=DEFAULT_MIN_SIZE,
            description=DESC_MIN_SIZE,
        ): get_size_schema("min"),
        vol.Optional(
            CONFIG_MAX_SIZE,
            default=DEFAULT_MAX_SIZE,
            description=DESC_MAX_SIZE,
        ): get_size_schema("max"),
        vol.Optional(
            CONFIG_MAX_AGE,
            default=DEFAULT_MAX_AGE,
            description=DESC_MAX_AGE,
        ): get_age_schema("max"),
        vol.Optional(
            CONFIG_MIN_AGE,
            default=DEFAULT_MIN_AGE,
            description=DESC_MIN_AGE,
        ): get_age_schema("min"),
    }
)

TIER_SCHEMA_SNAPSHOTS = TIER_SCHEMA_BASE.extend(
    {
        vol.Required(
            CONFIG_PATH,
            description=DESC_PATH,
        ): str,
        vol.Optional(
            CONFIG_POLL,
            default=DEFAULT_POLL,
            description=DESC_POLL,
        ): bool,
        vol.Optional(
            CONFIG_MOVE_ON_SHUTDOWN,
            default=DEFAULT_MOVE_ON_SHUTDOWN,
            description=DESC_MOVE_ON_SHUTDOWN,
        ): bool,
        vol.Optional(
            CONFIG_CHECK_INTERVAL,
            default=DEFAULT_CHECK_INTERVAL,
            description=DESC_CHECK_INTERVAL,
        ): vol.All(
            CoerceNoneToDict(),
            {
                vol.Optional(
                    CONFIG_DAYS,
                    default=DEFAULT_CHECK_INTERVAL_DAYS,
                    description=DESC_CHECK_INTERVAL_DAYS,
                ): vol.All(int, vol.Range(min=0)),
                vol.Optional(
                    CONFIG_HOURS,
                    default=DEFAULT_CHECK_INTERVAL_HOURS,
                    description=DESC_CHECK_INTERVAL_HOURS,
                ): vol.All(int, vol.Range(min=0)),
                vol.Optional(
                    CONFIG_MINUTES,
                    default=DEFAULT_CHECK_INTERVAL_MINUTES,
                    description=DESC_CHECK_INTERVAL_MINUTES,
                ): vol.All(int, vol.Range(min=0)),
                vol.Optional(
                    CONFIG_SECONDS,
                    default=DEFAULT_CHECK_INTERVAL_SECONDS,
                    description=DESC_CHECK_INTERVAL_SECONDS,
                ): vol.All(int, vol.Range(min=0)),
            },
        ),
    }
)

TIER_SCHEMA_RECORDER = vol.Schema(
    {
        vol.Required(
            CONFIG_PATH,
            description=DESC_PATH,
        ): vol.All(str, CoerceEndsWithSlash()),
        vol.Optional(
            CONFIG_POLL,
            default=DEFAULT_POLL,
            description=DESC_POLL,
        ): bool,
        vol.Optional(
            CONFIG_MOVE_ON_SHUTDOWN,
            default=DEFAULT_MOVE_ON_SHUTDOWN,
            description=DESC_MOVE_ON_SHUTDOWN,
        ): bool,
        vol.Optional(
            CONFIG_CHECK_INTERVAL,
            default=DEFAULT_CHECK_INTERVAL,
            description=DESC_CHECK_INTERVAL,
        ): vol.All(
            CoerceNoneToDict(),
            {
                vol.Optional(
                    CONFIG_DAYS,
                    default=DEFAULT_CHECK_INTERVAL_DAYS,
                    description=DESC_CHECK_INTERVAL_DAYS,
                ): vol.All(int, vol.Range(min=0)),
                vol.Optional(
                    CONFIG_HOURS,
                    default=DEFAULT_CHECK_INTERVAL_HOURS,
                    description=DESC_CHECK_INTERVAL_HOURS,
                ): vol.All(int, vol.Range(min=0)),
                vol.Optional(
                    CONFIG_MINUTES,
                    default=DEFAULT_CHECK_INTERVAL_MINUTES,
                    description=DESC_CHECK_INTERVAL_MINUTES,
                ): vol.All(int, vol.Range(min=0)),
                vol.Optional(
                    CONFIG_SECONDS,
                    default=DEFAULT_CHECK_INTERVAL_SECONDS,
                    description=DESC_CHECK_INTERVAL_SECONDS,
                ): vol.All(int, vol.Range(min=0)),
            },
        ),
        vol.Optional(
            CONFIG_CONTINUOUS,
            default=DEFAULT_CONTINUOUS,
            description=DESC_CONTINUOUS,
        ): vol.All(CoerceNoneToDict(), TIER_SCHEMA_BASE),
        vol.Optional(
            CONFIG_EVENTS,
            default=DEFAULT_EVENTS,
            description=DESC_EVENTS,
        ): vol.All(CoerceNoneToDict(), TIER_SCHEMA_BASE),
    }
)

STORAGE_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONFIG_RECORDER,
            default=DEFAULT_RECORDER,
            description=DESC_RECORDER,
        ): {
            vol.Optional(
                CONFIG_TIERS,
                default=DEFAULT_RECORDER_TIERS,
                description=DESC_RECORDER_TIERS,
            ): vol.All(
                [TIER_SCHEMA_RECORDER],
                vol.Length(min=1),
            ),
        },
        vol.Optional(
            CONFIG_SNAPSHOTS,
            default=DEFAULT_SNAPSHOTS,
            description=DESC_SNAPSHOTS,
        ): {
            vol.Optional(
                CONFIG_TIERS,
                default=DEFAULT_SNAPSHOTS_TIERS,
                description=DESC_SNAPSHOTS_TIERS,
            ): vol.All(
                [TIER_SCHEMA_SNAPSHOTS],
                vol.Length(min=1),
            ),
            vol.Optional(
                CONFIG_FACE_RECOGNITION,
                default=DEFAULT_FACE_RECOGNITION,
                description=DESC_FACE_RECOGNITION,
            ): Maybe(
                {
                    vol.Required(CONFIG_TIERS, description=DESC_DOMAIN_TIERS): vol.All(
                        [TIER_SCHEMA_SNAPSHOTS],
                        vol.Length(min=1),
                    ),
                }
            ),
            vol.Optional(
                CONFIG_OBJECT_DETECTION,
                default=DEFAULT_OBJECT_DETECTION,
                description=DESC_OBJECT_DETECTION,
            ): Maybe(
                {
                    vol.Required(CONFIG_TIERS, description=DESC_DOMAIN_TIERS): vol.All(
                        [TIER_SCHEMA_SNAPSHOTS],
                        vol.Length(min=1),
                    ),
                }
            ),
        },
    }
)


def _check_tier(tier: Tier, previous_tier: Tier | None, paths: list[str]):
    """Check tier config."""
    if tier[CONFIG_PATH] in ["/tmp", TEMP_DIR]:
        raise vol.Invalid(
            f"Tier {tier[CONFIG_PATH]} is a reserved path and cannot be used"
        )

    if tier[CONFIG_PATH] in paths:
        raise vol.Invalid(f"Tier {tier[CONFIG_PATH]} is defined multiple times")
    paths.append(tier[CONFIG_PATH])

    if previous_tier is None:
        return

    tier_max_age = calculate_age(tier[CONFIG_MAX_AGE]).total_seconds()
    previous_tier_max_age = calculate_age(previous_tier[CONFIG_MAX_AGE]).total_seconds()

    if (
        tier_max_age > 0  # pylint: disable=chained-comparison
        and tier_max_age <= previous_tier_max_age
    ):
        raise vol.Invalid(
            f"Tier {tier[CONFIG_PATH]} "
            "max_age must be greater than previous tier max_age"
        )


class Tier(TypedDict):
    """Tier."""

    path: str
    max_age: dict[str, Any]


def validate_tiers(config: dict[str, Any]) -> dict[str, Any]:
    """Validate tiers.

    Paths cannot be reserved paths.
    The same path cannot be defined multiple times.
    max_age has to be greater than previous tier max_age.
    """
    component_config: dict[str, Any] = config[COMPONENT]

    # Check events config
    previous_tier: None | Tier = None
    paths: list[str] = []
    for tier in component_config.get(CONFIG_RECORDER, {}).get(CONFIG_TIERS, []):
        if tier.get(CONFIG_EVENTS, None):
            _tier = Tier(
                path=tier[CONFIG_PATH], max_age=tier[CONFIG_EVENTS][CONFIG_MAX_AGE]
            )
            _check_tier(
                _tier,
                previous_tier,
                paths,
            )
            previous_tier = _tier

    # Check continuous config
    previous_tier = None
    paths = []
    for tier in component_config.get(CONFIG_RECORDER, {}).get(CONFIG_TIERS, []):
        if tier.get(CONFIG_CONTINUOUS, None):
            _tier = Tier(
                path=tier[CONFIG_PATH], max_age=tier[CONFIG_CONTINUOUS][CONFIG_MAX_AGE]
            )
            _check_tier(
                _tier,
                previous_tier,
                paths,
            )
            previous_tier = _tier

    return config
