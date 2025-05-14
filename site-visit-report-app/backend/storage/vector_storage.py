import os
import logging
import pickle
from typing import List, Dict, Any, Optional
import uuid
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
import pinecone
from langchain.vectorstores import Pinecone
from langchain.docstore.document import Document

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
LOCAL_VECTOR_STORE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vector_store.pkl")

class VectorStorage:
    """
    Vector storage implementation that can use either local FAISS or Pinecone
    """
    
    def __init__(self, storage_type="auto"):
        """
        Initialize vector storage
        
        Args:
            storage_type: "local", "pinecone", or "auto" (default: use Pinecone if configured, otherwise local)
        """
        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Read configuration
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        self.pinecone_environment = os.getenv('PINECONE_ENVIRONMENT')
        self.pinecone_index_name = os.getenv('PINECONE_INDEX_NAME', 'svr-product-data')
        
        # Determine storage type
        if storage_type == "auto":
            if self.pinecone_api_key and self.pinecone_environment:
                self.storage_type = "pinecone"
                logger.info("Using Pinecone for vector storage")
            else:
                self.storage_type = "local"
                logger.info("Using local FAISS for vector storage (Pinecone not configured)")
        else:
            self.storage_type = storage_type
            
        # Initialize storage based on type
        if self.storage_type == "pinecone":
            self._init_pinecone()
        else:
            self._init_local()
    
    def _init_pinecone(self):
        """Initialize Pinecone vector store"""
        try:
            # Initialize Pinecone
            pinecone.init(
                api_key=self.pinecone_api_key,
                environment=self.pinecone_environment
            )
            
            # Check if index exists and create it if it doesn't
            existing_indexes = pinecone.list_indexes()
            if self.pinecone_index_name not in existing_indexes:
                # Get embedding dimension
                dimension = len(self.embeddings.embed_query("test"))
                
                # Create the index
                pinecone.create_index(
                    name=self.pinecone_index_name,
                    dimension=dimension,
                    metric="cosine"
                )
                logger.info(f"Created new Pinecone index: {self.pinecone_index_name}")
                
                # Connect to the index and create empty vector store
                index = pinecone.Index(self.pinecone_index_name)
                self.vector_store = Pinecone(index, self.embeddings.embed_query, "text")
            else:
                # Connect to existing index
                index = pinecone.Index(self.pinecone_index_name)
                self.vector_store = Pinecone(index, self.embeddings.embed_query, "text")
                logger.info(f"Connected to existing Pinecone index: {self.pinecone_index_name}")
                
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {e}")
            # Fallback to local storage if Pinecone fails
            logger.warning("Falling back to local vector storage")
            self.storage_type = "local"
            self._init_local()
    
    def _init_local(self):
        """Initialize local FAISS vector store"""
        try:
            # First try to load existing vector store
            if os.path.exists(LOCAL_VECTOR_STORE_PATH):
                with open(LOCAL_VECTOR_STORE_PATH, "rb") as f:
                    self.vector_store = pickle.load(f)
                logger.info(f"Loaded local vector store from {LOCAL_VECTOR_STORE_PATH}")
            else:
                # If it doesn't exist, import FAISS and create a new one
                from langchain_community.vectorstores import FAISS
                
                # Create an empty vector store with a dummy document
                self.vector_store = FAISS.from_texts(["Empty vector store initialization. Delete me."], self.embeddings)
                self._save_local_vector_store()
                logger.info(f"Created new local vector store at {LOCAL_VECTOR_STORE_PATH}")
        except Exception as e:
            logger.error(f"Error initializing local vector store: {e}")
            # Create an empty store if loading fails
            from langchain_community.vectorstores import FAISS
            self.vector_store = FAISS.from_texts(["Empty vector store initialization. Delete me."], self.embeddings)
            self._save_local_vector_store()
            logger.warning(f"Created new local vector store due to error: {e}")
    
    def _save_local_vector_store(self):
        """Save local vector store to disk"""
        if self.storage_type == "local":
            try:
                with open(LOCAL_VECTOR_STORE_PATH, "wb") as f:
                    pickle.dump(self.vector_store, f)
                logger.info(f"Saved local vector store to {LOCAL_VECTOR_STORE_PATH}")
            except Exception as e:
                logger.error(f"Error saving local vector store: {e}")
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Add texts to the vector store
        
        Args:
            texts: List of text strings to add
            metadatas: List of metadata dictionaries (optional)
            
        Returns:
            List of IDs for the added texts
        """
        try:
            # Handle missing metadatas
            if not metadatas:
                metadatas = [{} for _ in texts]
            
            # Add document IDs if missing
            for metadata in metadatas:
                if "id" not in metadata:
                    metadata["id"] = str(uuid.uuid4())
            
            # Add texts to vector store
            ids = []
            
            if self.storage_type == "pinecone":
                # Using Pinecone
                ids = self.vector_store.add_texts(texts, metadatas)
            else:
                # Using local FAISS
                import numpy as np
                
                # Get text embeddings
                embeddings = [self.embeddings.embed_query(text) for text in texts]
                
                # Add to FAISS index
                for i, (text, metadata) in enumerate(zip(texts, metadatas)):
                    doc_id = metadata.get("id", str(uuid.uuid4()))
                    self.vector_store.add_embeddings(
                        text_embeddings=[(text, np.array(embeddings[i]))],
                        metadatas=[metadata]
                    )
                    ids.append(doc_id)
                
                # Save the updated vector store
                self._save_local_vector_store()
            
            return ids
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {e}")
            return []
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store
        
        Args:
            documents: List of Document objects
            
        Returns:
            List of IDs for the added documents
        """
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        return self.add_texts(texts, metadatas)
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        Perform similarity search
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List of Documents most similar to the query
        """
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return []
    
    def similarity_search_with_score(self, query: str, k: int = 4) -> List[tuple]:
        """
        Perform similarity search with scores
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List of (Document, score) tuples
        """
        try:
            return self.vector_store.similarity_search_with_score(query, k=k)
        except Exception as e:
            logger.error(f"Error performing similarity search with score: {e}")
            return []
    
    def clear(self) -> bool:
        """
        Clear all vectors from the store
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.storage_type == "pinecone":
                # Delete the index and recreate it
                pinecone.delete_index(self.pinecone_index_name)
                
                # Get embedding dimension
                dimension = len(self.embeddings.embed_query("test"))
                
                # Recreate the index
                pinecone.create_index(
                    name=self.pinecone_index_name,
                    dimension=dimension,
                    metric="cosine"
                )
                
                # Reconnect to the index
                index = pinecone.Index(self.pinecone_index_name)
                self.vector_store = Pinecone(index, self.embeddings.embed_query, "text")
            else:
                # For local storage, create a new empty vector store
                from langchain_community.vectorstores import FAISS
                self.vector_store = FAISS.from_texts(["Empty vector store initialization. Delete me."], self.embeddings)
                self._save_local_vector_store()
            
            return True
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            return False

# Singleton instance
_vector_storage = None

def get_vector_storage(storage_type="auto"):
    """Get or create the vector storage singleton."""
    global _vector_storage
    if _vector_storage is None:
        _vector_storage = VectorStorage(storage_type)
    return _vector_storage 