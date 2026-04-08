import base64
from email.mime.text import MIMEText
from mcp.server.fastmcp import FastMCP
from auth.helpers import gmail_service

def register(mcp: FastMCP):

    def _parse_message(msg: dict) -> dict:
        headers = {
            h["name"].lower(): h["value"]
            for h in msg.get("payload", {}).get("headers", [])
        }
        body = ""
        payload = msg.get("payload", {})
        if payload.get("body", {}).get("data"):
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                "utf-8", errors="replace"
            )
        elif payload.get("parts"):
            for part in payload["parts"]:
                if (
                    part.get("mimeType") == "text/plain"
                    and part.get("body", {}).get("data")
                ):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8", errors="replace"
                    )
                    break

        return {
            "id": msg["id"],
            "threadId": msg.get("threadId"),
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "subject": headers.get("subject", "(No subject)"),
            "date": headers.get("date", ""),
            "snippet": msg.get("snippet", ""),
            "body": body[:2000],
            "labelIds": msg.get("labelIds", []),
        }

    @mcp.tool()
    def gmail_search_emails(
        user_id: str,
        query: str = "",
        max_results: int = 10,
        label: str = "INBOX",
    ) -> list[dict]:
        """
        Search emails in Gmail.

        Args:
            user_id: The unique user identifier
            query: Gmail search query (e.g. "from:boss@company.com is:unread")
            max_results: Max emails to return (default: 10)
            label: Label to search in (default: "INBOX")
        """
        svc = gmail_service(user_id)
        params = {"userId": "me", "maxResults": max_results}
        if query:
            params["q"] = query
        if label:
            params["labelIds"] = [label]

        results = svc.users().messages().list(**params).execute()
        messages = results.get("messages", [])

        emails = []
        for m in messages:
            msg = svc.users().messages().get(
                userId="me", id=m["id"], format="full"
            ).execute()
            emails.append(_parse_message(msg))
        return emails

    @mcp.tool()
    def gmail_read_email(user_id: str, message_id: str) -> dict:
        """
        Read a specific email by its message ID.

        Args:
            user_id: The unique user identifier
            message_id: Gmail message ID
        """
        msg = gmail_service(user_id).users().messages().get(
            userId="me", id=message_id, format="full"
        ).execute()
        return _parse_message(msg)

    @mcp.tool()
    def gmail_send_email(
        user_id: str,
        to: str,
        subject: str,
        body: str,
        cc: str = "",
        bcc: str = "",
    ) -> dict:
        """
        Send an email via Gmail.

        Args:
            user_id: The unique user identifier
            to: Recipient email
            subject: Email subject
            body: Email body (plain text)
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
        """
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        if cc:
            message["cc"] = cc
        if bcc:
            message["bcc"] = bcc

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = gmail_service(user_id).users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        return {"id": sent["id"], "threadId": sent.get("threadId"), "status": "sent"}

    @mcp.tool()
    def gmail_reply_to_email(user_id: str, message_id: str, body: str) -> dict:
        """
        Reply to an email thread.

        Args:
            user_id: The unique user identifier
            message_id: Message ID to reply to
            body: Reply body (plain text)
        """
        svc = gmail_service(user_id)
        original = svc.users().messages().get(
            userId="me", id=message_id, format="full"
        ).execute()
        headers = {
            h["name"].lower(): h["value"]
            for h in original.get("payload", {}).get("headers", [])
        }

        reply_to = headers.get("reply-to", headers.get("from", ""))
        subject = headers.get("subject", "")
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        message = MIMEText(body)
        message["to"] = reply_to
        message["subject"] = subject
        message["In-Reply-To"] = headers.get("message-id", "")
        message["References"] = headers.get("message-id", "")

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = svc.users().messages().send(
            userId="me",
            body={"raw": raw, "threadId": original.get("threadId")},
        ).execute()
        return {"id": sent["id"], "threadId": sent.get("threadId"), "status": "replied"}

    @mcp.tool()
    def gmail_list_labels(user_id: str) -> list[dict]:
        """
        List all Gmail labels.

        Args:
            user_id: The unique user identifier
        """
        result = gmail_service(user_id).users().labels().list(userId="me").execute()
        return [
            {"id": lbl["id"], "name": lbl["name"], "type": lbl.get("type", "")}
            for lbl in result.get("labels", [])
        ]
