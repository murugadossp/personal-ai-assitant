import datetime
from mcp.server.fastmcp import FastMCP
from auth.helpers import calendar_service

def register(mcp: FastMCP):

    @mcp.tool()
    def calendar_list_calendars(user_id: str) -> list[dict]:
        """
        List all calendars accessible to the user.

        Args:
            user_id: The unique user identifier
        """
        result = calendar_service(user_id).calendarList().list().execute()
        return [
            {
                "id": cal["id"],
                "summary": cal.get("summary", ""),
                "primary": cal.get("primary", False),
            }
            for cal in result.get("items", [])
        ]

    @mcp.tool()
    def calendar_list_events(
        user_id: str,
        calendar_id: str = "primary",
        max_results: int = 10,
        time_min: str | None = None,
        time_max: str | None = None,
    ) -> list[dict]:
        """
        List upcoming events from a calendar.

        Args:
            user_id: The unique user identifier
            calendar_id: Calendar ID (default: "primary")
            max_results: Max events to return (default: 10)
            time_min: Start time ISO 8601 (default: now)
            time_max: End time ISO 8601 (optional)
        """
        if not time_min:
            time_min = datetime.datetime.now(datetime.timezone.utc).isoformat()

        params = {
            "calendarId": calendar_id,
            "timeMin": time_min,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if time_max:
            params["timeMax"] = time_max

        events = calendar_service(user_id).events().list(**params).execute().get("items", [])
        return [
            {
                "id": ev["id"],
                "summary": ev.get("summary", "(No title)"),
                "start": ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date")),
                "end": ev.get("end", {}).get("dateTime", ev.get("end", {}).get("date")),
                "location": ev.get("location", ""),
                "description": ev.get("description", ""),
                "attendees": [a.get("email") for a in ev.get("attendees", [])],
            }
            for ev in events
        ]

    @mcp.tool()
    def calendar_create_event(
        user_id: str,
        summary: str,
        start_time: str,
        end_time: str,
        calendar_id: str = "primary",
        description: str = "",
        location: str = "",
        attendees: list[str] | None = None,
        timezone: str = "Asia/Kolkata",
    ) -> dict:
        """
        Create a new calendar event.

        Args:
            user_id: The unique user identifier
            summary: Event title
            start_time: Start in ISO 8601 (e.g. "2026-04-10T10:00:00")
            end_time: End in ISO 8601
            calendar_id: Calendar ID (default: "primary")
            description: Event description
            location: Event location
            attendees: List of attendee emails
            timezone: Timezone (default: "Asia/Kolkata")
        """
        event_body = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": timezone},
            "end": {"dateTime": end_time, "timeZone": timezone},
        }
        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        if attendees:
            event_body["attendees"] = [{"email": e} for e in attendees]

        created = calendar_service(user_id).events().insert(
            calendarId=calendar_id, body=event_body
        ).execute()
        return {
            "id": created["id"],
            "summary": created.get("summary"),
            "htmlLink": created.get("htmlLink"),
            "start": created["start"],
            "end": created["end"],
        }

    @mcp.tool()
    def calendar_update_event(
        user_id: str,
        event_id: str,
        calendar_id: str = "primary",
        summary: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        description: str | None = None,
        location: str | None = None,
        timezone: str = "Asia/Kolkata",
    ) -> dict:
        """
        Update an existing calendar event.

        Args:
            user_id: The unique user identifier
            event_id: Event ID to update
            calendar_id: Calendar ID (default: "primary")
            summary: New title (optional)
            start_time: New start ISO 8601 (optional)
            end_time: New end ISO 8601 (optional)
            description: New description (optional)
            location: New location (optional)
            timezone: Timezone (default: "Asia/Kolkata")
        """
        svc = calendar_service(user_id)
        event = svc.events().get(calendarId=calendar_id, eventId=event_id).execute()

        if summary is not None:
            event["summary"] = summary
        if description is not None:
            event["description"] = description
        if location is not None:
            event["location"] = location
        if start_time is not None:
            event["start"] = {"dateTime": start_time, "timeZone": timezone}
        if end_time is not None:
            event["end"] = {"dateTime": end_time, "timeZone": timezone}

        updated = svc.events().update(
            calendarId=calendar_id, eventId=event_id, body=event
        ).execute()
        return {
            "id": updated["id"],
            "summary": updated.get("summary"),
            "htmlLink": updated.get("htmlLink"),
            "start": updated["start"],
            "end": updated["end"],
        }

    @mcp.tool()
    def calendar_delete_event(
        user_id: str, event_id: str, calendar_id: str = "primary"
    ) -> dict:
        """
        Delete a calendar event.

        Args:
            user_id: The unique user identifier
            event_id: Event ID to delete
            calendar_id: Calendar ID (default: "primary")
        """
        calendar_service(user_id).events().delete(
            calendarId=calendar_id, eventId=event_id
        ).execute()
        return {"status": "deleted", "event_id": event_id}

    @mcp.tool()
    def calendar_check_availability(
        user_id: str,
        time_min: str,
        time_max: str,
        calendar_ids: list[str] | None = None,
    ) -> list[dict]:
        """
        Check free/busy availability.

        Args:
            user_id: The unique user identifier
            time_min: Start ISO 8601
            time_max: End ISO 8601
            calendar_ids: Calendar IDs to check (default: ["primary"])
        """
        if not calendar_ids:
            calendar_ids = ["primary"]

        body = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": cid} for cid in calendar_ids],
        }
        result = calendar_service(user_id).freebusy().query(body=body).execute()
        return [
            {
                "calendar_id": cal_id,
                "busy_slots": info.get("busy", []),
                "is_free": len(info.get("busy", [])) == 0,
            }
            for cal_id, info in result.get("calendars", {}).items()
        ]
