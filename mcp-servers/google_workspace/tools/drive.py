from mcp.server.fastmcp import FastMCP
from auth.helpers import drive_service

def register(mcp: FastMCP):

    @mcp.tool()
    def drive_list_files(
        user_id: str,
        query: str = "",
        max_results: int = 10,
        folder_id: str | None = None,
    ) -> list[dict]:
        """
        List files in Google Drive.

        Args:
            user_id: The unique user identifier
            query: Search query (e.g. "name contains 'report'")
            max_results: Max files to return (default: 10)
            folder_id: Restrict to a specific folder (optional)
        """
        q_parts = []
        if query:
            q_parts.append(query)
        if folder_id:
            q_parts.append(f"'{folder_id}' in parents")

        params = {
            "pageSize": max_results,
            "fields": "files(id,name,mimeType,modifiedTime,size,webViewLink,owners)",
        }
        if q_parts:
            params["q"] = " and ".join(q_parts)

        result = drive_service(user_id).files().list(**params).execute()
        return [
            {
                "id": f["id"],
                "name": f["name"],
                "mimeType": f.get("mimeType", ""),
                "modifiedTime": f.get("modifiedTime", ""),
                "size": f.get("size", ""),
                "webViewLink": f.get("webViewLink", ""),
            }
            for f in result.get("files", [])
        ]

    @mcp.tool()
    def drive_search_files(
        user_id: str, search_term: str, max_results: int = 10
    ) -> list[dict]:
        """
        Search for files by name in Google Drive.

        Args:
            user_id: The unique user identifier
            search_term: Text to search for in file names
            max_results: Max files to return (default: 10)
        """
        return drive_list_files(
            user_id=user_id,
            query=f"name contains '{search_term}'",
            max_results=max_results,
        )

    @mcp.tool()
    def drive_read_file(user_id: str, file_id: str) -> dict:
        """
        Read metadata and content of a Google Drive file.
        Google Docs/Sheets/Slides are exported as plain text.

        Args:
            user_id: The unique user identifier
            file_id: Google Drive file ID
        """
        svc = drive_service(user_id)
        metadata = svc.files().get(
            fileId=file_id,
            fields="id,name,mimeType,modifiedTime,size,webViewLink",
        ).execute()

        result = {
            "id": metadata["id"],
            "name": metadata["name"],
            "mimeType": metadata.get("mimeType", ""),
            "modifiedTime": metadata.get("modifiedTime", ""),
            "webViewLink": metadata.get("webViewLink", ""),
        }

        mime = metadata.get("mimeType", "")
        export_map = {
            "application/vnd.google-apps.document": "text/plain",
            "application/vnd.google-apps.spreadsheet": "text/csv",
            "application/vnd.google-apps.presentation": "text/plain",
        }

        if mime in export_map:
            content = svc.files().export(
                fileId=file_id, mimeType=export_map[mime]
            ).execute()
            result["content"] = content.decode("utf-8", errors="replace")[:5000]
        else:
            result["content"] = "(Binary file — use webViewLink to view)"

        return result
