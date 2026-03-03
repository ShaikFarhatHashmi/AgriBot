import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging so you can see EXACTLY what is happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from app import create_app

app = create_app()

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  AgriBot - AI Agriculture Assistant")
    print("=" * 55)
    print("  URL  : http://127.0.0.1:5000")
    print("  Login: http://127.0.0.1:5000/auth/login")
    print("")
    print("  STATUS: Server is running and waiting...")
    print("  ACTION: Open browser and type a question")
    print("          Terminal will show progress here")
    print("")
    print("  FIRST QUESTION will take 2-5 mins because:")
    print("  1. Embedding model loads from cache")
    print("  2. ChromaDB loads from disk")
    print("  3. Groq LLM connects")
    print("  After that every answer comes in seconds.")
    print("")
    print("  Stop : CTRL + C")
    print("=" * 55 + "\n")

    app.run(
        debug=False,
        use_reloader=False,
        host="127.0.0.1",
        port=5000
    )