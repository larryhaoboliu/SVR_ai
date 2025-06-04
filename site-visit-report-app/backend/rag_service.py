import os
import sys
import pickle
import tempfile
import logging
from typing import List, Dict, Any, Optional

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory for product data
PRODUCT_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'product_data')
os.makedirs(PRODUCT_DATA_DIR, exist_ok=True)

# Path to the vector store file
VECTOR_STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vector_store.pkl')

# Embedding model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast and good quality model

class RAGService:
    """Service for Retrieval-Augmented Generation with product data using local FAISS storage."""
    
    def __init__(self):
        """Initialize the RAG service."""
        self.embedding_model = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
        self.vector_store = None
        self.initialize_vector_store()
    
    def initialize_vector_store(self):
        """Initialize the vector store from pickle file or create a new one."""
        try:
            logger.info("Using local FAISS vector database")
            
            if os.path.exists(VECTOR_STORE_PATH):
                with open(VECTOR_STORE_PATH, 'rb') as f:
                    self.vector_store = pickle.load(f)
                logger.info(f"Loaded vector store from {VECTOR_STORE_PATH}")
            else:
                logger.info("No existing vector store found. Creating a new one.")
                self.rebuild_vector_store()
                    
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            # Create an empty FAISS vector store as fallback
            self.vector_store = FAISS.from_texts([""], self.embedding_model)
    
    def add_product_data(self, file_path: str) -> bool:
        """
        Add product data from a file (PDF or TXT) to the vector store.
        
        Args:
            file_path: Path to the file to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load the document
            documents = []
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                loader = PyPDFLoader(file_path)
                documents = loader.load()
                logger.info(f"Loaded PDF: {file_path}")
            elif file_ext == '.txt':
                loader = TextLoader(file_path)
                documents = loader.load()
                logger.info(f"Loaded text file: {file_path}")
            else:
                logger.error(f"Unsupported file format: {file_ext}")
                return False
            
            # Split the document into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", " ", ""]
            )
            chunks = text_splitter.split_documents(documents)
            
            # Add to local FAISS
            if not self.vector_store:
                self.vector_store = FAISS.from_documents(chunks, self.embedding_model)
            else:
                self.vector_store.add_documents(chunks)
            
            # Save the updated vector store
            with open(VECTOR_STORE_PATH, 'wb') as f:
                pickle.dump(self.vector_store, f)
            logger.info(f"Added {len(chunks)} chunks to local vector store and saved to {VECTOR_STORE_PATH}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding product data: {str(e)}")
            return False
    
    def rebuild_vector_store(self) -> bool:
        """
        Rebuild the vector store from all files in the product_data directory.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a new local FAISS vector store
            self.vector_store = FAISS.from_texts([""], self.embedding_model)
            
            # Add all files in the product_data directory
            success = True
            file_count = 0
            
            for filename in os.listdir(PRODUCT_DATA_DIR):
                file_path = os.path.join(PRODUCT_DATA_DIR, filename)
                if os.path.isfile(file_path) and (file_path.lower().endswith('.pdf') or file_path.lower().endswith('.txt')):
                    if self.add_product_data(file_path):
                        file_count += 1
                    else:
                        success = False
            
            logger.info(f"Rebuilt vector store with {file_count} files")
            return success
            
        except Exception as e:
            logger.error(f"Error rebuilding vector store: {str(e)}")
            return False
    
    def query_product_data(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Query the vector store for relevant product data.
        
        Args:
            query: Query string
            k: Number of results to return
            
        Returns:
            List of dictionaries with source and content
        """
        try:
            if not self.vector_store:
                logger.warning("Vector store not initialized")
                return []
            
            # Search the vector store
            results = self.vector_store.similarity_search(query, k=k)
            
            # Format the results
            formatted_results = []
            for doc in results:
                formatted_results.append({
                    "source": doc.metadata.get("source", "Unknown"),
                    "content": doc.page_content
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying product data: {str(e)}")
            return []

# Singleton instance
_rag_service = None

def get_rag_service() -> RAGService:
    """Get or create the RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service 