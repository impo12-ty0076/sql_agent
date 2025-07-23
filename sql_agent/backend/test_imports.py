import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from rag.document_indexer import DocumentIndexer
    from rag.document_store import DocumentStore
    from rag.rag_service import RagService
    from rag.text_utils import normalize_text, extract_keywords
    print("All imports successful!")
    
    # Check if FAISS is available
    try:
        import faiss
        print("FAISS is available")
    except ImportError:
        print("FAISS is not available")
    
    # Check if tiktoken is available
    try:
        import tiktoken
        print("tiktoken is available")
    except ImportError:
        print("tiktoken is not available")
        
    # Check if langchain is available
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        print("langchain is available")
    except ImportError:
        print("langchain is not available")
        
except Exception as e:
    print(f"Error importing modules: {e}")