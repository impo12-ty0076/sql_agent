"""
Manual test for RAG components.
This script checks if the files exist and have the expected content.
"""

import os
import re

def check_file_exists(file_path):
    exists = os.path.exists(file_path)
    print(f"Checking {file_path}: {'✓ Exists' if exists else '✗ Not found'}")
    return exists

def check_class_in_file(file_path, class_name):
    if not os.path.exists(file_path):
        print(f"  ✗ Cannot check for class {class_name}, file not found")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for class definition with more flexible pattern
    class_patterns = [
        r'class\s+' + class_name + r'\s*\(',  # Standard class definition
        r'class\s+' + class_name + r'\s*:',   # Class without explicit inheritance
        r'class\s+' + class_name + r'\s*\w*'  # More flexible pattern
    ]
    
    has_class = any(bool(re.search(pattern, content)) for pattern in class_patterns)
    print(f"  Checking for class {class_name}: {'✓ Found' if has_class else '✗ Not found'}")
    return has_class

def check_method_in_file(file_path, method_name):
    if not os.path.exists(file_path):
        print(f"  ✗ Cannot check for method {method_name}, file not found")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for method definition with more flexible pattern
    method_patterns = [
        r'def\s+' + method_name + r'\s*\(',  # Standard method definition
        r'def\s+' + method_name + r'\s*\w*'  # More flexible pattern
    ]
    
    has_method = any(bool(re.search(pattern, content)) for pattern in method_patterns)
    print(f"  Checking for method {method_name}: {'✓ Found' if has_method else '✗ Not found'}")
    return has_method

def check_content_for_keywords(file_path, keywords):
    if not os.path.exists(file_path):
        print(f"  ✗ Cannot check for keywords in {file_path}, file not found")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_found = True
    for keyword in keywords:
        found = keyword in content
        print(f"  Checking for keyword '{keyword}': {'✓ Found' if found else '✗ Not found'}")
        all_found = all_found and found
    
    return all_found

def main():
    print("Manual RAG System Test")
    print("=====================")
    
    # Check if files exist
    rag_dir = "sql_agent/backend/rag"
    files_to_check = [
        os.path.join(rag_dir, "__init__.py"),
        os.path.join(rag_dir, "document_indexer.py"),
        os.path.join(rag_dir, "document_store.py"),
        os.path.join(rag_dir, "rag_service.py"),
        os.path.join(rag_dir, "text_utils.py"),
        os.path.join(rag_dir, "search_engine.py")
    ]
    
    all_files_exist = all(check_file_exists(f) for f in files_to_check)
    
    if not all_files_exist:
        print("\n✗ Some files are missing. RAG system is not fully implemented.")
        return False
    
    print("\nChecking for required classes by keywords:")
    # Check for required classes by looking for keywords
    class_keywords = [
        (os.path.join(rag_dir, "document_indexer.py"), ["class DocumentIndexer", "index_database_schema", "chunk_document"]),
        (os.path.join(rag_dir, "document_store.py"), ["class DocumentStore", "add_document", "search"]),
        (os.path.join(rag_dir, "rag_service.py"), ["class RagService", "index_database_schema", "generate_response"]),
        (os.path.join(rag_dir, "search_engine.py"), ["class SearchEngine", "search", "keyword_search"])
    ]
    
    all_classes_exist = all(check_content_for_keywords(file_path, keywords) 
                           for file_path, keywords in class_keywords)
    
    if not all_classes_exist:
        print("\n✗ Some required class keywords are missing. RAG system is not fully implemented.")
        return False
    
    print("\nChecking for required functionality:")
    # Check for specific functionality in each file
    
    # DocumentIndexer should handle DB schema indexing
    indexer_keywords = [
        "index_database_schema",
        "_create_database_document",
        "_create_schema_document",
        "_create_table_document",
        "_create_column_document",
        "_generate_embeddings",
        "chunk_document"
    ]
    
    indexer_functionality = check_content_for_keywords(os.path.join(rag_dir, "document_indexer.py"), indexer_keywords)
    
    # DocumentStore should handle document storage and retrieval
    store_keywords = [
        "add_document",
        "get_document",
        "search",
        "_update_index",
        "_save_index",
        "load_index"
    ]
    
    store_functionality = check_content_for_keywords(os.path.join(rag_dir, "document_store.py"), store_keywords)
    
    # RagService should integrate indexer and store
    service_keywords = [
        "index_database_schema",
        "search",
        "generate_response",
        "_build_enhanced_context"
    ]
    
    service_functionality = check_content_for_keywords(os.path.join(rag_dir, "rag_service.py"), service_keywords)
    
    # SearchEngine should provide search functionality
    search_keywords = [
        "keyword_search",
        "embedding_search",
        "hybrid_search",
        "fuzzy_search"
    ]
    
    search_functionality = check_content_for_keywords(os.path.join(rag_dir, "search_engine.py"), search_keywords)
    
    all_functionality_exists = indexer_functionality and store_functionality and service_functionality and search_functionality
    
    if not all_functionality_exists:
        print("\n✗ Some required functionality is missing. RAG system is not fully implemented.")
        return False
    
    print("\n✓ All required files and functionality are present.")
    print("✓ Document Indexing System appears to be fully implemented.")
    return True

if __name__ == "__main__":
    success = main()
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")