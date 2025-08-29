const puppeteer = require('puppeteer');
const { Parser } = require('json2csv');
const fs = require('fs');

// This is the main function that will be executed
async function scrapeGoogleMaps(query) {
  console.log(`Starting headless scrape for: "${query}"`);

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();

  // Set a realistic user agent
  await page.setUserAgent(
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
  );

  // Navigate to Google Maps
  await page.goto(
    `https://www.google.com/maps/search/${query.replace(/ /g, '+')}`,
    { waitUntil: 'networkidle2' },
  );

  // This is the selector for the scrollable results panel
  const scrollableSelector = '.m6Utre';

  // --- The scrolling logic ---
  // This is the most fragile part. Google can change its layout, breaking this.
  let results = [];
  try {
    await page.waitForSelector(scrollableSelector, { timeout: 5000 });
    let previousHeight;
    let scrollCount = 0;
    const maxScrolls = 10; // To prevent infinite loops

    while (scrollCount < maxScrolls) {
      const currentHeight = await page.evaluate((selector) => {
        const element = document.querySelector(selector);
        return element.scrollHeight;
      }, scrollableSelector);

      if (currentHeight === previousHeight) {
        break; // Stop if the height hasn't changed
      }

      await page.evaluate((selector) => {
        const element = document.querySelector(selector);
        element.scrollTop = element.scrollHeight;
      }, scrollableSelector);

      await new Promise((resolve) => setTimeout(resolve, 2000)); // Wait for new results to load
      previousHeight = currentHeight;
      scrollCount++;
      console.log(`Scrolled ${scrollCount} time(s)...`);
    }
  } catch (error) {
    console.log(
      'Could not find the results panel to scroll, or an error occurred during scrolling. Scraping what is visible...',
    );
  }

  // --- The data extraction logic ---
  // This is adapted from the original browser extension
  const scrapedData = await page.evaluate(() => {
    const links = Array.from(
      document.querySelectorAll('a[href^="https://www.google.com/maps/place"]'),
    );
    return links
      .map((link) => {
        const container = link.closest('[jsaction*="mouseover:pane"]');
        if (!container) return null;

        const title =
          container.querySelector('.fontHeadlineSmall')?.textContent || '';
        let rating = '0';
        let reviewCount = '0';
        let phoneNumber = '';

        const roleImgContainer = container.querySelector('[role="img"]');
        if (roleImgContainer) {
          const ariaLabel = roleImgContainer.getAttribute('aria-label');
          if (ariaLabel && ariaLabel.includes('stars')) {
            const parts = ariaLabel.split(' ');
            rating = parts[0];
            reviewCount = parts[2] ? parts[2].replace(/\(|\)/g, '') : '0';
          }
        }

        const phoneNumberElement = container.querySelector(
          '[data-item-id^="phone:tel:"]',
        );
        if (phoneNumberElement) {
          phoneNumber = phoneNumberElement
            .getAttribute('data-item-id')
            .replace('phone:tel:', '');
        } else {
          const phoneSpan = container.querySelector('.rog2Wb'); // Common class for phone number
          if (phoneSpan) {
            phoneNumber = phoneSpan.textContent.trim();
          }
        }

        return {
          title: title,
          rating: rating,
          reviewCount: reviewCount,
          href: link.href,
          phoneNumber: phoneNumber, // Add phone number
        };
      })
      .filter((item) => item !== null && item.title); // Filter out nulls and items without a title
  });

  console.log(`Found ${scrapedData.length} results.`);
  await browser.close();

  // --- Save to CSV ---
  if (scrapedData.length > 0) {
    const parser = new Parser();
    const csv = parser.parse(scrapedData);
    fs.writeFileSync('headless_leads.csv', csv);
    console.log('Successfully saved data to headless_leads.csv');
  }
}

// --- Entry point ---
// The script takes the search query as a command-line argument
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error(
    'Please provide a search query. Example: node scraper.js "restaurants in New York"',
  );
  process.exit(1);
}

const query = args.join(' ');
scrapeGoogleMaps(query);
