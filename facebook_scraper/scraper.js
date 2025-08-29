const puppeteer = require('puppeteer');
const { Parser } = require('json2csv');
const fs = require('fs');

const COOKIE_FILE_PATH = './facebook_session.json';

// This is the main function that will be executed
async function scrapeFacebook(postUrl, email, password) {
  console.log(`Starting Facebook scrape for: "${postUrl}"`);

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  // Set a realistic user agent
  await page.setUserAgent(
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
  );

  // --- Login ---
  try {
    // Try to load cookies first
    const cookiesString = fs.readFileSync(COOKIE_FILE_PATH);
    const cookies = JSON.parse(cookiesString);
    await page.setCookie(...cookies);
    console.log('Session restored from cookies.');
    await page.goto('https://www.facebook.com/', { waitUntil: 'networkidle2' });
  } catch (error) {
    console.log(
      'No saved session found or cookies are invalid. Proceeding with manual login.',
    );

    if (!email || !password) {
      console.error('Error: Credentials are required for the first login.');
      await browser.close();
      return; // Exit if no credentials on first login
    }

    await page.goto('https://www.facebook.com/', { waitUntil: 'networkidle2' });

    // Handle cookie consent
    const cookieButtonSelector = 'button[data-cookiebanner="accept_button"]';
    try {
      await page.waitForSelector(cookieButtonSelector, { timeout: 5000 });
      await page.click(cookieButtonSelector);
      console.log('Accepted cookies.');
    } catch (e) {
      console.log('Cookie consent button not found, proceeding...');
    }

    console.log('Entering credentials...');
    await page.type('#email', email, { delay: 30 });
    await page.type('#pass', password, { delay: 30 });
    await page.click('button[name="login"]');
    await page.waitForNavigation({ waitUntil: 'networkidle2' });
    console.log('Login successful.');

    // Save session cookies
    const cookies = await page.cookies();
    fs.writeFileSync(COOKIE_FILE_PATH, JSON.stringify(cookies, null, 2));
    console.log('Session cookies saved for future use.');
  }

  // --- Navigate to URL ---
  console.log('Navigating to URL...');
  await page.goto(postUrl, { waitUntil: 'networkidle2' });

  // --- CHOOSE SCRAPING LOGIC BASED ON URL ---
  if (postUrl.includes('/search/')) {
    // Logic for scraping search results
    console.log('Search URL detected. Scraping top 10 posts.');

    try {
      console.log('Waiting for feed to load...');
      // This is a generic selector for the main feed area.
      const feedSelector = 'div[role="feed"]';
      await page.waitForSelector(feedSelector, { timeout: 10000 });
      console.log('Feed found. Proceeding with scrape.');
    } catch (error) {
      console.log('Could not find feed on the page within 10 seconds.');
      await browser.close();
      return;
    }

    const posts = await page.evaluate(() => {
      const feed = document.querySelector('div[role="feed"]');
      if (!feed) return [];

      // Select all direct children of the feed, assuming they are posts.
      const potentialPosts = Array.from(feed.children);

      return potentialPosts
        .slice(0, 10)
        .map((post) => {
          // In each post, find the first element with user-written text and the first valid link.
          const contentElement = post.querySelector('div[dir="auto"]');
          const linkElement = post.querySelector(
            'a[href*="/posts/"], a[href*="/videos/"], a[href*="multi_permalinks"]',
          );

          return {
            postContent: contentElement
              ? contentElement.textContent
              : 'No text content found',
            postUrl: linkElement ? linkElement.href : 'No URL found',
          };
        })
        .filter((p) => p.postUrl !== 'No URL found'); // Only return items that have a valid link
    });

    console.log(`Found ${posts.length} posts.`);
    if (posts.length > 0) {
      const parser = new Parser({ fields: ['postContent', 'postUrl'] });
      const csv = parser.parse(posts);
      fs.writeFileSync('facebook_search_leads.csv', csv);
      console.log(
        'Successfully saved search results to facebook_search_leads.csv',
      );
    }
  } else {
    // Logic for scraping comments from a single post
    console.log('Single post URL detected. Scraping comments.');

    // Scroll to load comments
    console.log('Scrolling to load comments...');
    let scrollCount = 0;
    const maxScrolls = 5;
    try {
      while (scrollCount < maxScrolls) {
        await page.evaluate(() =>
          window.scrollTo(0, document.body.scrollHeight),
        );
        await new Promise((resolve) =>
          setTimeout(resolve, 2000 + Math.random() * 1000),
        );
        scrollCount++;
        console.log(`Scrolled ${scrollCount} time(s)...`);
      }
    } catch (error) {
      console.log('Error during scrolling:', error.message);
    }

    const comments = await page.evaluate(() => {
      const commentElements = document.querySelectorAll('div[role="article"]');
      return Array.from(commentElements)
        .map((comment) => {
          const userLinkElement = comment.querySelector('a[href*="/user/"]');
          const commentTextElement = comment.querySelector(
            'div[data-ad-preview="message"]',
          );
          if (commentTextElement) {
            return {
              userName: userLinkElement
                ? userLinkElement.textContent
                : 'Unknown User',
              userProfileUrl: userLinkElement ? userLinkElement.href : 'No URL',
              comment: commentTextElement.textContent,
            };
          }
          return null;
        })
        .filter((c) => c !== null);
    });

    console.log(`Found ${comments.length} potential comments.`);
    if (comments.length > 0) {
      const parser = new Parser();
      const csv = parser.parse(comments);
      fs.writeFileSync('facebook_leads.csv', csv);
      console.log('Successfully saved comments to facebook_leads.csv');
    }
  }

  await browser.close();
}

// --- Entry point ---
const args = process.argv.slice(2);
if (args.length < 1) {
  console.error(
    'Please provide at least the post URL. Usage: node scraper.js <postUrl> [email] [password]',
  );
  process.exit(1);
}

const [postUrl, email, password] = args;
scrapeFacebook(postUrl, email, password);
