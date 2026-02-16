# app.py - FIXED VERSION
from flask import Flask, request, jsonify, render_template
import logging
from chat2 import qa_chain
import traceback

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
        
        # Validate query
        if not query:
            logger.warning("Empty query received")
            return jsonify({
                'error': 'Empty query',
                'answer': 'Please enter a question about agriculture.'
            }), 400
        
        if len(query) > 500:
            logger.warning(f"Query too long: {len(query)} characters")
            return jsonify({
                'error': 'Query too long',
                'answer': 'Please keep your question under 500 characters.'
            }), 400
        
        # Check if chain is available
        if qa_chain is None:
            logger.error("QA chain not initialized")
            return jsonify({
                'error': 'Service unavailable',
                'answer': 'The chatbot service is currently unavailable. Please try again later.'
            }), 503
        
        logger.info(f"Processing query: {query[:50]}...")
        
        # ✓ FIXED: Use invoke() instead of calling directly
        response = qa_chain.invoke({"query": query})
        
        # Extract answer from response
        if isinstance(response, dict):
            # Try different possible keys
            answer = response.get('result', 
                     response.get('answer', 
                     response.get('output', 
                     str(response))))
        else:
            answer = str(response)
        
        # Clean up the answer
        answer = answer.strip()
        
        if not answer:
            answer = "I apologize, but I couldn't generate a response. Could you rephrase your question?"
        
        logger.info(f"Generated answer: {answer[:100]}...")
        
        # ✓ Return format that matches your JavaScript expectations
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
    """Health check endpoint"""
    chain_status = "healthy" if qa_chain is not None else "unhealthy"
    return jsonify({
        'status': chain_status,
        'service': 'AgriGenius',
        'version': '1.0'
    }), 200 if qa_chain else 503


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("🌾 AgriGenius - AI Agriculture Chatbot")
    print("="*50)
    print("Starting Flask server...")
    print("Navigate to: http://127.0.0.1:5000")
    print("Press CTRL+C to quit")
    print("="*50 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)