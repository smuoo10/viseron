import dayjs, { Dayjs } from "dayjs";
import { Fragment } from "hls.js";

import { BLANK_IMAGE, dateToTimestamp } from "lib/helpers";
import * as types from "lib/types";

export const TICK_HEIGHT = 8;
export const SCALE = 60;
export const EXTRA_TICKS = 10;
export const COLUMN_HEIGHT = "99dvh";
export const EVENT_ICON_HEIGHT = 20;

export const DEFAULT_ITEM: TimelineItem = {
  time: 0,
  timedEvent: null,
  snapshotEvents: null,
  availableTimespan: null,
  activityLineVariant: null,
};

export type TimelineItem = {
  time: number;
  timedEvent: null | types.CameraMotionEvent | types.CameraRecordingEvent;
  snapshotEvents: null | types.CameraSnapshotEvents;
  availableTimespan: null | types.HlsAvailableTimespan;
  activityLineVariant: "first" | "middle" | "last" | "round" | null;
};

export type TimelineItems = {
  [key: string]: TimelineItem;
};

// Get a Date object that corresponds to 'position'
export const getDateAtPosition = (
  position: number,
  height: number,
  startRef: React.MutableRefObject<number>,
  endRef: React.MutableRefObject<number>,
) => {
  // Calculate the percentage of cursor position within the container
  const percentage = position / height;

  // First time tick is preceded by a margin of half the time tick height
  // so we add half the scale to get the correct time
  const _start = startRef.current * 1000 + (SCALE * 1000) / 2;
  // Last time tick is followed by a margin of half the time tick height
  // so we subtract half the scale to get the correct time
  const _end = endRef.current * 1000 - (SCALE * 1000) / 2;
  // Calculate the time difference in milliseconds between start and end dates
  const timeDifference = _end - _start;

  // Calculate the time corresponding to the cursor position
  const dateAtCursor = new Date(_start + percentage * timeDifference);
  return dateAtCursor;
};

// Calculate the Y-position on the timeline of the requested timestamp
export const getYPosition = (
  startTimestamp: number,
  endTimestamp: number,
  requestedTimestamp: number,
  timelineHeight: number,
): number => {
  // Calculate the total time duration from start to end
  const totalTime = endTimestamp - startTimestamp;
  // Calculate the time elapsed from start to the requested timestamp
  const elapsedTime = requestedTimestamp - startTimestamp;
  // Calculate the proportion of time elapsed relative to the total time
  const timeProportion = elapsedTime / totalTime;
  // Calculate the Y-position of the requested timestamp
  const yPosition = timeProportion * timelineHeight;
  return yPosition;
};

// Round to neareset SCALE
export const round = (num: number) => Math.ceil(num / SCALE) * SCALE;

// Calculate the start time of the timeline, called on first render
export const calculateStart = (date: Dayjs | null) => {
  if (!date) {
    return round(dateToTimestamp(new Date()) + SCALE * EXTRA_TICKS);
  }
  // if date is today, start at current time
  if (date.isSame(dayjs(), "day")) {
    return round(dateToTimestamp(new Date()) + SCALE * EXTRA_TICKS);
  }
  // Otherwise start at midnight the next day
  return dateToTimestamp(
    new Date(date.add(1, "day").toDate().setHours(0, 0, 0, 0)),
  );
};

// Calculate the end time of the timeline, called on first render
export const calculateEnd = (date: Dayjs | null) =>
  dateToTimestamp(
    date
      ? new Date(date.toDate().setHours(0, 0, 0, 0))
      : new Date(new Date().setHours(0, 0, 0, 0)),
  );

// Calculate the number of items to render in the virtual list
export const calculateItemCount = (
  startRef: React.MutableRefObject<number>,
  endRef: React.MutableRefObject<number>,
) => (startRef.current - endRef.current) / SCALE + 1;

// Calculate the time from the index
export const calculateTimeFromIndex = (
  startRef: React.MutableRefObject<number>,
  index: number,
) => startRef.current - index * SCALE;

// Calculate the index from the time
export const calculateIndexFromTime = (
  startRef: React.MutableRefObject<number>,
  timestamp: number | null,
) => Math.round((startRef.current - (timestamp || dayjs().unix())) / SCALE);

// Common logic for items that affect the activity line
export const createActivityLineItem = (
  startRef: React.MutableRefObject<number>,
  indexStart: number,
  indexEnd: number,
  event: types.CameraEvent | types.HlsAvailableTimespan,
  eventType: "availableTimespan" | "timedEvent",
) => {
  const timelineItems: TimelineItems = {};

  let time = calculateTimeFromIndex(startRef, indexStart);
  timelineItems[time] = {
    ...DEFAULT_ITEM,
    time,
    [eventType]: event,
    activityLineVariant: indexStart === indexEnd ? "round" : "first",
  };

  if (indexStart !== indexEnd) {
    time = calculateTimeFromIndex(startRef, indexEnd);
    timelineItems[time] = {
      ...DEFAULT_ITEM,
      time,
      [eventType]: event,
      activityLineVariant: "last",
    };

    for (let i = indexStart + 1; i < indexEnd; i++) {
      time = calculateTimeFromIndex(startRef, i);
      timelineItems[time] = {
        ...DEFAULT_ITEM,
        time,
        [eventType]: event,
        activityLineVariant: "middle",
      };
    }
  }

  return timelineItems;
};

// For snapshot events, make sure adjacent events are grouped together
const addSnapshotEvent = (
  startRef: React.MutableRefObject<number>,
  timelineItems: TimelineItems,
  cameraEvent: types.CameraSnapshotEvent,
) => {
  // Find number of grouped ticks
  const groupedTicks = Math.ceil(EVENT_ICON_HEIGHT / TICK_HEIGHT);

  // Check if previous ticks have snapshot events and group them
  const index = calculateIndexFromTime(startRef, cameraEvent.timestamp);
  const groupedSnapshotEvents: types.CameraSnapshotEvents = [];
  for (let i = 0; i < groupedTicks; i++) {
    const time = calculateTimeFromIndex(startRef, index - i);
    if (time in timelineItems && timelineItems[time].snapshotEvents) {
      groupedSnapshotEvents.push(...(timelineItems[time].snapshotEvents || []));
      timelineItems[time].snapshotEvents = null;
    }
  }

  // Add the (grouped) snapshot events to the timeline
  const time = calculateTimeFromIndex(startRef, index);
  timelineItems[time] = {
    ...DEFAULT_ITEM,
    ...timelineItems[time],
    time,
    snapshotEvents: [
      ...groupedSnapshotEvents,
      ...(timelineItems[time].snapshotEvents || []),
      cameraEvent,
    ],
  };
};

// Get the timeline items from the events and available timespans
export const getTimelineItems = (
  startRef: React.MutableRefObject<number>,
  eventsData: types.CameraEvent[],
  availableTimespansData: types.HlsAvailableTimespan[],
) => {
  let timelineItems: TimelineItems = {};

  // Loop over available HLS files
  availableTimespansData.forEach((timespan) => {
    const indexEnd = calculateIndexFromTime(startRef, timespan.start);
    const indexStart = calculateIndexFromTime(startRef, timespan.end);

    timelineItems = {
      ...timelineItems,
      ...createActivityLineItem(
        startRef,
        indexStart,
        indexEnd,
        timespan,
        "availableTimespan",
      ),
    };
  });

  // Loop over events where type is motion or recording
  eventsData
    .filter(
      (cameraEvent): cameraEvent is types.CameraTimedEvents =>
        cameraEvent.type === "motion" || cameraEvent.type === "recording",
    )
    // Create a copy of the array and sort it by type
    .slice()
    .sort((cameraEvent, _) => (cameraEvent.type === "recording" ? 1 : -1))
    .forEach((cameraEvent) => {
      const indexEnd = calculateIndexFromTime(
        startRef,
        cameraEvent.start_timestamp,
      );
      const indexStart = calculateIndexFromTime(
        startRef,
        cameraEvent.end_timestamp,
      );

      timelineItems = {
        ...timelineItems,
        ...createActivityLineItem(
          startRef,
          indexStart,
          indexEnd,
          cameraEvent,
          "timedEvent",
        ),
      };
    });

  // Loop over events where type is object
  eventsData
    .filter(
      (cameraEvent): cameraEvent is types.CameraObjectEvent =>
        cameraEvent.type === "object",
    )
    .forEach((cameraEvent) => {
      addSnapshotEvent(startRef, timelineItems, cameraEvent);
    });

  eventsData
    .filter(
      (cameraEvent): cameraEvent is types.CameraFaceRecognitionEvent =>
        cameraEvent.type === "face_recognition",
    )
    .forEach((cameraEvent) => {
      addSnapshotEvent(startRef, timelineItems, cameraEvent);
    });
  return timelineItems;
};

// Get timeline items for the virtual list
export const getItem = (time: number, items: TimelineItems) =>
  time.toString() in items ? items[time] : { ...DEFAULT_ITEM, time };

// Convert confidence to percentage
export const convertToPercentage = (confidence: number) =>
  Math.round(confidence * 100);

// Get HLS fragment by timestamp
export const findFragmentByTimestamp = (
  fragments: Fragment[],
  timestamp: number,
): Fragment | null => {
  for (const fragment of fragments) {
    if (fragment.programDateTime) {
      const fragmentStart = fragment.programDateTime;
      const fragmentEnd = fragment.programDateTime + fragment.duration * 1000;
      if (
        (timestamp >= fragmentStart && timestamp <= fragmentEnd) ||
        timestamp < fragmentStart
      ) {
        return fragment;
      }
    }
  }

  return null; // Return null if no matching fragment is found
};

// Calculate the height of the camera while maintaining aspect ratio
export const calculateHeight = (
  cameraWidth: number,
  cameraHeight: number,
  width: number,
): number => (width * cameraHeight) / cameraWidth;

export const getSrc = (event: types.CameraEvent) => {
  switch (event.type) {
    case "recording":
      return event.thumbnail_path;
    case "object":
    case "face_recognition":
      return event.snapshot_path;
    default:
      return BLANK_IMAGE;
  }
};

// Extract unique snapshot event types into a map
export const extractUniqueTypes = (
  snapshotEvents: types.CameraSnapshotEvents,
) => {
  if (!snapshotEvents) {
    return {};
  }

  const typeMap = new Map<string, types.CameraSnapshotEvents>();

  snapshotEvents.forEach((event) => {
    const type = event.type;
    if (!typeMap.has(type)) {
      typeMap.set(type, []);
    }
    typeMap.get(type)!.push(event);
  });

  const result: { [key: string]: types.CameraSnapshotEvents } = {};
  typeMap.forEach((value, key) => {
    result[key] = value;
  });

  return result;
};

// Extract unique labels for object snapshot events into a map
export const extractUniqueLabels = (objectEvents: types.CameraObjectEvents) => {
  if (!objectEvents) {
    return {};
  }

  const labelMap = new Map<string, types.CameraObjectEvents>();

  objectEvents.forEach((event) => {
    let label;
    switch (event.label) {
      case "car":
      case "truck":
      case "vehicle":
        label = "vehicle";
        break;
      default:
        label = event.label;
    }

    if (!labelMap.has(label)) {
      labelMap.set(label, []);
    }
    labelMap.get(label)!.push(event);
  });

  const result: { [key: string]: types.CameraObjectEvents } = {};
  labelMap.forEach((value, key) => {
    result[key] = value;
  });

  return result;
};

export const filterEvents = (events: types.CameraEvent[]) =>
  events.filter(
    (cameraEvent): cameraEvent is types.CameraSnapshotEvent =>
      cameraEvent.type === "object" || cameraEvent.type === "face_recognition",
  );
