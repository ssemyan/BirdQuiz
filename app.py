from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import csv
import random
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import requests
from urllib.parse import quote
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Azure OpenAI with Azure AD authentication
credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=token_provider
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

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
        
        response_text = response.choices[0].message.content.strip()
        print(f"[OpenAI Response for '{bird_name}']: {response_text}")
        
        similar_birds = response_text.split('\n')
        similar_birds = [bird.strip() for bird in similar_birds if bird.strip()]
        return similar_birds[:num_similar]
    except Exception as e:
        print(f"Error getting similar birds: {e}")
        print(f"  - API Key set: {bool(os.getenv('AZURE_OPENAI_API_KEY'))}")
        print(f"  - API Base: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"  - Deployment: {DEPLOYMENT_NAME}")
        return []


def fetch_bird_images(bird_name, num_images=3):
    """Fetch bird images from Wikimedia Commons."""
    try:
        # Headers with User-Agent to avoid 403
        headers = {
            'User-Agent': 'BirdIdentificationQuiz/1.0 (Student project)'
        }
        
        # Query Wikimedia Commons API for bird images
        search_term = f"{bird_name}"
        wiki_params = {
            'action': 'query',
            'list': 'search',
            'srsearch': search_term,
            'format': 'json',
            'srnamespace': '6',  # File namespace
            'srlimit': 20
        }
        
        response = requests.get('https://commons.wikimedia.org/w/api.php', params=wiki_params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        images = []
        if data.get('query', {}).get('search'):
            for item in data['query']['search'][:num_images * 3]:  # Try more to filter
                file_title = item['title']
                # Skip non-image files
                if not any(file_title.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    continue
                    
                # Get file URL
                file_params = {
                    'action': 'query',
                    'titles': file_title,
                    'prop': 'imageinfo',
                    'iiprop': 'url',
                    'format': 'json'
                }
                file_response = requests.get('https://commons.wikimedia.org/w/api.php', params=file_params, headers=headers, timeout=5)
                file_response.raise_for_status()
                file_data = file_response.json()
                
                pages = file_data.get('query', {}).get('pages', {})
                for page_id, page_info in pages.items():
                    if 'imageinfo' in page_info:
                        image_url = page_info['imageinfo'][0]['url']
                        # Only use images that are reasonably sized
                        if image_url and 'upload.wikimedia.org' in image_url:
                            images.append(image_url)
                        if len(images) >= num_images:
                            break
                if len(images) >= num_images:
                    break
        
        if images:
            return {
                "image_urls": images,
                "search_term": bird_name,
                "source": "Wikimedia Commons"
            }
        else:
            # Fallback if no images found
            return {
                "image_urls": [],
                "search_term": bird_name,
                "source": "Wikimedia Commons"
            }
    except Exception as e:
        print(f"Error fetching images: {e}")
        return {
            "image_urls": [],
            "search_term": bird_name,
            "source": "Wikimedia Commons"
        }


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
    print(f"\n[Quiz Question] Showing bird: {correct_bird}")
    
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
