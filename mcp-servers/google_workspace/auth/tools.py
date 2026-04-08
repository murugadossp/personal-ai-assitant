from mcp.server.fastmcp import FastMCP

from config import get_base_url
from auth.store import token_store

def register(mcp: FastMCP):
    @mcp.tool()
    def auth_check_status(user_id: str) -> dict:
        """
        Check if a user has authorized Google Workspace access.

        Args:
            user_id: The unique user identifier
        """
        is_authorized = token_store.exists(user_id)
        result = {
            "user_id": user_id,
            "authorized": is_authorized,
        }
        if not is_authorized:
            result["auth_url"] = f"{get_base_url()}/auth?user_id={user_id}"
            result["message"] = (
                "User has not authorized. Please open the auth_url in a browser "
                "to grant Google Workspace access."
            )
        return result

    @mcp.tool()
    def auth_revoke(user_id: str) -> dict:
        """
        Revoke a user's Google Workspace authorization.

        Args:
            user_id: The unique user identifier
        """
        token_store.delete(user_id)
        return {"user_id": user_id, "status": "revoked"}
