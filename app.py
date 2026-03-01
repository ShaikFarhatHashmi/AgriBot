# app.py - UPDATED VERSION
# Change from old chat2.py: imports get_chain() instead of qa_chain directly.
# This is required because chat2.py now uses lazy initialization —
# qa_chain starts as None and is only built on the first request.

from flask import Flask, request, jsonify, render_template
import logging
import traceback
import os
from chat2 import get_chain   # ← updated: was "from chat2 import qa_chain"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/')
def home():
    """Render the home page"""
    return render_template('index.html')


@app.route('/ask', methods=['POST'])
def ask():
    """Handle user queries with comprehensive error handling"""
    try:
        # Get query from form data (jQuery sends as form, not JSON)
        query = request.form.get('messageText', '').strip()

        # Validate: empty query
        if not query:
            logger.warning("Empty query received")
            return jsonify({
                'error': 'Empty query',
                'answer': 'Please enter a question about agriculture.'
            }), 400

        # Validate: query too long
        if len(query) > 500:
            logger.warning(f"Query too long: {len(query)} characters")
            return jsonify({
                'error': 'Query too long',
                'answer': 'Please keep your question under 500 characters.'
            }), 400

        # ── Get chain via lazy loader ──────────────────────────────────────────
        # get_chain() builds the chain on the very first call, then reuses it.
        # If setup fails (bad API key, no documents, etc.) it raises an exception
        # which we catch here and return a clean error to the user.
        try:
            chain = get_chain()
        except Exception as chain_err:
            logger.error(f"Failed to initialize QA chain: {chain_err}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Service unavailable',
                'answer': 'The chatbot service failed to initialize. Please check your setup and try again.'
            }), 503

        logger.info(f"Processing query: {query[:50]}...")

        # Invoke the chain
        response = chain.invoke({"query": query})

        # Extract answer — try different possible keys LangChain may return
        if isinstance(response, dict):
            answer = response.get('result',
                     response.get('answer',
                     response.get('output',
                     str(response))))
        else:
            answer = str(response)

        answer = answer.strip()

        if not answer:
            answer = "I apologize, but I couldn't generate a response. Could you rephrase your question?"

        logger.info(f"Generated answer: {answer[:100]}...")

        return jsonify({
            'answer': answer,
            'status': 'success'
        }), 200

    except ValueError as e:
        logger.error(f"ValueError: {e}")
        return jsonify({
            'error': 'Invalid input',
            'answer': 'There was an error with your input. Please try again.'
        }), 400

    except ConnectionError as e:
        logger.error(f"ConnectionError: {e}")
        return jsonify({
            'error': 'Connection error',
            'answer': 'Unable to connect to the AI service. Please check your internet connection.'
        }), 503

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Processing error',
            'answer': 'Sorry, there was an error processing your request. Please try again later.'
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    Tries to get the chain — if it succeeds the service is healthy.
    Returns 200 if healthy, 503 if not.
    """
    try:
        chain = get_chain()
        status = "healthy" if chain is not None else "unhealthy"
        http_code = 200 if chain is not None else 503
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        status = "unhealthy"
        http_code = 503

    return jsonify({
        'status': status,
        'service': 'AgriGenius',
        'version': '1.0'
    }), http_code


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    print("\n" + "="*50)
    print("🌾 AgriBot - AI Agriculture Chatbot")
    print("="*50)
    print("Starting Flask server...")
    print("Navigate to: http://127.0.0.1:5000")
    print("Note: First request will take 2-5 mins to build the AI chain.")
    print("Press CTRL+C to quit")
    print("="*50 + "\n")

    app.run(debug=debug_mode, use_reloader=False, host='127.0.0.1', port=5000)