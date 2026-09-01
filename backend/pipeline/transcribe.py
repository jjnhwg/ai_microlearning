import os
import tempfile

import boto3
import whisper

_s3 = boto3.client("s3")
_BUCKET = os.environ["SPEAKSHARP_S3_BUCKET"]
# load once at startup; override with WHISPER_MODEL=large-v3 in production
_model = whisper.load_model(os.environ.get("WHISPER_MODEL", "base"))


def transcribe(s3_key: str) -> dict:
    """Download audio from S3, transcribe, return word-level transcript."""
        #creates a temp file w an extension .audio 
    with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp:
         #download the audio file from S3 into the temp file
        _s3.download_fileobj(_BUCKET, s3_key, tmp)
        #store the path to the temp file for later use /tmp/tmpXYZ123.audio
        tmp_path = tmp.name

    try:
        #transcribe the audio file using the Whisper model
        result = _model.transcribe(tmp_path, word_timestamps=True)
        '''
    result =
        {
    "text": " Hello everyone, um, today I want to talk about my project.",
    "language": "en",
    "segments": [
        {
            "id": 0,
            "start": 0.0,
            "end": 3.2,
            "text": " Hello everyone, um, today I want to talk about my project.",
            "words": [
                {"word": " Hello",   "start": 0.0, "end": 0.5, "probability": 0.98},
                {"word": " everyone","start": 0.5, "end": 1.0, "probability": 0.95},
                {"word": " um",      "start": 1.2, "end": 1.4, "probability": 0.72},
                {"word": " today",   "start": 1.6, "end": 1.9, "probability": 0.99},
                {"word": " I",       "start": 2.0, "end": 2.1, "probability": 0.99},
                {"word": " want",    "start": 2.1, "end": 2.3, "probability": 0.97},
                ...
            ]
        },
        ...
    ]
}
        '''
        
    finally:
        #delete the temporary file to free up space
        os.unlink(tmp_path)

    words = []
    #store each word and its timestampe in a dictoniary within a list
    for segment in result["segments"]:
        for w in segment.get("words", []):
            words.append({
                "word": w["word"].strip(),
                #round the start and end times to 3 decimal places
                "start": round(w["start"], 3),
                "end": round(w["end"], 3),
                "confidence": round(w["probability"], 4),
            })

    return {
        "text": result["text"].strip(),
        "language": result["language"],
        "words": words,
    }
