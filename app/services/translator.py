"""
app/services/translator.py
Free multilingual translation using Google Translate
via deep-translator. No API key required.
"""
from deep_translator import GoogleTranslator

# All Indian languages supported by your bot
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi — हिंदी",
    "te": "Telugu — తెలుగు",
    "ta": "Tamil — தமிழ்",
    "kn": "Kannada — ಕನ್ನಡ",
    "ml": "Malayalam — മലയാളം",
    "mr": "Marathi — मराठी",
    "bn": "Bengali — বাংলা",
    "gu": "Gujarati — ગુજરાતી",
    "pa": "Punjabi — ਪੰਜਾਬੀ",
    "ur": "Urdu — اردو",
}


def translate_to_english(text, source_lang):
    """
    Translate user input from their language to English
    before sending to RAG pipeline.
    If source is already English, return as-is.
    """
    if source_lang == "en" or not text.strip():
        return text
    try:
        translated = GoogleTranslator(
            source=source_lang,
            target="en"
        ).translate(text)
        return translated or text   # fallback to original if translation fails
    except Exception as e:
        print(f"[Translator] to_english failed: {e}")
        return text                 # fallback — never crash the chat


def translate_from_english(text, target_lang):
    """
    Translate English RAG answer back to user's language.
    If target is English, return as-is.
    """
    if target_lang == "en" or not text.strip():
        return text
    try:
        # Google Translate has a 5000 char limit per request
        # Split long answers into chunks if needed
        if len(text) <= 4500:
            translated = GoogleTranslator(
                source="en",
                target=target_lang
            ).translate(text)
            return translated or text

        # Long text — translate in chunks
        chunks     = _split_text(text, max_length=4500)
        translated = []
        for chunk in chunks:
            result = GoogleTranslator(
                source="en",
                target=target_lang
            ).translate(chunk)
            translated.append(result or chunk)
        return "\n".join(translated)

    except Exception as e:
        print(f"[Translator] from_english failed: {e}")
        return text                 # fallback — always return something


def _split_text(text, max_length=4500):
    """Split text at sentence boundaries to stay under API limit."""
    sentences = text.replace("\n", " \n ").split(". ")
    chunks, current = [], ""
    for sentence in sentences:
        if len(current) + len(sentence) < max_length:
            current += sentence + ". "
        else:
            if current:
                chunks.append(current.strip())
            current = sentence + ". "
    if current:
        chunks.append(current.strip())
    return chunks if chunks else [text]