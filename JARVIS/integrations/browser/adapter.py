"""
JARVIS AI - Browser & Web Navigation Adapter
Executes smart web navigation, e-commerce search, YouTube video queries, online compilers, and search engine lookups.
"""

import os
import sys
import re
import urllib.parse
import webbrowser
from typing import Dict, Any, Optional
from services.local_agent.process_manager import ProcessManager


class BrowserAdapter:
    def __init__(self, process_manager: Optional[ProcessManager] = None):
        self.pm = process_manager or ProcessManager()

    def open_url(self, url: str) -> Dict[str, Any]:
        """
        Opens any authorized URL in the default browser using native Windows ShellExecute
        with graceful fallback to Python's standard webbrowser.
        """
        try:
            if not (url.startswith("http://") or url.startswith("https://")):
                url = "https://" + url

            opened = False
            # On Windows, os.startfile invokes ShellExecute directly in the active user desktop session
            if hasattr(os, "startfile"):
                try:
                    os.startfile(url)
                    opened = True
                except Exception:
                    opened = webbrowser.open(url)
            else:
                opened = webbrowser.open(url)

            return {
                "success": True,
                "url": url,
                "verified": bool(opened),
                "message": f"Successfully launched browser to: {url}"
            }
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": f"Failed to open URL '{url}': {str(e)}",
                "verified": False
            }

    def search_youtube(self, search_term: str) -> Dict[str, Any]:
        """Navigates to YouTube with the query."""
        clean_query = self._clean_query(search_term, ["youtube", "search for", "search", "and play", "play"])
        encoded = urllib.parse.quote_plus(clean_query or "Python tutorials")
        url = f"https://www.youtube.com/results?search_query={encoded}"
        res = self.open_url(url)
        res["query"] = clean_query
        res["site"] = "YouTube"
        res["message"] = f"Opened YouTube search for '{clean_query}'."
        return res

    def search_amazon(self, query: str) -> Dict[str, Any]:
        """Navigates to Amazon with product search query."""
        clean_query = self._clean_query(query, ["amazon", "go to", "find", "search for", "look for", "and", "buy"])
        encoded = urllib.parse.quote_plus(clean_query or "deals")
        url = f"https://www.amazon.com/s?k={encoded}"
        res = self.open_url(url)
        res["query"] = clean_query
        res["site"] = "Amazon"
        res["message"] = f"Opened Amazon search for '{clean_query}'."
        return res

    def open_online_compiler(self, language: str = "python") -> Dict[str, Any]:
        """Navigates to an interactive online compiler."""
        lang = language.lower()
        if "c++" in lang or "cpp" in lang:
            url = "https://www.onlinegdb.com/online_c++_compiler"
        elif "java" in lang:
            url = "https://www.programiz.com/java-programming/online-compiler/"
        else:
            url = "https://www.programiz.com/python-programming/online-compiler/"

        res = self.open_url(url)
        res["site"] = f"Online {language.capitalize()} Compiler"
        res["message"] = f"Opened online {language.capitalize()} compiler at: {url}"
        return res

    def search_web(self, query: str) -> Dict[str, Any]:
        """Performs a web search via Google."""
        clean_query = self._clean_query(query, ["google", "search for", "search", "look up", "find", "go to"])
        encoded = urllib.parse.quote_plus(clean_query or query)
        url = f"https://www.google.com/search?q={encoded}"
        res = self.open_url(url)
        res["query"] = clean_query or query
        res["site"] = "Google Search"
        res["message"] = f"Searched web for '{clean_query or query}'."
        return res

    def smart_navigate(self, command: str) -> Dict[str, Any]:
        """
        Intelligently decomposes natural language web instructions into target site & query.
        e.g.:
          - 'go to amazon and find belts for men' -> Amazon search: belts for men
          - 'go to python online compiler and write hello world code' -> Programiz Python compiler
          - 'open youtube and search for python tutorials' -> YouTube search: python tutorials
          - 'go to github and search for langchain' -> GitHub search
        """
        cmd = command.lower().strip()

        # E-Commerce: Amazon
        if "amazon" in cmd:
            return self.search_amazon(command)

        # Online code compilers
        if "online compiler" in cmd or ("compiler" in cmd and ("python" in cmd or "code" in cmd)):
            lang = "python"
            if "java" in cmd:
                lang = "java"
            elif "c++" in cmd or "cpp" in cmd:
                lang = "c++"
            return self.open_online_compiler(lang)

        # Video: YouTube
        if "youtube" in cmd:
            return self.search_youtube(command)

        # Developer: GitHub
        if "github" in cmd:
            clean = self._clean_query(command, ["github", "go to", "search for", "find", "and", "repo", "repository"])
            encoded = urllib.parse.quote_plus(clean)
            url = f"https://github.com/search?q={encoded}" if clean else "https://github.com"
            res = self.open_url(url)
            res["site"] = "GitHub"
            res["message"] = f"Opened GitHub for '{clean}'." if clean else "Opened GitHub."
            return res

        # Wikipedia
        if "wikipedia" in cmd or "wiki" in cmd:
            clean = self._clean_query(command, ["wikipedia", "wiki", "search for", "look up", "about", "find"])
            encoded = urllib.parse.quote_plus(clean)
            url = f"https://en.wikipedia.org/wiki/Special:Search?search={encoded}"
            res = self.open_url(url)
            res["site"] = "Wikipedia"
            res["message"] = f"Opened Wikipedia for '{clean}'."
            return res

        # Explicit URL patterns (e.g. "go to reddit.com" or "open https://news.ycombinator.com")
        url_match = re.search(r'(https?://[^\s]+|[a-zA-Z0-9-]+\.(?:com|org|net|io|edu|gov|in|ai|dev|co)[^\s]*)', command)
        if url_match:
            raw_url = url_match.group(1).rstrip(",.!?")
            return self.open_url(raw_url)

        # Generic web search
        return self.search_web(command)

    def _clean_query(self, raw: str, stopwords: list) -> str:
        text = raw
        for word in stopwords:
            pattern = re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
            text = pattern.sub('', text)
        return " ".join(text.split()).strip()
