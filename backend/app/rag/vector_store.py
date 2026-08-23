from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


COLLECTION_NAME = "industrial_maintenance"


class VectorStore:

    def __init__(self, storage_path: str = "data/qdrant"):
        self.storage_path = Path(storage_path)

        self.storage_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = QdrantClient(
            path=str(self.storage_path)
        )

    def create_collection(
        self,
        vector_size: int,
        recreate: bool = False,
    ):
        """
        Create the Industrial Maintenance collection.
        """

        collections = self.client.get_collections()

        existing_names = [
            collection.name
            for collection in collections.collections
        ]

        if COLLECTION_NAME in existing_names:

            if recreate:
                self.client.delete_collection(
                    COLLECTION_NAME
                )

            else:
                return

        self.client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    def upsert_chunks(
        self,
        chunks: list[dict],
        embeddings: list[list[float]],
    ):
        """
        Store chunks, embeddings and metadata.
        """

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings must match."
            )

        points = []

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):

            payload = {
                "text": chunk["text"],
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "document_name": chunk["document_name"],
                "document_type": chunk["document_type"],
                "machine_type": chunk["machine_type"],
                "section": chunk["section"],
                "section_number": chunk["section_number"],
                "page": chunk["page"],
                "source": chunk["source"],
            }

            point = PointStruct(
                id=index,
                vector=embedding,
                payload=payload,
            )

            points.append(point)

        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )

    def count(self) -> int:
        """
        Return number of stored vectors.
        """

        result = self.client.count(
            collection_name=COLLECTION_NAME,
            exact=True,
        )

        return result.count

    def get_collection_info(self):
        """
        Return collection information.
        """

        return self.client.get_collection(
            collection_name=COLLECTION_NAME
        )