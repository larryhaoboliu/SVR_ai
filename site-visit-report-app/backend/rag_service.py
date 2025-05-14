import os
import sys
import pickle
import tempfile
import logging
from typing import List, Dict, Any, Optional

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import TextLoader
from langchain.vectorstores.base import VectorStore
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
import pinecone
from langchain.vectorstores import Pinecone

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
    """Service for Retrieval-Augmented Generation with product data."""
    
    def __init__(self):
        """Initialize the RAG service."""
        self.embedding_model = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
        self.vector_store = None
        self.use_pinecone = False  # Will be set to True if Pinecone environment variables are found
        self.pinecone_initialized = False
        self.initialize_vector_store()
    
    def initialize_vector_store(self):
        """Initialize the vector store from pickle file or create a new one."""
        try:
            # Check for Pinecone environment variables
            pinecone_api_key = os.getenv("PINECONE_API_KEY")
            pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
            pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
            
            # If all Pinecone variables are set, use Pinecone
            if pinecone_api_key and pinecone_environment and pinecone_index_name:
                logger.info("Using Pinecone as vector database")
                self.use_pinecone = True
                
                if not self.pinecone_initialized:
                    pinecone.init(api_key=pinecone_api_key, environment=pinecone_environment)
                    self.pinecone_initialized = True
                
                # Check if index exists
                if pinecone_index_name in pinecone.list_indexes():
                    self.vector_store = Pinecone.from_existing_index(
                        index_name=pinecone_index_name,
                        embedding=self.embedding_model
                    )
                    logger.info(f"Connected to existing Pinecone index: {pinecone_index_name}")
                else:
                    # If index doesn't exist, let's create it with product data
                    logger.info(f"Pinecone index '{pinecone_index_name}' not found. Creating and populating it.")
                    self._create_pinecone_index(pinecone_index_name)
                    self.rebuild_vector_store()
            else:
                # Fall back to local FAISS
                logger.info("Using local FAISS vector database")
                self.use_pinecone = False
                
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
    
    def _create_pinecone_index(self, index_name):
        """Create a new Pinecone index with the appropriate dimension."""
        # Get embeddings dimension for the chosen model
        dimension = len(self.embedding_model.embed_query("Test"))
        
        # Create the index
        pinecone.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine"
        )
        logger.info(f"Created new Pinecone index: {index_name} with dimension {dimension}")
    
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
            
            # Add the chunks to the vector store
            if self.use_pinecone:
                # Add to Pinecone
                pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
                if not self.vector_store:
                    self.vector_store = Pinecone.from_documents(
                        chunks, self.embedding_model, index_name=pinecone_index_name
                    )
                else:
                    self.vector_store.add_documents(chunks)
                logger.info(f"Added {len(chunks)} chunks to Pinecone index")
            else:
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
            # Create a new vector store
            if self.use_pinecone:
                # For Pinecone, we'll first clear the index then re-add all documents
                pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
                if pinecone_index_name in pinecone.list_indexes():
                    logger.info(f"Clearing Pinecone index: {pinecone_index_name}")
                    index = pinecone.Index(pinecone_index_name)
                    index.delete(delete_all=True)
                    
                # Initialize empty vector store
                self.vector_store = None
            else:
                # For local FAISS, we'll create a new vector store
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
    """
    Get the RAG service singleton instance.
    
    Returns:
        RAGService: The RAG service instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service 