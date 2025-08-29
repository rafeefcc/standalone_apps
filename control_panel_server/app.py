from flask import Flask, request, jsonify, Response, session, send_from_directory, redirect, url_for
import subprocess

import json
import csv
import time
import psycopg2
from psycopg2 import Error
from googlemaps import Client as GoogleMapsClient
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
import ui
import os
import uuid
import openpyxl
from io import BytesIO


app = Flask(__name__)
app.secret_key = os.urandom(24) # Add a secret key for session management
app.permanent_session_lifetime = timedelta(days=7)

# --- Session Management ---
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.before_request
def ensure_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
# --- End Session Management ---

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

def initialize_database():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            print("Attempting to create/check database tables...")

            # New Search Queries Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_queries (
                    id SERIAL PRIMARY KEY,
                    query_text TEXT NOT NULL,
                    session_id VARCHAR(36) NOT NULL,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table search_queries checked/created.")

            # Google Maps API Scraper Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gmaps_api_leads (
                    id SERIAL PRIMARY KEY,
                    query_id INTEGER REFERENCES search_queries(id),
                    name VARCHAR(255),
                    address TEXT,
                    rating NUMERIC(2,1),
                    total_ratings INTEGER,
                    phone_number VARCHAR(50),
                    url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table gmaps_api_leads checked/created.")

            # Headless Google Maps Scraper Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gmaps_headless_leads (
                    id SERIAL PRIMARY KEY,
                    query_id INTEGER REFERENCES search_queries(id),
                    title VARCHAR(255),
                    rating NUMERIC(2,1),
                    review_count INTEGER,
                    href TEXT,
                    phone_number VARCHAR(50),
                    url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table gmaps_headless_leads checked/created.")

            # Facebook Comments Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facebook_comments (
                    id SERIAL PRIMARY KEY,
                    query_id INTEGER REFERENCES search_queries(id),
                    user_name VARCHAR(255),
                    user_profile_url TEXT,
                    comment TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table facebook_comments checked/created.")

            # Facebook Search Posts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facebook_search_posts (
                    id SERIAL PRIMARY KEY,
                    query_id INTEGER REFERENCES search_queries(id),
                    post_content TEXT,
                    post_url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table facebook_search_posts checked/created.")

            # Wikipedia Test Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wikipedia_results (
                    id SERIAL PRIMARY KEY,
                    query_id INTEGER REFERENCES search_queries(id),
                    title TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table wikipedia_results checked/created.")

            # Visitor Tracking Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS visitor_tracking (
                    id SERIAL PRIMARY KEY,
                    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table visitor_tracking checked/created.")

            # Email Downloads Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_downloads (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) NOT NULL,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("Table email_downloads checked/created.")
            connection.commit()
            print("Database tables checked/created successfully.")
        except Error as e:
            print(f"Error creating tables: {e}")
        finally:
            if connection:
                cursor.close()
                connection.close()

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
                    session_id VARCHAR(36) NOT NULL,
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

def insert_search_query(query_text, session_id):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO search_queries (query_text, session_id)
                VALUES (%s, %s) RETURNING id;
            """, (query_text, session_id))
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

def insert_gmaps_api_lead(query_id, name, address, rating, total_ratings, phone_number, url):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO gmaps_api_leads (query_id, name, address, rating, total_ratings, phone_number, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (query_id, name, address, rating, total_ratings, phone_number, url))
            connection.commit()
            return True
        except Error as e:
            print(f"Error inserting Google Maps API lead: {e}")
            return False
        finally:
            if connection:
                cursor.close()
                connection.close()

def insert_gmaps_headless_lead(query_id, title, rating, review_count, href, phone_number, url):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO gmaps_headless_leads (query_id, title, rating, review_count, href, phone_number, url)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (query_id, title, rating, review_count, href, phone_number, url))
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

def log_visitor():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO visitor_tracking (visited_at) VALUES (CURRENT_TIMESTAMP);")
            connection.commit()
        except Error as e:
            print(f"Error logging visitor: {e}")
        finally:
            if connection:
                cursor.close()
                connection.close()

def get_total_visitors():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM visitor_tracking;")
            count = cursor.fetchone()[0]
            return count
        except Error as e:
            print(f"Error getting total visitors: {e}")
            return 0
        finally:
            if connection:
                cursor.close()
                connection.close()
    return 0

def get_today_visitors():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM visitor_tracking WHERE visited_at >= CURRENT_DATE;")
            count = cursor.fetchone()[0]
            return count
        except Error as e:
            print(f"Error getting today's visitors: {e}")
            return 0
        finally:
            if connection:
                cursor.close()
                connection.close()
    return 0

def get_last_hour_visitors():
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            one_hour_ago = datetime.now() - timedelta(hours=1)
            cursor.execute("SELECT COUNT(*) FROM visitor_tracking WHERE visited_at >= %s;", (one_hour_ago,))
            count = cursor.fetchone()[0]
            return count
        except Error as e:
            print(f"Error getting last hour's visitors: {e}")
            return 0
        finally:
            if connection:
                cursor.close()
                connection.close()
    return 0

def insert_email_download(email):
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO email_downloads (email)
                VALUES (%s);
            """, (email,))
            connection.commit()
            return True
        except Error as e:
            print(f"Error inserting email download: {e}")
            return False
        finally:
            if connection:
                cursor.close()
                connection.close()

# --- End Database Functions ---

@app.route('/')
def index():
    """Serve the main HTML page."""
    log_visitor()
    return ui.render_index_page()

@app.route('/api/visitors')
def api_visitors():
    total = get_total_visitors()
    today = get_today_visitors()
    last_hour = get_last_hour_visitors()
    return jsonify({
        "total": total,
        "today": today,
        "last_hour": last_hour
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    return send_from_directory('.', filename)


# --- Google Maps API Scraper ---
@app.route('/scrape/api') # Changed to GET for EventSource
def scrape_api():
    """Endpoint to trigger and stream logs from the Google Maps API scraper."""
    query = request.args.get('query')
    session_id = session.get('session_id') # Get session_id in context

    if not query:
        return Response("Error: Query is required", status=400)
    if API_KEY == "YOUR_API_KEY_HERE":
        return Response("Error: API key is not set in the server.", status=500)

    def generate_logs(sid): # Pass session_id as an argument
        yield "data: Starting Google Maps API scraper...\n\n"
        
        # Combine query parameters for search_queries table
        query_text = f"Google Maps API: {query}"
        query_id = insert_search_query(query_text, sid) # Use the passed sid
        if query_id is None:
            yield "data: SERVER ERROR: Failed to record search query\n\n"
            yield "event: close\ndata: Connection closed\n\n"
            return

        try:
            yield f"data: Searching for '{query}' using Google Maps API...\n\n"
            places = gmaps.places(query=query)
            all_results = places.get('results', [])
            next_page_token = places.get('next_page_token')
            yield f"data: Found {len(all_results)} initial results.\n\n"

            page_count = 1
            while next_page_token:
                page_count += 1
                yield f"data: Fetching page {page_count}...\n\n"
                time.sleep(2)
                places = gmaps.places(query=query, page_token=next_page_token)
                all_results.extend(places.get('results', []))
                next_page_token = places.get('next_page_token')
                yield f"data: Found {len(places.get('results', []))} more results. Total: {len(all_results)}\n\n"

            if not all_results:
                yield "data: No results found.\n\n"
                yield "event: close\ndata: Connection closed\n\n"
                return

            yield f"data: Total of {len(all_results)} results found. Inserting into database...\n\n"
            
            # Insert into PSQL
            inserted_count = 0
            for i, place in enumerate(all_results[:50]): # Limit to 50 results
                place_id = place.get('place_id')
                phone_number = None
                if place_id:
                    try:
                        details = gmaps.place(place_id=place_id, fields=['formatted_phone_number'])
                        phone_number = details.get('result', {}).get('formatted_phone_number')
                    except Exception as e:
                        yield f"data: Error fetching details for place_id {place_id}: {e}\n\n"

                if insert_gmaps_api_lead(
                    query_id,
                    place.get('name'),
                    place.get('formatted_address'),
                    place.get('rating'),
                    place.get('user_ratings_total'),
                    phone_number,
                    place.get('website')
                ):
                    inserted_count += 1
                if (i + 1) % 10 == 0:
                    yield f"data: Inserted {inserted_count}/{len(all_results[:50])} records...\n\n"

            yield f"data: \n--- SCRIPT FINISHED SUCCESSFULLY ---\n\n"
            yield f"data: Success! {inserted_count} Google Maps API results inserted into PSQL.\n\n"

        except Exception as e:
            yield f"data: SERVER ERROR: {str(e)}\n\n"
        
        yield "event: close\ndata: Connection closed\n\n"

    return Response(generate_logs(session_id), mimetype='text/event-stream')

# --- End Google Maps API Scraper ---


# --- Headless Google Maps Scraper ---
@app.route('/scrape/headless') # Changed to GET for EventSource
def scrape_headless():
    """Endpoint to trigger and stream logs from the headless browser script."""
    query = request.args.get('query')

    if not query:
        return Response("Error: Query is required", status=400)

    def generate_logs():
        yield "data: Starting Headless Google Maps scraper...\n\n"
        
        # Combine query parameters for search_queries table
        query_text = f"Google Maps Headless: {query}"
        query_id = insert_search_query(query_text, session.get('session_id'))
        if query_id is None:
            yield "data: SERVER ERROR: Failed to record search query\n\n"
            yield "event: close\ndata: Connection closed\n\n"
            return

        try:
            scraper_path = os.path.join(os.path.dirname(__file__), '..', 'headless_scraper', 'scraper.js')
            scraper_dir = os.path.dirname(scraper_path)
            csv_filename = os.path.join(scraper_dir, 'headless_leads.csv')

            # Ensure the CSV file does not exist from a previous run
            if os.path.exists(csv_filename):
                os.remove(csv_filename)
                yield "data: Removed old CSV file.\n\n"

            command = ['node', scraper_path, query]
            
            process = subprocess.Popen(
                command,
                cwd=scraper_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Combine stdout and stderr
                text=True,
                bufsize=1 # Line-buffered
            )

            # Stream output line by line
            for line in iter(process.stdout.readline, ''):
                yield f"data: {line.strip()}\n\n"
            
            process.stdout.close()
            return_code = process.wait()

            if return_code != 0:
                yield f"data: \n--- SCRIPT FAILED (Exit Code: {return_code}) ---\n\n"
            else:
                yield "data: \n--- SCRIPT FINISHED SUCCESSFULLY ---\n\n"
                inserted_count = 0
                if os.path.exists(csv_filename):
                    yield "data: CSV file found. Inserting data into PSQL...\n\n"
                    with open(csv_filename, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        header = next(reader) # Skip header row
                        for row in reader:
                            if len(row) >= 5:
                                title, rating_str, review_count_str, href, phone_number = row[:5]
                                rating = float(rating_str) if rating_str else None
                                review_count = int(review_count_str) if review_count_str else 0
                                if insert_gmaps_headless_lead(query_id, title, rating, review_count, href, phone_number, None):
                                    inserted_count += 1
                    os.remove(csv_filename) # Clean up the CSV file
                    yield f"data: Successfully inserted {inserted_count} records into PSQL.\n\n"
                else:
                    yield "data: No CSV file generated or found for PSQL insertion.\n\n"

        except Exception as e:
            yield f"data: SERVER ERROR: {str(e)}\n\n"
        
        yield "event: close\ndata: Connection closed\n\n"

    return Response(generate_logs(), mimetype='text/event-stream')
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
    query_id = insert_search_query(query_text, session.get('session_id'))
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
    query_id = insert_search_query(query_text, session.get('session_id'))
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
    return ui.render_results_page()

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

        # Get current session ID
        current_session_id = session.get('session_id')
        if not current_session_id:
            return jsonify({"results": [], "total_count": 0, "page": page, "page_size": page_size})

        # Fetch all search queries for the current session for fuzzy matching
        search_queries_map = {}
        cursor.execute("SELECT id, query_text FROM search_queries WHERE session_id = %s;", (current_session_id,))
        session_query_ids = []
        for q_id, q_text in cursor.fetchall():
            session_query_ids.append(q_id)
            # Extract the actual query part for better fuzzy matching
            extracted_query = q_text
            if q_text.startswith("Google Maps API: "):
                extracted_query = q_text.replace("Google Maps API: ", "")
            elif q_text.startswith("Google Maps Headless: "):
                extracted_query = q_text.replace("Google Maps Headless: ", "")
            elif q_text.startswith("Facebook: URL="):
                pass # Keep as is for now
            elif q_text.startswith("Wikipedia Test: "):
                extracted_query = q_text.replace("Wikipedia Test: ", "")
            search_queries_map[q_id] = extracted_query
        
        if not session_query_ids:
            return jsonify({"results": [], "total_count": 0, "page": page, "page_size": page_size})

        # --- Google Maps API Leads ---
        cursor.execute("""
            SELECT query_id, name, address, rating::text as rating, scraped_at, 'Google Maps API' as source_display, phone_number, url
            FROM gmaps_api_leads WHERE query_id = ANY(%s)
        """, (session_query_ids,))
        for row in cursor.fetchall():
            all_raw_results.append({
                "query_id": row[0],
                "source_display": row[5],
                "name_title": row[1],
                "address_content": row[2],
                "rating": row[3],
                "scraped_at": row[4].isoformat(),
                "phone_number": row[6],
                "url": row[7]
            })

        # --- Google Maps Headless Leads ---
        cursor.execute("""
            SELECT query_id, title, NULL as address, rating::text as rating, href, scraped_at, 'Google Maps Headless' as source_display, phone_number, url
            FROM gmaps_headless_leads WHERE query_id = ANY(%s)
        """, (session_query_ids,))
        for row in cursor.fetchall():
            all_raw_results.append({
                "query_id": row[0],
                "source_display": row[6],
                "name_title": row[1],
                "address_content": row[2], # This will be NULL again
                "rating": row[3],
                "url": row[4],
                "scraped_at": row[5].isoformat(),
                "phone_number": row[7]
            })

        # --- Facebook Comments ---
        cursor.execute("""
            SELECT query_id, user_name, comment, user_profile_url, scraped_at, 'Facebook Comments' as source_display, NULL as phone_number, NULL as rating, NULL as email
            FROM facebook_comments WHERE query_id = ANY(%s)
        """, (session_query_ids,))
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
            FROM facebook_search_posts WHERE query_id = ANY(%s)
        """, (session_query_ids,))
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
            FROM wikipedia_results WHERE query_id = ANY(%s)
        """, (session_query_ids,))
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

@app.route('/download/xlsx')
def download_xlsx():
    """Endpoint to download results as an XLSX file."""
    email = request.args.get('email', '').strip()
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Log the email download
    insert_email_download(email)

    # Placeholder for sending email
    print(f"Received request to download XLSX for email: {email}")

    business_type_filter = request.args.get('business_type', '').strip()
    address_filter = request.args.get('address', '').strip()
    search_term_filter = request.args.get('search_term', '').strip()
    source_filter = request.args.get('source', '').strip()

    all_results = []
    connection = None

    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = connection.cursor()

        current_session_id = session.get('session_id')
        if not current_session_id:
            return jsonify({"error": "No session found"}), 400

        search_queries_map = {}
        cursor.execute("SELECT id, query_text FROM search_queries WHERE session_id = %s;", (current_session_id,))
        session_query_ids = [row[0] for row in cursor.fetchall()]
        
        if not session_query_ids:
            return jsonify({"error": "No results found for the current session"}), 404

        # Fetch all data without pagination
        # (This logic is duplicated from /api/results, consider refactoring in a real application)
        all_raw_results = []
        # --- Google Maps API Leads ---
        cursor.execute("""
            SELECT query_id, name, address, rating::text as rating, scraped_at, 'Google Maps API' as source_display, phone_number, url
            FROM gmaps_api_leads WHERE query_id = ANY(%s)
        """, (session_query_ids,))
        for row in cursor.fetchall():
            all_raw_results.append({
                "query_id": row[0], "source_display": row[5], "name_title": row[1], "address_content": row[2],
                "rating": row[3], "scraped_at": row[4].isoformat(), "phone_number": row[6], "url": row[7]
            })
        # ... (add other data sources similarly) ...

        # Apply filters
        # (This filtering logic is also duplicated, consider refactoring)
        if search_term_filter:
            # Simplified filtering for brevity
            pass
        if source_filter:
            all_raw_results = [item for item in all_raw_results if SOURCE_FILTER_MAP.get(item["source_display"]) == source_filter]

        # Create XLSX file
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Scraped Results"

        # Add headers
        headers = ["Source", "Name / Title", "Address / Content", "Rating", "Phone", "URL / Link", "Scraped At"]
        ws.append(headers)

        # Add data
        for item in all_raw_results:
            row = [
                item.get('source_display', 'N/A'),
                item.get('name_title', 'N/A'),
                item.get('address_content', 'N/A'),
                item.get('rating', 'N/A'),
                item.get('phone_number', 'N/A'),
                item.get('url', 'N/A'),
                item.get('scraped_at', 'N/A')
            ]
            ws.append(row)

        # Save to a BytesIO object
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return Response(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        headers={'Content-Disposition': 'attachment;filename=scraped_results.xlsx'})

    except Error as e:
        print(f"Error generating XLSX file: {e}")
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


@app.route('/admin')
def admin_panel():
    if not session.get('admin_logged_in'):
        return ui.render_admin_login_page()
    return ui.render_admin_page()

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    password = data.get('password')
    if password == DB_CONFIG["password"]:
        session['admin_logged_in'] = True
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False}), 401

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_panel'))

@app.route('/api/admin/stats/leads_by_scraper')
def get_leads_by_scraper():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    source_filter = request.args.get('source')

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        query = """
            SELECT source_display, COUNT(*) 
            FROM (
                SELECT 'Google Maps API' as source_display FROM gmaps_api_leads
                UNION ALL
                SELECT 'Google Maps Headless' as source_display FROM gmaps_headless_leads
                UNION ALL
                SELECT 'Facebook Comments' as source_display FROM facebook_comments
                UNION ALL
                SELECT 'Facebook Posts' as source_display FROM facebook_search_posts
                UNION ALL
                SELECT 'Wikipedia' as source_display FROM wikipedia_results
            ) as all_leads
        """
        if source_filter:
            query += f" WHERE source_display = '{source_filter}'"

        query += " GROUP BY source_display;"

        cursor.execute(query)
        results = cursor.fetchall()
        return jsonify(dict(results))
    except Error as e:
        print(f"Error fetching leads by scraper: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/admin/stats/lead_sources')
def get_lead_sources():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        query = """
            SELECT source_display, COUNT(*) 
            FROM (
                SELECT 'Google Maps API' as source_display FROM gmaps_api_leads
                UNION ALL
                SELECT 'Google Maps Headless' as source_display FROM gmaps_headless_leads
                UNION ALL
                SELECT 'Facebook Comments' as source_display FROM facebook_comments
                UNION ALL
                SELECT 'Facebook Posts' as source_display FROM facebook_search_posts
                UNION ALL
                SELECT 'Wikipedia' as source_display FROM wikipedia_results
            ) as all_leads
            GROUP BY source_display;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return jsonify(dict(results))
    except Error as e:
        print(f"Error fetching lead sources: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/admin/stats/visitors_over_time')
def get_visitors_over_time():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    source_filter = request.args.get('source')

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        query = """
            SELECT DATE(visited_at), COUNT(*) 
            FROM visitor_tracking
        """
        if source_filter:
            # This is a bit tricky, as we don't have a direct link between visitors and lead sources.
            # For now, I'll just filter by the date, and in the future, we can add a source to the visitor_tracking table.
            pass

        query += """
            WHERE visited_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(visited_at)
            ORDER BY DATE(visited_at);
        """
        cursor.execute(query)
        results = cursor.fetchall()
        # format results as a dictionary of date: count
        results_dict = {row[0].isoformat(): row[1] for row in results}
        return jsonify(results_dict)

    except Error as e:
        print(f"Error fetching visitors over time: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/admin/sql', methods=['POST'])
def run_sql_query():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    query = data.get('query')

    if not query or not query.strip().lower().startswith('select'):
        return jsonify({"error": "Only SELECT queries are allowed."}), 400

    # Extract table name from query
    import re
    match = re.search(r'from\s+([\w\d_]+)', query, re.IGNORECASE)
    table_name = match.group(1) if match else None

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return jsonify({"columns": columns, "rows": results, "table_name": table_name})
    except Error as e:
        print(f"Error executing SQL query: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/admin/stats/business_type_searches')
def get_business_type_searches():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT query_text FROM search_queries;")
        queries = [row[0] for row in cursor.fetchall()]

        # This is a simplified approach. A more robust solution would use NLP for entity extraction.
        business_types = {}
        for query in queries:
            # Example: "restaurants in New York" -> "restaurants"
            # This is a very basic way to extract business types and can be improved.
            business_type = query.split(' in ')[0]
            business_types[business_type] = business_types.get(business_type, 0) + 1

        return jsonify(business_types)

    except Error as e:
        print(f"Error fetching business type searches: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/admin/stats/search_intent_searches')
def get_search_intent_searches():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT query_text FROM search_queries;")
        queries = [row[0] for row in cursor.fetchall()]

        # Simplified intent extraction
        intents = {}
        for query in queries:
            if 'near me' in query:
                intent = query.replace(' near me', '')
                intents[intent] = intents.get(intent, 0) + 1
            else:
                intents['other'] = intents.get('other', 0) + 1

        return jsonify(intents)

    except Error as e:
        print(f"Error fetching search intent searches: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@app.route('/api/admin/stats/location_searches')
def get_location_searches():
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    connection = get_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT query_text FROM search_queries;")
        queries = [row[0] for row in cursor.fetchall()]

        # Simplified location extraction
        locations = {}
        for query in queries:
            if ' in ' in query:
                location = query.split(' in ')[1]
                locations[location] = locations.get(location, 0) + 1

        return jsonify(locations)

    except Error as e:
        print(f"Error fetching location searches: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    # Create database tables on startup
    initialize_database()

    app.run(host='0.0.0.0', debug=True, port=8005)