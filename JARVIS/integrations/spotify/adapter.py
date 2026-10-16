"""
JARVIS AI - Spotify Universal Adapter
Controls Spotify via deep links, Windows protocol invocation, and OS media commands.
"""

import os
import urllib.parse
from typing import Dict, Any, Optional
from services.local_agent.process_manager import ProcessManager


class SpotifyAdapter:
    def __init__(self, process_manager: Optional[ProcessManager] = None):
        self.pm = process_manager or ProcessManager()

    def play_search(self, query: str) -> Dict[str, Any]:
        """
        Opens Spotify and plays/searches for a track, artist, or playlist.
        Uses the spotify:search: URI scheme.
        """
        encoded_query = urllib.parse.quote(query)
        uri = f"spotify:search:{encoded_query}"
        
        res = self.pm.launch_application("spotify", [uri])
        return {
            "success": res.get("success", False),
            "action": "play_search",
            "query": query,
            "uri": uri,
            "verified": res.get("verified", False),
            "message": f"Dispatched search to Spotify for '{query}'."
        }

    def open_playlist(self, playlist_name_or_id: str) -> Dict[str, Any]:
        """
        Opens a specific playlist or queries Spotify for a named playlist (e.g., 'study playlist').
        """
        if playlist_name_or_id.startswith("spotify:"):
            uri = playlist_name_or_id
        else:
            uri = f"spotify:search:{urllib.parse.quote(playlist_name_or_id)}"

        res = self.pm.launch_application("spotify", [uri])
        return {
            "success": res.get("success", False),
            "action": "open_playlist",
            "playlist": playlist_name_or_id,
            "uri": uri,
            "verified": res.get("verified", False),
            "message": f"Spotify opening playlist: '{playlist_name_or_id}'."
        }

    def launch(self) -> Dict[str, Any]:
        """Launches the Spotify desktop application."""
        return self.pm.launch_application("spotify")
