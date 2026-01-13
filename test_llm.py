from app.utils.llm_extractor import extract_meeting_data

sample_transcript = """
Today we discussed project progress.
Taniya will create the UI by Wednesday.
Riya will integrate Whisper by Friday.
We decided to deploy the app on Render.
Potential blocker is limited time.
"""

data = extract_meeting_data(sample_transcript)
print(data)
