import pandas as pd
from langchain.tools import tool
from typing import Dict, List, Optional, Union

# Data is hard-coded so that the agent can call them without passing the dataframe as an argument.
# We cannot use a class because LangChain does not support tools inside classes.
CALENDAR_EVENTS = pd.read_csv("data/processed/calendar_events.csv", dtype=str)


def reset_state():
    """
    Resets the calendar events to the original state.
    """
    global CALENDAR_EVENTS
    CALENDAR_EVENTS = pd.read_csv("data/processed/calendar_events.csv", dtype=str)


@tool("calendar.get_event_information_by_id", return_direct=False, parse_docstring=True)
def get_event_information_by_id(
    event_id: Optional[str] = None,
    field: Optional[str] = None
) -> Union[str, Dict[str, str]]:
    """
    Returns the event for a given ID.

    Args:
        event_id: 8-digit ID of the event.
        field: Field to return. Available fields are: "event_id", "event_name", "participant_email", "event_start", "duration"

    Returns
    -------
    event : dict
        Event information for the given ID and field.


    Examples
    --------
    >>> calendar.get_event_information_by_id("00000000", "event_name")
    {{"event_name": "Meeting with Sam"}}

    >>> calendar.get_event_information_by_id("00000000", "event_start")
    {{"event_start": "2021-06-01 13:00:00"}}

    >>> calendar.get_event_information_by_id("00000000", "duration")
    {{"duration": "60"}}

    """
    if not event_id:
        return "Event ID not provided."
    if not field:
        return "Field not provided."
    event = CALENDAR_EVENTS[CALENDAR_EVENTS["event_id"] == event_id].to_dict(orient="records")
    if event:
        if field in event[0]:
            return {field: event[0][field]}
        else:
            return "Field not found."
    else:
        return "Event not found."


@tool("calendar.search_events", return_direct=False, parse_docstring=True)
def search_events(
    query: str = "",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None
) -> Union[str, List[Dict[str, str]]]:
    """
    Returns the events for a given query.

    Args:
        query: Query to search for. Terms will be matched in the event_name and participant_email fields.
        time_min: Lower bound (inclusive) for an event's end time to filter by. Format: "YYYY-MM-DD HH:MM:SS"
        time_max: Upper bound (inclusive) for an event's start time to filter by. Format: "YYYY-MM-DD HH:MM:SS

    Returns
    -------
    events : list
        List of events matching the query. Returns at most 5 events.

    Examples
    --------
    >>> calendar.search_events("Sam")
    [{{"event_id": "00000000", "event_name": "Meeting with Sam", "participant_email: "sam@example.com", "event_start": "2021-06-01 13:00:00", "duration": "60"}},
    {{"event_id": "00000001", "event_name": "Lunch with Sam", "participant_email": "sam@example.com", "event_start": "2021-06-01 13:00:00", "duration": "30}}"
    ]
    """
    events = CALENDAR_EVENTS[
        (CALENDAR_EVENTS["event_name"].str.contains(query, case=False))
        | (CALENDAR_EVENTS["participant_email"].str.contains(query, case=False))
    ].to_dict(orient="records")
    if time_min:
        events = [event for event in events if pd.Timestamp(event["event_start"]) >= pd.Timestamp(time_min)]
    if time_max:
        events = [event for event in events if pd.Timestamp(event["event_start"]) <= pd.Timestamp(time_max)]
    if events:
        return events[:5]
    else:
        return "No events found."


@tool("calendar.create_event", return_direct=False, parse_docstring=True)
def create_event(
    event_name: Optional[str] = None,
    participant_email: Optional[str] = None,
    event_start: Optional[str] = None,
    duration: Optional[str] = None
) -> str:
    """
    Creates a new event.

    Args:
        event_name: Name of the event.
        participant_email: Email of the participant.
        event_start: Start time of the event. Format: "YYYY-MM-DD HH:MM:SS"
        duration: Duration of the event in minutes.

    Returns
    -------
        event_id: ID of the newly created event.

    Examples
    --------
    >>> calendar.create_event("Meeting with Sam", "sam@example.com", "2021-06-01 13:00:00", "60")
    "00000000"
    """
    # Working with classes is difficult in LangChain, so we use a global variable instead.
    global CALENDAR_EVENTS

    if not event_name:
        return "Event name not provided."
    if not participant_email:
        return "Participant email not provided."
    if not event_start:
        return "Event start not provided."
    if not duration:
        return "Event duration not provided."

    participant_email = participant_email.lower()

    event_id = str(int(CALENDAR_EVENTS["event_id"].max()) + 1).zfill(8)
    new_event = pd.DataFrame(
        {
            "event_id": [event_id],
            "event_name": [event_name],
            "participant_email": [participant_email],
            "event_start": [event_start],
            "duration": [duration],
        }
    )
    CALENDAR_EVENTS = pd.concat([CALENDAR_EVENTS, new_event])
    return event_id


@tool("calendar.delete_event", return_direct=False, parse_docstring=True)
def delete_event(event_id: Optional[str] = None) -> str:
    """
    Deletes an event.

    Args:
        event_id: 8-digit ID of the event.

    Returns
    -------
        message: Message indicating whether the deletion was successful.

    Examples
    --------
    >>> calendar.delete_event("00000000")
    "Event deleted successfully."

    """
    global CALENDAR_EVENTS

    if not event_id:
        return "Event ID not provided."

    if event_id in CALENDAR_EVENTS["event_id"].values:
        CALENDAR_EVENTS = CALENDAR_EVENTS[CALENDAR_EVENTS["event_id"] != event_id]
        return "Event deleted successfully."
    else:
        return "Event not found."


@tool("calendar.update_event", return_direct=False, parse_docstring=True)
def update_event(
    event_id: Optional[str] = None,
    field: Optional[str] = None,
    new_value: Optional[str] = None
) -> str:
    """
    Updates an event.

    Args:
        event_id: 8-digit ID of the event.
        field: Field to update.
        new_value: New value for the field.

    Returns
    -------
        message: Message indicating whether the update was successful.

    Examples
    --------
    >>> calendar.update_event("00000000", "event_name", "New Event Name")
    "Event updated successfully."

    """
    global CALENDAR_EVENTS

    if not event_id or not field or not new_value:
        return "Event ID, field, or new value not provided."
    if event_id in CALENDAR_EVENTS["event_id"].values:
        if field == "participant_email":
            new_value = new_value.lower()
        CALENDAR_EVENTS.loc[CALENDAR_EVENTS["event_id"] == event_id, field] = new_value
        return "Event updated successfully."
    else:
        return "Event not found."
