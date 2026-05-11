"""ChromaDB client utility."""

import chromadb
from typing import Optional
from backend.config import get_settings


class ChromaClient:
    """ChromaDB client wrapper — uses local persistent storage by default,
    falls back from HTTP if server version is incompatible."""

    def __init__(self):
        self._client: Optional[chromadb.ClientAPI] = None

    def connect(self):
        """Initialize ChromaDB connection."""
        settings = get_settings()

        # Try HTTP client first
        try:
            self._client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port
            )
            # Test connection
            self._client.heartbeat()
            print("ChromaDB HTTP client connected")
            return
        except Exception as e:
            print(f"ChromaDB HTTP failed ({e}), using local persistent client")

        # Fallback to local persistent client (no server needed)
        import os
        chroma_dir = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data")
        os.makedirs(chroma_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(path=chroma_dir)
        print(f"ChromaDB persistent client initialized at {chroma_dir}")

    @property
    def client(self) -> chromadb.ClientAPI:
        if self._client is None:
            raise RuntimeError("ChromaDB client not connected. Call connect() first.")
        return self._client

    def get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        return self.client.get_or_create_collection(name=name)

    def get_collection(self, name: str):
        """Get an existing collection."""
        return self.client.get_collection(name=name)


# Singleton
chroma_client = ChromaClient()
