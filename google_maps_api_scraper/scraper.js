const { Client } = require('@googlemaps/google-maps-services-js');
const { Parser } = require('json2csv');
const fs = require('fs');

// --- CONFIGURATION ---
// 1. PASTE YOUR GOOGLE MAPS API KEY HERE
const API_KEY = 'YOUR_API_KEY_HERE';

// 2. DEFINE YOUR SEARCH QUERY
const searchQuery = {
  query: 'restaurants in New York', // e.g., "plumbers in London", "cafes in Paris"
};

// 3. DEFINE YOUR OUTPUT FILENAME
const outputFilename = 'leads.csv';
// ---

const client = new Client({});

// Function to sleep for a given time in milliseconds
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function fetchAllPages(query) {
  let allResults = [];
  let nextPageToken = null;

  do {
    try {
      const response = await client.textSearch({
        params: {
          query: query.query,
          key: API_KEY,
          pagetoken: nextPageToken,
        },
        timeout: 5000, // timeout in milliseconds
      });

      allResults = allResults.concat(response.data.results);
      nextPageToken = response.data.next_page_token;

      if (nextPageToken) {
        console.log('Fetching next page...');
        // Google requires a short delay before the next page token becomes valid.
        await sleep(2000);
      }
    } catch (error) {
      console.error(
        'An error occurred:',
        error.response ? error.response.data : error.message,
      );
      nextPageToken = null; // Stop pagination on error
    }
  } while (nextPageToken);

  return allResults;
}

async function main() {
  if (API_KEY === 'YOUR_API_KEY_HERE') {
    console.error(
      'Please enter your Google Maps API key in the scraper.js file.',
    );
    return;
  }

  console.log(`Starting search for: "${searchQuery.query}"`);
  const results = await fetchAllPages(searchQuery);
  console.log(`Found a total of ${results.length} results.`);

  if (results.length === 0) {
    console.log('No results to save.');
    return;
  }

  // We will select and flatten the data for a cleaner CSV
  const flattenedResults = results.map((place) => ({
    name: place.name,
    address: place.formatted_address,
    rating: place.rating,
    user_ratings_total: place.user_ratings_total,
    // The price_level is returned as a number (e.g., 2), so you can interpret it as "$$"
    price_level: place.price_level,
    // Not all results have a website or phone number, so we check for them
    // website: place.website, // This often requires a separate "Place Details" request
    // phone_number: place.formatted_phone_number, // This also requires a "Place Details" request
  }));

  try {
    const parser = new Parser();
    const csv = parser.parse(flattenedResults);
    fs.writeFileSync(outputFilename, csv);
    console.log(`Successfully saved data to ${outputFilename}`);
  } catch (err) {
    console.error('Error writing CSV file:', err);
  }
}

main();
