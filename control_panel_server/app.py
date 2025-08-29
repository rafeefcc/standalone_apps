from flask import Flask, render_template, request, jsonify, Response
import subprocess
import json
import os
import csv
import time
import psycopg2
from psycopg2 import Error
from googlemaps import Client as GoogleMapsClient
from datetime import datetime
from fuzzywuzzy import fuzz

app = Flask(__name__)

# Mapping for source display names to filter values
SOURCE_FILTER_MAP = {
    'Google Maps API': 'gmaps_api',
    'Google Maps Headless': 'gmaps_headless',
    'Facebook Comments': 'facebook_comments',
    'Facebook Posts': 'facebook_posts',
    'Wikipedia': 'wikipedia'
}

app.config['JSONIFY_AS_ASCII'] = False # To display non-ASCII characters directly in JSON

# --- CONFIGURATION ---
# PASTE YOUR GOOGLE MAPS API KEY HERE
API_KEY = "AIzaSyBTcOc4xa3qwsmzY189fHt7cfiWE5TugNc"

# PostgreSQL Configuration
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": "5432",
    "database": "scrape_details",
    "user": "scrape_bot",
    "password": "Viewsonic2574"
}
# ---

# Initialize Google Maps Client
gmaps = GoogleMapsClient(key=API_KEY)

# --- Database Functions ---
def get_db_connection():
    connection = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        return None

def create_tables():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            print("Attempting to create/check database tables...")

            # Drop tables if they exist (for purging functionality)
            cursor.execute("DROP TABLE IF EXISTS gmaps_api_leads CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS gmaps_headless_leads CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS facebook_comments CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS facebook_search_posts CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS wikipedia_results CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS search_queries CASCADE;")
            print("Existing tables dropped if they existed.")

            # New Search Queries Table
            cursor.execute("""
                CREATE TABLE search_queries (
                    id SERIAL PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table search_queries created.")

            # Google Maps API Scraper Table
            cursor.execute("""
                CREATE TABLE gmaps_api_leads (
                    id SERIAL PRIMARY KEY,
                    query_id INTEGER REFERENCES search_queries(id),
                    name VARCHAR(255),
                    address TEXT,
                    rating NUMERIC(2,1),
                    total_ratings INTEGER,
                    phone_number VARCHAR(50),
                    email VARCHAR(255),
                    url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table gmaps_api_leads created.")

            # Headless Google Maps Scraper Table
            cursor.execute("""
                CREATE TABLE gmaps_headless_leads (
                    id SERIAL PRIMARY KEY,
                    query_id INTEGER REFERENCES search_queries(id),
                    title VARCHAR(255),
                    rating NUMERIC(2,1),
                    review_count INTEGER,
                    href TEXT,
                    phone_number VARCHAR(50),
                    email VARCHAR(255),
                    url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table gmaps_headless_leads created.")

            # Facebook Comments Table
            cursor.execute("""
                CREATE TABLE facebook_comments (
                    id SERIAL PRIMARY KEY,
                    query_id INTEGER REFERENCES search_queries(id),
                    user_name VARCHAR(255),
                    user_profile_url TEXT,
                    comment TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table facebook_comments created.")

            # Facebook Search Posts Table
            cursor.execute("""
                CREATE TABLE facebook_search_posts (
                    id SERIAL PRIMARY KEY,
                    query_id INTEGER REFERENCES search_queries(id),
                    post_content TEXT,
                    post_url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table facebook_search_posts created.")

            # Wikipedia Test Table
            cursor.execute("""
                CREATE TABLE wikipedia_results (
                    id SERIAL PRIMARY KEY,
                    query_id INTEGER REFERENCES search_queries(id),
                    title TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table wikipedia_results created.")
            connection.commit()
            print("Database tables created successfully.")
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            if connection:
                cursor.close()
                connection.close()

def insert_search_query(query_text):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO search_queries (query_text)
                VALUES (%s) RETURNING id;
            """, (query_text,))
            query_id = cursor.fetchone()[0]
            connection.commit()
            return query_id
        except Error as e:
            print(f"Error inserting search query: {e}")
            return None
        finally:
            if connection:
                cursor.close()
                connection.close()

def insert_gmaps_api_lead(query_id, name, address, rating, total_ratings, phone_number, email, url):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO gmaps_api_leads (query_id, name, address, rating, total_ratings, phone_number, email, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (query_id, name, address, rating, total_ratings, phone_number, email, url))
            connection.commit()
            return True
        except Error as e:
            print(f"Error inserting Google Maps API lead: {e}")
            return False
        finally:
            if connection:
                cursor.close()
                connection.close()

def insert_gmaps_headless_lead(query_id, title, rating, review_count, href, phone_number, email, url):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO gmaps_headless_leads (query_id, title, rating, review_count, href, phone_number, email, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (query_id, title, rating, review_count, href, phone_number, email, url))
            connection.commit()
            return True
        except Error as e:
            print(f"Error inserting Google Maps headless lead: {e}")
            return False
        finally:
            if connection:
                cursor.close()
                connection.close()

def insert_facebook_comment(query_id, user_name, user_profile_url, comment):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO facebook_comments (query_id, user_name, user_profile_url, comment)
                VALUES (%s, %s, %s, %s);
            """, (query_id, user_name, user_profile_url, comment))
            connection.commit()
            return True
        except Error as e:
            print(f"Error inserting Facebook comment: {e}")
            return False
        finally:
            if connection:
                cursor.close()
                connection.close()

def insert_facebook_search_post(query_id, post_content, post_url):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO facebook_search_posts (query_id, post_content, post_url)
                VALUES (%s, %s, %s);
            """, (query_id, post_content, post_url))
            connection.commit()
            return True
        except Error as e:
            print(f"Error inserting Facebook search post: {e}")
            return False
        finally:
            if connection:
                cursor.close()
                connection.close()

def insert_wikipedia_result(query_id, title):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO wikipedia_results (query_id, title)
                VALUES (%s, %s);
            """, (query_id, title))
            connection.commit()
            return True
        except Error as e:
            print(f"Error inserting Wikipedia result: {e}")
            return False
        finally:
            if connection:
                cursor.close()
                connection.close()

# --- End Database Functions ---

@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')

# --- Google Maps API Scraper ---
@app.route('/scrape/api', methods=['POST'])
def scrape_api():
    """Endpoint to trigger scraping with the Google Maps API."""
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({'error': 'Query is required'}), 400
    if API_KEY == "YOUR_API_KEY_HERE":
        return jsonify({'error': 'API key is not set in the server.'}), 500

    # Combine query parameters for search_queries table
    query_text = f"Google Maps API: {query}"
    query_id = insert_search_query(query_text)
    if query_id is None:
        return jsonify({'error': 'Failed to record search query'}), 500

    try:
        places = gmaps.places(query=query)
        all_results = places.get('results', [])
        next_page_token = places.get('next_page_token')

        while next_page_token:
            time.sleep(2)
            places = gmaps.places(query=query, page_token=next_page_token)
            all_results.extend(places.get('results', []))
            next_page_token = places.get('next_page_token')

        if not all_results:
            return jsonify({'message': 'No results found.'})

        # Insert into PSQL
        inserted_count = 0
        for place in all_results:
            if insert_gmaps_api_lead(
                query_id, # Pass query_id
                place.get('name'),
                place.get('formatted_address'),
                place.get('rating'),
                place.get('user_ratings_total'),
                place.get('formatted_phone_number'), # Pass phone number
                None, # Pass None for email
                place.get('website') # Pass website as url
            ):
                inserted_count += 1

        return jsonify({'message': f'Success! {inserted_count} Google Maps API results inserted into PSQL.'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
# --- End Google Maps API Scraper ---


# --- Headless Google Maps Scraper ---
@app.route('/scrape/headless', methods=['POST'])
def scrape_headless():
    """Endpoint to trigger scraping with the headless browser script."""
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    # Combine query parameters for search_queries table
    query_text = f"Google Maps Headless: {query}"
    query_id = insert_search_query(query_text)
    if query_id is None:
        return jsonify({'error': 'Failed to record search query'}), 500

    try:
        scraper_path = os.path.join(os.path.dirname(__file__), '..', 'headless_scraper', 'scraper.js')
        scraper_dir = os.path.dirname(scraper_path)
        csv_filename = os.path.join(scraper_dir, 'headless_leads.csv')

        # Ensure the CSV file does not exist from a previous run
        if os.path.exists(csv_filename):
            os.remove(csv_filename)

        process = subprocess.Popen(
            ['node', scraper_path, query],
            cwd=scraper_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate()

        # Print stdout and stderr for debugging
        print(f"Headless Scraper STDOUT:\n{stdout}")
        print(f"Headless Scraper STDERR:\n{stderr}")

        if process.returncode != 0:
            return jsonify({'error': 'Headless scraper failed', 'details': stderr}), 500

        inserted_count = 0
        if os.path.exists(csv_filename):
            with open(csv_filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader) # Skip header row
                for row in reader:
                    # Assuming CSV format: title, rating, review_count, href, phoneNumber
                    if len(row) >= 5: # Now expecting 5 columns
                        title = row[0]
                        rating = float(row[1]) if row[1] else None
                        review_count = int(row[2]) if row[2] else 0
                        href = row[3]
                        phone_number = row[4] if row[4] else None # New: phone_number
                        email = None # Pass None for email
                        if insert_gmaps_headless_lead(query_id, title, rating, review_count, href, phone_number, email): # Pass query_id, phone_number and email
                            inserted_count += 1
            os.remove(csv_filename) # Clean up the CSV file

        return jsonify({'message': f'Success! {inserted_count} Headless Google Maps results inserted into PSQL.'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
# --- End Headless Google Maps Scraper ---


# --- Facebook Scraper (Live Log) ---
@app.route('/scrape/facebook') # Changed to GET for EventSource
def scrape_facebook():
    """Endpoint to trigger and stream logs from the Facebook scraper script."""
    post_url = request.args.get('url')
    email = request.args.get('email', '')
    password = request.args.get('password', '')

    if not post_url:
        return Response("Error: Post URL is required", status=400)

    # Combine query parameters for search_queries table
    query_text = f"Facebook: URL={post_url}, Email={email}"
    query_id = insert_search_query(query_text)
    if query_id is None:
        yield "data: SERVER ERROR: Failed to record search query\n\n"
        yield "event: close\ndata: Connection closed\n\n"
        return

    def generate_logs():
        csv_filename = None
        try:
            scraper_path = os.path.join(os.path.dirname(__file__), '..', 'facebook_scraper', 'scraper.js')
            scraper_dir = os.path.dirname(scraper_path)
            
            command = ['node', scraper_path, post_url, email, password]
            
            yield "data: Starting Facebook scraper...\n\n"
            
            process = subprocess.Popen(
                command,
                cwd=scraper_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Combine stdout and stderr
                text=True,
                bufsize=1 # Line-buffered
            )

            # Stream output line by line and capture last line for CSV path
            last_line = ""
            for line in iter(process.stdout.readline, ''):
                yield f"data: {line.strip()}\n\n"
                last_line = line.strip()
            
            process.stdout.close()
            return_code = process.wait()

            # Extract CSV filename from last line of output
            if "Successfully saved data to facebook_leads.csv" in last_line:
                csv_filename = 'facebook_leads.csv'
            elif "Successfully saved search results to facebook_search_leads.csv" in last_line:
                csv_filename = 'facebook_search_leads.csv'

            if return_code == 0:
                yield "data: \n--- SCRIPT FINISHED SUCCESSFULLY ---\n\n"
                # Insert into PSQL if CSV was generated
                if csv_filename and os.path.exists(os.path.join(scraper_dir, csv_filename)):
                    yield f"data: Inserting data from {csv_filename} into PSQL...\n\n"
                    inserted_count = 0
                    with open(os.path.join(scraper_dir, csv_filename), 'r', newline='', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        header = next(reader) # Skip header
                        for row in reader:
                            if csv_filename == 'facebook_leads.csv':
                                if len(row) >= 3: # user_name, user_profile_url, comment
                                    if insert_facebook_comment(query_id, row[0], row[1], row[2]): # Pass query_id
                                        inserted_count += 1
                            elif csv_filename == 'facebook_search_leads.csv':
                                if len(row) >= 2: # post_content, post_url
                                    if insert_facebook_search_post(query_id, row[0], row[1]): # Pass query_id
                                        inserted_count += 1
                    os.remove(os.path.join(scraper_dir, csv_filename)) # Clean up CSV
                    yield f"data: Successfully inserted {inserted_count} records into PSQL.\n\n"
                else:
                    yield "data: No CSV file generated or found for PSQL insertion.\n\n"
            else:
                yield f"data: \n--- SCRIPT FAILED (Exit Code: {return_code}) ---\n\n"

        except Exception as e:
            yield f"data: SERVER ERROR: {str(e)}\n\n"
        
        yield "event: close\ndata: Connection closed\n\n"

    return Response(generate_logs(), mimetype='text/event-stream')
# --- End Facebook Scraper ---


# --- Wikipedia Test Scraper (Live Log) ---
@app.route('/scrape/test')
def scrape_test():
    """Endpoint to trigger and stream logs from the test scraper script."""
    query = request.args.get('query')

    if not query:
        return Response("Error: Search query is required", status=400)

    # Combine query parameters for search_queries table
    query_text = f"Wikipedia Test: {query}"
    query_id = insert_search_query(query_text)
    if query_id is None:
        yield "data: SERVER ERROR: Failed to record search query\n\n"
        yield "event: close\ndata: Connection closed\n\n"
        return

    def generate_logs():
        csv_filename = None
        try:
            scraper_path = os.path.join(os.path.dirname(__file__), '..', 'test_scraper.js')
            scraper_dir = os.path.dirname(scraper_path)

            command = ['node', scraper_path, query]
            
            yield "data: Starting Wikipedia test scraper...\n\n"
            
            process = subprocess.Popen(
                command,
                cwd=scraper_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            last_line = ""
            for line in iter(process.stdout.readline, ''):
                yield f"data: {line.strip()}\n\n"
                last_line = line.strip()
            
            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                yield "data: \n--- SCRIPT FINISHED SUCCESSFULLY ---\n\n"
                # Assuming test_scraper.js prints a success message with CSV path if it saves one
                if "Successfully saved data to" in last_line and last_line.endswith(".csv"):
                    # This part is not implemented in test_scraper.js yet, but for future proofing
                    # we would extract the filename and insert into PSQL here.
                    yield "data: Test scraper does not save CSVs for PSQL insertion.\n\n"
                else:
                    insert_wikipedia_result(query_id, f"Test Result for {query}")
                    yield "data: Test scraper does not save CSVs for PSQL insertion, but a dummy result was recorded.\n\n"
            else:
                yield f"data: \n--- SCRIPT FAILED (Exit Code: {return_code}) ---\n\n"

        except Exception as e:
            yield f"data: SERVER ERROR: {str(e)}\n\n"
        
        yield "event: close\ndata: Connection closed\n\n"

    return Response(generate_logs(), mimetype='text/event-stream')
# --- End Wikipedia Test Scraper ---

# --- Results Page Endpoint (HTML) ---
@app.route('/results')
def results_page():
    return render_template('results.html')

# --- Results API Endpoint (JSON) ---
@app.route('/api/results')
def api_results():
    business_type_filter = request.args.get('business_type', '').strip()
    address_filter = request.args.get('address', '').strip()
    search_term_filter = request.args.get('search_term', '').strip() # New search term filter
    source_filter = request.args.get('source', '').strip()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size

    all_results = []
    total_count = 0
    connection = None

    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = connection.cursor()

        all_raw_results = []

        all_raw_results = []

        # Fetch all search queries for fuzzy matching
        search_queries_map = {}
        cursor.execute("SELECT id, query_text FROM search_queries;")
        for q_id, q_text in cursor.fetchall():
            # Extract the actual query part for better fuzzy matching
            extracted_query = q_text
            if q_text.startswith("Google Maps API: "):
                extracted_query = q_text.replace("Google Maps API: ", "")
            elif q_text.startswith("Google Maps Headless: "):
                extracted_query = q_text.replace("Google Maps Headless: ", "")
            elif q_text.startswith("Facebook: URL="):
                # For Facebook, we might want to match against URL or email, or both
                # For simplicity, let's just use the whole string for now, or refine later
                pass # Keep as is for now, or extract more specifically if needed
            elif q_text.startswith("Wikipedia Test: "):
                extracted_query = q_text.replace("Wikipedia Test: ", "")
            search_queries_map[q_id] = extracted_query

        # --- Google Maps API Leads ---
        cursor.execute("""
            SELECT query_id, name, address, rating::text as rating, scraped_at, 'Google Maps API' as source_display, phone_number, url, email
            FROM gmaps_api_leads
        """)
        for row in cursor.fetchall():
            all_raw_results.append({
                "query_id": row[0],
                "source_display": row[5],
                "name_title": row[1],
                "address_content": row[2],
                "rating": row[3],
                "scraped_at": row[4].isoformat(),
                "phone_number": row[6],
                "url": row[7],
                "email": row[8]
            })

        # --- Google Maps Headless Leads ---
        cursor.execute("""
            SELECT query_id, title, NULL as address, rating::text as rating, href, scraped_at, 'Google Maps Headless' as source_display, phone_number, email
            FROM gmaps_headless_leads
        """)
        for row in cursor.fetchall():
            all_raw_results.append({
                "query_id": row[0],
                "source_display": row[6],
                "name_title": row[1],
                "address_content": row[2], # This will be NULL again
                "rating": row[3],
                "url": row[4],
                "scraped_at": row[5].isoformat(),
                "phone_number": row[7],
                "email": row[8]
            })

        # --- Facebook Comments ---
        cursor.execute("""
            SELECT query_id, user_name, comment, user_profile_url, scraped_at, 'Facebook Comments' as source_display, NULL as phone_number, NULL as rating, NULL as email
            FROM facebook_comments
        """)
        for row in cursor.fetchall():
            all_raw_results.append({
                "query_id": row[0],
                "source_display": row[5],
                "name_title": row[1],
                "address_content": row[2],
                "url": row[3],
                "scraped_at": row[4].isoformat(),
                "phone_number": row[6],
                "rating": row[7],
                "email": row[8]
            })

        # --- Facebook Search Posts ---
        cursor.execute("""
            SELECT query_id, post_content, post_url, scraped_at, 'Facebook Posts' as source_display, NULL as phone_number, NULL as rating, NULL as address, NULL as email
            FROM facebook_search_posts
        """)
        for row in cursor.fetchall():
            all_raw_results.append({
                "query_id": row[0],
                "source_display": row[4],
                "name_title": row[1],
                "address_content": row[7],
                "url": row[2],
                "scraped_at": row[3].isoformat(),
                "phone_number": row[5],
                "rating": row[6],
                "email": row[8]
            })

        # --- Wikipedia Results ---
        cursor.execute("""
            SELECT query_id, title, scraped_at, 'Wikipedia' as source_display, NULL as phone_number, NULL as rating, NULL as address, NULL as url, NULL as email
            FROM wikipedia_results
        """)
        for row in cursor.fetchall():
            all_raw_results.append({
                "query_id": row[0],
                "source_display": row[3],
                "name_title": row[1],
                "address_content": row[6],
                "rating": row[5],
                "url": row[7],
                "scraped_at": row[2].isoformat(),
                "phone_number": row[4],
                "email": row[8]
            })

        # Apply search term filter first
        if search_term_filter:
            matching_query_ids = set()
            for q_id, stored_query_text in search_queries_map.items():
                if fuzz.ratio(search_term_filter.lower(), stored_query_text.lower()) >= 30:
                    matching_query_ids.add(q_id)
            all_results = [item for item in all_raw_results if item.get('query_id') in matching_query_ids]
        else:
            all_results = all_raw_results

        # Apply source filter
        if source_filter:
            all_results = [item for item in all_results if SOURCE_FILTER_MAP.get(item["source_display"]) == source_filter]
        
        # Apply fuzzy filtering in Python
        if business_type_filter or address_filter:
            initial_results_count = len(all_results) # For debugging
            print(f"Applying fuzzy filter for business_type='{business_type_filter}', address='{address_filter}' to {initial_results_count} results.")
            
            current_filtered_results = all_results # Start with source-filtered results

            # Apply business_type_filter if present
            if business_type_filter:
                temp_results = []
                for item in current_filtered_results:
                    score_name = 0
                    if item.get('name_title'):
                        score_name = fuzz.ratio(business_type_filter.lower(), item['name_title'].lower())
                    if score_name >= 35:
                        temp_results.append(item)
                current_filtered_results = temp_results
            
            # Apply address_filter if present (to the already business_type-filtered results)
            if address_filter:
                temp_results = []
                for item in current_filtered_results:
                    score_address = 0
                    if item.get('address_content'):
                        score_address = fuzz.partial_ratio(address_filter.lower(), item['address_content'].lower())
                    if score_address >= 70: # Increased partial_ratio threshold for stricter address matching
                        temp_results.append(item)
                current_filtered_results = temp_results
            
            all_results = current_filtered_results
            print(f"Fuzzy filtering complete. {len(all_results)} results remaining.")

        total_count = len(all_results) # Calculate total_count after all filters

        # Sort all_results by scraped_at (newest first)
        all_results.sort(key=lambda x: x['scraped_at'], reverse=True)

        # Apply pagination
        paginated_results = all_results[offset:offset + page_size]

        return jsonify({
            "results": paginated_results,
            "total_count": total_count,
            "page": page,
            "page_size": page_size
        })

    except Error as e:
        print(f"Error fetching results: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/purge_database', methods=['POST'])
def purge_database():
    data = request.get_json()
    password = data.get('password')

    if password == DB_CONFIG["password"]:
        try:
            create_tables() # This will now drop and recreate all tables
            return jsonify({'message': 'Database purged and tables recreated successfully.'}), 200
        except Exception as e:
            print(f"Error during database purge: {e}")
            return jsonify({'error': f'Failed to purge database: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Incorrect password.'}), 401


if __name__ == '__main__':
    # Create the templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create database tables on startup
    create_tables()

    app.run(host='0.0.0.0', debug=True, port=8005)