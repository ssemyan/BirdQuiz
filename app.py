from flask import Flask, render_template, request, jsonify
import csv
import random
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import requests

load_dotenv()

app = Flask(__name__)

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
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None or 'Common Name' not in reader.fieldnames:
                return None
            birds = [row['Common Name'].strip() for row in reader if row['Common Name'].strip()]
        # Remove duplicates while preserving order
        bird_list = list(dict.fromkeys(birds))
        return bird_list
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
        print(f"  - Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"  - Deployment: {DEPLOYMENT_NAME}")
        return []


def fetch_bird_images(bird_name, num_images=3):
    """Fetch bird images from Wikimedia Commons."""
    empty_result = {
        "image_urls": [],
        "search_term": bird_name,
        "source": "Wikimedia Commons"
    }
    try:
        headers = {
            'User-Agent': 'BirdIdentificationQuiz/1.0 (Student project)'
        }
        
        # Query Wikimedia Commons API for bird images
        wiki_params = {
            'action': 'query',
            'list': 'search',
            'srsearch': bird_name,
            'format': 'json',
            'srnamespace': '6',  # File namespace
            'srlimit': 20
        }
        
        response = requests.get('https://commons.wikimedia.org/w/api.php', params=wiki_params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        search_results = data.get('query', {}).get('search', [])
        if not search_results:
            return empty_result
        
        # Filter to image files only
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
        file_titles = [
            item['title'] for item in search_results
            if any(item['title'].lower().endswith(ext) for ext in image_extensions)
        ]
        
        if not file_titles:
            return empty_result
        
        # Batch request: get URLs for all matching files at once
        file_params = {
            'action': 'query',
            'titles': '|'.join(file_titles),
            'prop': 'imageinfo',
            'iiprop': 'url',
            'format': 'json'
        }
        file_response = requests.get('https://commons.wikimedia.org/w/api.php', params=file_params, headers=headers, timeout=5)
        file_response.raise_for_status()
        file_data = file_response.json()
        
        images = []
        for page_info in file_data.get('query', {}).get('pages', {}).values():
            if 'imageinfo' in page_info:
                image_url = page_info['imageinfo'][0]['url']
                if image_url and 'upload.wikimedia.org' in image_url:
                    images.append(image_url)
        
        if not images:
            return empty_result
        
        selected_images = random.sample(images, min(num_images, len(images)))
        return {
            "image_urls": selected_images,
            "search_term": bird_name,
            "source": "Wikimedia Commons"
        }
    except Exception as e:
        print(f"Error fetching images: {e}")
        return empty_result


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


@app.route('/api/load-csv-data', methods=['POST'])
def load_csv_data():
    """Load birds from a pasted list of names, one per line."""
    data = request.json
    bird_names = data.get('bird_names', '')
    
    if not bird_names.strip():
        return jsonify({'success': False, 'error': 'No bird names provided'}), 400
    
    global bird_list
    try:
        birds = [name.strip() for name in bird_names.splitlines() if name.strip()]
        bird_list = list(dict.fromkeys(birds))
        if not bird_list:
            return jsonify({'success': False, 'error': 'No bird names found in the list'}), 400
        return jsonify({'success': True, 'count': len(bird_list)})
    except Exception as e:
        print(f"Error parsing bird list: {e}")
        return jsonify({'success': False, 'error': 'Failed to parse bird list'}), 400


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


if __name__ == '__main__':
    # Load default bird list
    if os.path.exists('ebird_world_year_list.csv'):
        load_birds_from_csv('ebird_world_year_list.csv')
    
    app.run(debug=True, port=5000)
