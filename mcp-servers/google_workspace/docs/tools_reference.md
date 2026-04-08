# 🛠️ MCP Tools Reference: Google Workspace

This document provides a detailed catalog of the 16 specialized tools exposed by the **Google Workspace MCP Server**. These tools enable AI agents to perform complex operations across **Gmail**, **Calendar**, and **Drive**.

---

## 📅 Google Calendar

### `calendar_list_calendars`
- **Description**: Retrieves a list of all calendars the user can access.
- **Parameters**: 
    - `user_id` (string): Unique user identifier.
- **Returns**: A list of calendars (ID, summary, primary).

### `calendar_list_events`
- **Description**: Fetches upcoming events from a specific calendar.
- **Parameters**:
    - `user_id` (string): Unique user identifier.
    - `calendar_id` (string, optional): Default is "primary".
    - `max_results` (int, optional): Default is 10.
    - `time_min` (string, optional): Start time in ISO 8601.
    - `time_max` (string, optional): End time in ISO 8601.

---

## 📧 Gmail

### `gmail_search_emails`
- **Description**: Executes a Gmail search query (using standard Gmail syntax).
- **Parameters**:
    - `user_id` (string): Unique user identifier.
    - `query` (string, optional): Example: `from:boss@company.com is:unread`.
    - `max_results` (int, optional): Default is 10.
    - `label` (string, optional): Default is `INBOX`.

### `gmail_send_email`
- **Description**: Composes and sends a new message.
- **Parameters**:
    - `user_id` (string): Unique user identifier.
    - `to` (string): Recipient email.
    - `subject` (string): Email subject.
    - `body` (string): Plain text body.
    - `cc`, `bcc` (string, optional): Comma-separated lists.

---

## 📁 Google Drive

### `drive_list_files`
- **Description**: Lists files in the user's Drive, optionally within a folder.
- **Parameters**:
    - `user_id` (string): Unique user identifier.
    - `query` (string, optional): Drive API search query.
    - `max_results` (int, optional): Default is 10.
    - `folder_id` (string, optional): Restrict search to this folder.

### `drive_read_file`
- **Description**: Reads file metadata and content. **Automatically exports Google Docs to plain text**.
- **Parameters**:
    - `user_id` (string): Unique user identifier.
    - `file_id` (string): Google Drive file ID.

---

## 🔐 Authentication Tools

### `auth_check_status`
- **Description**: Verifies if the user is authorized to use the MCP tools.
- **Parameters**:
    - `user_id` (string): Unique user identifier.
- **Return JSON**:
    ```json
    {
       "user_id": "alice",
       "authorized": false,
       "auth_url": "https://server.app/auth?user_id=alice"
    }
    ```

---

> [!TIP]
> **Gmail Query Syntax**: Use `is:unread`, `from:someone@test.com`, or `after:2026/01/01` in the `query` field of `gmail_search_emails` to get precise results.

> [!CAUTION]
> **File Sizes**: `drive_read_file` pulls up to **5,000 characters** of text from Google Docs. For larger docs, consider using `webViewLink` for manual viewing.
