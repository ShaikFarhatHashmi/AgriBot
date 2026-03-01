# test_accuracy.py - Simple Accuracy Testing for AgriGenius
# ===========================================================

from chat2 import qa_chain
import time

# Test questions with expected answer keywords
test_cases = [
    {
        "question": "What are the main crops grown during monsoon season in India?",
        "expected_keywords": ["rice", "maize", "cotton", "soybean", "groundnut"],
        "category": "Seasonal Crops"
    },
    {
        "question": "How can I control pests in rice farming?",
        "expected_keywords": ["pesticide", "insect", "spray", "organic", "neem"],
        "category": "Pest Control"
    },
    {
        "question": "What is the best fertilizer for wheat crops?",
        "expected_keywords": ["nitrogen", "phosphorus", "potassium", "urea", "NPK"],
        "category": "Fertilizers"
    },
    {
        "question": "What causes yellowing of leaves in plants?",
        "expected_keywords": ["nitrogen", "deficiency", "nutrient", "chlorosis", "iron"],
        "category": "Plant Disease"
    },
    {
        "question": "How much water does a rice crop need?",
        "expected_keywords": ["water", "irrigation", "flooded", "standing water", "cm"],
        "category": "Irrigation"
    },
    {
        "question": "What is crop rotation and why is it important?",
        "expected_keywords": ["rotation", "soil", "nutrients", "different crops", "fertility"],
        "category": "Farming Practices"
    },
    {
        "question": "How do I prepare soil for planting?",
        "expected_keywords": ["plough", "till", "organic matter", "compost", "preparation"],
        "category": "Soil Management"
    },
    {
        "question": "What is drip irrigation?",
        "expected_keywords": ["drip", "water", "efficient", "pipes", "slow"],
        "category": "Irrigation Technology"
    },
    {
        "question": "Which crops are good for dry land farming?",
        "expected_keywords": ["millet", "sorghum", "groundnut", "drought", "pulses"],
        "category": "Dry Farming"
    },
    {
        "question": "How to increase soil fertility naturally?",
        "expected_keywords": ["compost", "organic", "manure", "green manure", "natural"],
        "category": "Organic Farming"
    }
]

def test_accuracy():
    """Test the chatbot and calculate accuracy"""
    
    print("\n" + "="*60)
    print("🧪 TESTING AGRIGENIUS CHATBOT ACCURACY")
    print("="*60 + "\n")
    
    correct = 0
    total = len(test_cases)
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}/{total}] Category: {test['category']}")
        print(f"Question: {test['question']}")
        
        try:
            # Get response from chatbot
            start_time = time.time()
            response = qa_chain.invoke({"query": test['question']})
            response_time = time.time() - start_time
            
            # Extract answer
            if isinstance(response, dict):
                answer = response.get('result', response.get('answer', str(response)))
            else:
                answer = str(response)
            
            answer_lower = answer.lower()
            
            # Check if any expected keywords are in the answer
            found_keywords = [kw for kw in test['expected_keywords'] if kw.lower() in answer_lower]
            
            # Calculate score (at least 1 keyword = correct)
            is_correct = len(found_keywords) > 0
            confidence = (len(found_keywords) / len(test['expected_keywords'])) * 100
            
            if is_correct:
                correct += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            
            print(f"Status: {status}")
            print(f"Response Time: {response_time:.2f}s")
            print(f"Confidence: {confidence:.1f}%")
            print(f"Keywords Found: {', '.join(found_keywords) if found_keywords else 'None'}")
            print(f"Answer Preview: {answer[:150]}...")
            
            results.append({
                "question": test['question'],
                "category": test['category'],
                "correct": is_correct,
                "confidence": confidence,
                "response_time": response_time
            })
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "question": test['question'],
                "category": test['category'],
                "correct": False,
                "confidence": 0,
                "response_time": 0
            })
    
    # Calculate overall metrics
    accuracy = (correct / total) * 100
    avg_confidence = sum(r['confidence'] for r in results) / total
    avg_response_time = sum(r['response_time'] for r in results) / total
    
    # Print summary
    print("\n" + "="*60)
    print("📊 ACCURACY TEST RESULTS")
    print("="*60)
    print(f"\n✅ Correct Answers: {correct}/{total}")
    print(f"📈 Overall Accuracy: {accuracy:.1f}%")
    print(f"💯 Average Confidence: {avg_confidence:.1f}%")
    print(f"⚡ Average Response Time: {avg_response_time:.2f}s")
    
    # Category breakdown
    print("\n📋 Category Breakdown:")
    categories = {}
    for r in results:
        cat = r['category']
        if cat not in categories:
            categories[cat] = {'correct': 0, 'total': 0}
        categories[cat]['total'] += 1
        if r['correct']:
            categories[cat]['correct'] += 1
    
    for cat, stats in categories.items():
        cat_accuracy = (stats['correct'] / stats['total']) * 100
        print(f"   {cat}: {stats['correct']}/{stats['total']} ({cat_accuracy:.0f}%)")
    
    # Quality rating
    print("\n🏆 Quality Rating:")
    if accuracy >= 90:
        rating = "⭐⭐⭐⭐⭐ Excellent!"
    elif accuracy >= 80:
        rating = "⭐⭐⭐⭐ Very Good!"
    elif accuracy >= 70:
        rating = "⭐⭐⭐ Good"
    elif accuracy >= 60:
        rating = "⭐⭐ Fair"
    else:
        rating = "⭐ Needs Improvement"
    
    print(f"   {rating}")
    
    print("\n" + "="*60 + "\n")
    
    return accuracy, results


if __name__ == "__main__":
    print("\n🌾 Starting AgriGenius Accuracy Test...")
    print("⏳ This will take about 1-2 minutes...\n")
    
    try:
        accuracy, results = test_accuracy()
        
        # Save results to file
        with open("accuracy_results.txt", "w") as f:
            f.write("AgriGenius Accuracy Test Results\n")
            f.write("="*60 + "\n\n")
            f.write(f"Overall Accuracy: {accuracy:.1f}%\n\n")
            f.write("Individual Test Results:\n")
            f.write("-"*60 + "\n")
            for i, r in enumerate(results, 1):
                status = "PASS" if r['correct'] else "FAIL"
                f.write(f"{i}. [{status}] {r['category']}\n")
                f.write(f"   Question: {r['question']}\n")
                f.write(f"   Confidence: {r['confidence']:.1f}%\n")
                f.write(f"   Response Time: {r['response_time']:.2f}s\n\n")
        
        print("📄 Results saved to: accuracy_results.txt")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()