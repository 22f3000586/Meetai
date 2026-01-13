"""
Text cleaning utilities for meeting transcripts.
"""
import re

def clean_transcript(transcript: str) -> str:
    """
    Clean and preprocess the transcript text.
    
    Args:
        transcript (str): Raw transcript text
        
    Returns:
        str: Cleaned transcript text
    """
    if not transcript:
        return ""
    
    # Remove extra whitespace and newlines
    cleaned = ' '.join(transcript.split())
    
    # Add spaces after periods if they're missing
    cleaned = re.sub(r'\.(\w)', r'. \1', cleaned)
    
    # Remove speaker labels if they exist (e.g., "Speaker 1:")
    cleaned = re.sub(r'\b(?:Speaker|Speaker \d+):\s*', '', cleaned)
    
    # Remove timestamps if they exist (e.g., [00:00:00])
    cleaned = re.sub(r'\[\d+:\d+:\d+\]\s*', '', cleaned)
    
    # Remove any remaining special characters except basic punctuation and letters
    cleaned = re.sub(r'[^\w\s.,!?]', ' ', cleaned)
    
    # Replace multiple spaces with a single space
    cleaned = ' '.join(cleaned.split())
    
    # Ensure proper spacing around punctuation
    cleaned = re.sub(r'\s+([.,!?])(?=\s|$)', r'\1', cleaned)
    
    # Capitalize the first letter of each sentence
    sentences = re.split(r'([.!?]\s+)', cleaned)
    cleaned = ''
    for i in range(0, len(sentences)-1, 2):
        if i+1 < len(sentences):
            cleaned += sentences[i].capitalize() + sentences[i+1]
        else:
            cleaned += sentences[i].capitalize()
    
    return cleaned.strip()
