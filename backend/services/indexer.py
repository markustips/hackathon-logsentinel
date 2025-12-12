"""Log indexing service with embeddings and FAISS."""
import os
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import numpy as np

logger = logging.getLogger(__name__)


class LogIndexer:
    """Index logs with semantic embeddings using FAISS."""

    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2", index_path: str = "./data/faiss_index"):
        """
        Initialize the indexer.

        Args:
            embedding_model_name: Name of the sentence-transformers model
            index_path: Path to store FAISS indices
        """
        self.embedding_model_name = embedding_model_name
        self.index_path = index_path
        self.model = None
        self.dimension = 384  # Default for all-MiniLM-L6-v2

        # Lazy load model
        os.makedirs(index_path, exist_ok=True)

    def _load_model(self):
        """Lazy load the embedding model."""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.embedding_model_name}")
                self.model = SentenceTransformer(self.embedding_model_name)
                self.dimension = self.model.get_sentence_embedding_dimension()
                logger.info(f"Model loaded successfully. Embedding dimension: {self.dimension}")
            except Exception as e:
                logger.error(f"Error loading embedding model: {e}")
                raise

    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            Numpy array of embeddings
        """
        self._load_model()

        if not texts:
            return np.array([])

        try:
            embeddings = self.model.encode(texts, show_progress_bar=len(texts) > 100)
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            raise

    def create_chunks(
        self,
        records: List[Dict[str, Any]],
        window_minutes: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group records into time-based chunks.

        Args:
            records: List of log records
            window_minutes: Chunk window size in minutes

        Returns:
            Dictionary mapping chunk_id to list of records
        """
        chunks = {}

        for record in records:
            timestamp = record.get('timestamp')

            if timestamp:
                # Round timestamp to nearest window
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)

                window_start = timestamp.replace(
                    minute=(timestamp.minute // window_minutes) * window_minutes,
                    second=0,
                    microsecond=0
                )
                chunk_id = window_start.isoformat()
            else:
                # No timestamp - use default chunk
                chunk_id = "no_timestamp"

            if chunk_id not in chunks:
                chunks[chunk_id] = []

            chunks[chunk_id].append(record)

        logger.info(f"Created {len(chunks)} chunks from {len(records)} records")
        return chunks

    def build_index(self, file_id: str, records: List[Dict[str, Any]]) -> str:
        """
        Build FAISS index for log records.

        Args:
            file_id: Unique file identifier
            records: List of log records with embeddings

        Returns:
            Path to the saved index
        """
        try:
            import faiss
        except ImportError:
            logger.error("FAISS not installed. Install with: pip install faiss-cpu")
            raise

        # Extract embeddings
        embeddings_list = []
        for record in records:
            embedding_str = record.get('embedding_vector')
            if embedding_str:
                embedding = json.loads(embedding_str)
                embeddings_list.append(embedding)

        if not embeddings_list:
            logger.warning("No embeddings found in records")
            return ""

        embeddings = np.array(embeddings_list, dtype=np.float32)

        # Create FAISS index
        logger.info(f"Building FAISS index with {len(embeddings)} vectors")
        index = faiss.IndexFlatL2(self.dimension)
        index.add(embeddings)

        # Save index
        index_file = os.path.join(self.index_path, f"{file_id}.index")
        faiss.write_index(index, index_file)
        logger.info(f"FAISS index saved to {index_file}")

        # Save record IDs mapping
        mapping = [record['id'] for record in records if record.get('embedding_vector')]
        mapping_file = os.path.join(self.index_path, f"{file_id}.mapping")
        with open(mapping_file, 'wb') as f:
            pickle.dump(mapping, f)

        return index_file

    def search(
        self,
        file_id: str,
        query: str,
        k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Search for similar log records.

        Args:
            file_id: File identifier
            query: Search query
            k: Number of results to return

        Returns:
            List of (record_id, distance) tuples
        """
        try:
            import faiss
        except ImportError:
            logger.error("FAISS not installed")
            raise

        # Load index
        index_file = os.path.join(self.index_path, f"{file_id}.index")
        if not os.path.exists(index_file):
            logger.error(f"Index not found: {index_file}")
            return []

        index = faiss.read_index(index_file)

        # Load mapping
        mapping_file = os.path.join(self.index_path, f"{file_id}.mapping")
        with open(mapping_file, 'rb') as f:
            record_ids = pickle.load(f)

        # Create query embedding
        query_embedding = self.create_embeddings([query])

        # Search
        distances, indices = index.search(query_embedding, min(k, len(record_ids)))

        # Convert to results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(record_ids):
                # Convert L2 distance to similarity score (inverse)
                score = 1.0 / (1.0 + dist)
                results.append((record_ids[idx], float(score)))

        return results

    def get_index_stats(self, file_id: str) -> Dict[str, Any]:
        """Get statistics about an index."""
        try:
            import faiss
            index_file = os.path.join(self.index_path, f"{file_id}.index")

            if not os.path.exists(index_file):
                return {"error": "Index not found"}

            index = faiss.read_index(index_file)

            return {
                "total_vectors": index.ntotal,
                "dimension": self.dimension,
                "index_type": "FlatL2"
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {"error": str(e)}
