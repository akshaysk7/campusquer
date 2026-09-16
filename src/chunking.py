import re
import tiktoken
from typing import List, Dict, Any

def get_tokenizer():
    # Using cl100k_base which is standard for modern models
    return tiktoken.get_encoding("cl100k_base")

def split_text_by_structure(text: str) -> List[str]:
    """Split text primarily by paragraphs (double newlines), then sentences if too long."""
    # Split by paragraphs
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return paragraphs

def chunk_document(document: Dict[str, Any], max_tokens: int = 500, overlap_tokens: int = 75) -> List[Dict[str, Any]]:
    """
    Splits a document's text into chunks of roughly max_tokens.
    Splits on structure first (paragraphs), falling back to character splits if needed.
    Maintains metadata for every chunk.
    """
    tokenizer = get_tokenizer()
    paragraphs = split_text_by_structure(document["text"])
    
    chunks = []
    current_chunk_text = ""
    current_chunk_tokens = []
    
    for para in paragraphs:
        para_tokens = tokenizer.encode(para)
        
        if len(current_chunk_tokens) + len(para_tokens) <= max_tokens:
            current_chunk_tokens.extend(para_tokens)
            current_chunk_text += ("\n\n" if current_chunk_text else "") + para
        else:
            # Current chunk is full, save it
            if current_chunk_text:
                chunks.append({
                    "text": current_chunk_text,
                    "metadata": document["metadata"].copy()
                })
            
            # Start new chunk, incorporating overlap from previous chunk
            if overlap_tokens > 0 and len(current_chunk_tokens) > overlap_tokens:
                overlap_text = tokenizer.decode(current_chunk_tokens[-overlap_tokens:])
                current_chunk_tokens = tokenizer.encode(overlap_text) + para_tokens
                current_chunk_text = overlap_text + "\n\n" + para
            else:
                current_chunk_tokens = para_tokens
                current_chunk_text = para
                
            # If a single paragraph is longer than max_tokens, we need to hard split it
            while len(current_chunk_tokens) > max_tokens:
                # Force split
                chunk_tokens = current_chunk_tokens[:max_tokens]
                chunks.append({
                    "text": tokenizer.decode(chunk_tokens),
                    "metadata": document["metadata"].copy()
                })
                current_chunk_tokens = current_chunk_tokens[max_tokens - overlap_tokens:]
                current_chunk_text = tokenizer.decode(current_chunk_tokens)

    if current_chunk_text:
         chunks.append({
             "text": current_chunk_text,
             "metadata": document["metadata"].copy()
         })
         
    return chunks

def chunk_documents(documents: List[Dict[str, Any]], max_tokens: int = 500, overlap_tokens: int = 75) -> List[Dict[str, Any]]:
    all_chunks = []
    for doc in documents:
        all_chunks.extend(chunk_document(doc, max_tokens, overlap_tokens))
    return all_chunks
