from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import csv
import random
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import requests
from urllib.parse import quote
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")

# Store bird list in memory
bird_list = []


def load_birds_from_csv(file_path):
    """Load bird names from CSV file."""
    global bird_list
    birds = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None or 'Common Name' not in reader.fieldnames:
                return None
            for row in reader:
                if row['Common Name'].strip():
                    birds.append(row['Common Name'].strip())
        # Remove duplicates while preserving order
        seen = set()
        unique_birds = []
        for bird in birds:
            if bird not in seen:
                seen.add(bird)
                unique_birds.append(bird)
        bird_list = unique_birds
        return unique_birds
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None


def get_similar_birds(bird_name, num_similar=3):
    """Use Azure OpenAI to get similar-looking birds."""
    try:
        message_text = f"""You are an ornithology expert. I need you to suggest {num_similar} bird species that look similar to the {bird_name}.

For each similar bird, just provide the common name, one per line. Only provide the bird names, nothing else. No numbering, no descriptions.

Similar birds to {bird_name}:"""
        
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are an ornithology expert who knows bird identification well. When asked for similar birds, respond with only the common names, one per line, with no additional text, numbering, or formatting."},
                {"role": "user", "content": message_text}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        similar_birds = response.choices[0].message.content.strip().split('\n')
        similar_birds = [bird.strip() for bird in similar_birds if bird.strip()]
        return similar_birds[:num_similar]
    except Exception as e:
        print(f"Error getting similar birds: {e}")
        return []


def fetch_bird_images(bird_name, num_images=2):
    """Fetch bird images from Bing Image Search."""
    try:
        # Using Bing Image Search via direct URL (no API key required for basic usage)
        search_url = f"https://www.bing.com/images/search?q={quote(bird_name + ' bird')}"
        
        # Alternative: Use a simple image search approach
        # Try multiple image search endpoints
        images = []
        
        # Try eBird photo search endpoint
        try:
            ebird_url = f"https://search.macaulaylibrary.org/api/v0/server?s={quote(bird_name)}&key=YOUR_EBIRD_KEY&media=p&limit=10"
            # For now, we'll use a simpler approach
        except:
            pass
        
        # Use a simple Bing search approach - return search URL that can be used client-side
        return {
            "search_term": bird_name,
            "search_url": search_url
        }
    except Exception as e:
        print(f"Error fetching images: {e}")
        return {"search_term": bird_name, "search_url": f"https://www.bing.com/images/search?q={quote(bird_name + ' bird')}"}


@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')


@app.route('/api/load-csv', methods=['POST'])
def load_csv():
    """Load birds from uploaded or specified CSV file."""
    data = request.json
    file_path = data.get('file_path', 'ebird_world_year_list.csv')
    
    # Ensure file exists in the current directory
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': f'File not found: {file_path}'}), 400
    
    birds = load_birds_from_csv(file_path)
    if birds is None:
        return jsonify({'success': False, 'error': 'CSV must have a "Common Name" column'}), 400
    
    return jsonify({'success': True, 'count': len(birds)})


@app.route('/api/quiz-question', methods=['GET'])
def get_quiz_question():
    """Generate a quiz question with random bird and options."""
    if not bird_list:
        return jsonify({'success': False, 'error': 'No birds loaded. Load a CSV first.'}), 400
    
    # Pick a random bird
    correct_bird = random.choice(bird_list)
    
    # Get similar birds
    similar_birds = get_similar_birds(correct_bird, num_similar=3)
    
    # Filter out any similar birds that might be the same as correct bird
    similar_birds = [b for b in similar_birds if b.lower() != correct_bird.lower()][:3]
    
    # If we don't have enough similar birds, fill with random birds from list
    while len(similar_birds) < 3:
        random_bird = random.choice(bird_list)
        if random_bird.lower() != correct_bird.lower() and random_bird not in similar_birds:
            similar_birds.append(random_bird)
    
    # Create options (1 correct + 3 similar)
    options = [correct_bird] + similar_birds[:3]
    random.shuffle(options)
    
    # Get images
    images = fetch_bird_images(correct_bird)
    
    return jsonify({
        'success': True,
        'correct_answer': correct_bird,
        'options': options,
        'images': images
    })


@app.route('/api/check-answer', methods=['POST'])
def check_answer():
    """Check if the user's answer is correct."""
    data = request.json
    user_answer = data.get('answer', '').strip()
    correct_answer = data.get('correct_answer', '').strip()
    
    is_correct = user_answer.lower() == correct_answer.lower()
    
    return jsonify({
        'success': True,
        'is_correct': is_correct,
        'correct_answer': correct_answer
    })


if __name__ == '__main__':
    # Load default bird list
    if os.path.exists('ebird_world_year_list.csv'):
        load_birds_from_csv('ebird_world_year_list.csv')
    
    app.run(debug=True, port=5000)
