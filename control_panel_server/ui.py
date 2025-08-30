def render_base(page_content, page_title="Scraper Control Panel"):
    """Renders the base HTML structure with dynamic content."""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/favicon-16x16.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="48x48" href="/static/favicon-48x48.png">
    <link rel="icon" type="image/png" sizes="64x64" href="/static/favicon-64x64.png">
    <link rel="icon" type="image/png" sizes="96x96" href="/static/favicon-96x96.png">
    <link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
    <link rel="apple-touch-icon" sizes="152x152" href="/static/apple-touch-icon-152x152.png">
    <link rel="apple-touch-icon" sizes="167x167" href="/static/apple-touch-icon-167x167.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/static/apple-touch-icon-180x180.png">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/styles.css">
    <style>
        .spinner-border {{
            width: 1rem;
            height: 1rem;
            margin-right: 0.5rem;
        }}
        .btn-loading {{
            pointer-events: none;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="visitor-stats">
            <span>Total Visitors: <span id="total-visitors">-</span></span>
            <span>Today: <span id="today-visitors">-</span></span>
            <span>Last Hour: <span id="last-hour-visitors">-</span></span>
        </div>
        <div class="theme-switch-wrapper">
            <label class="theme-switch" for="checkbox">
                <input type="checkbox" id="checkbox" />
                <div class="slider round"></div>
            </label>
        </div>
        {page_content}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        (function() {{
            const themeToggle = document.getElementById('checkbox');
            const htmlElement = document.documentElement;

            // Function to set theme
            function setTheme(theme) {{
                localStorage.setItem('theme', theme);
                htmlElement.setAttribute('data-bs-theme', theme);
                themeToggle.checked = theme === 'dark';
            }}

            // Event listener for the toggle
            themeToggle.addEventListener('change', function() {{
                setTheme(this.checked ? 'dark' : 'light');
            }});

            // Check for saved theme in localStorage
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {{
                setTheme(savedTheme);
            }} else {{
                // If no saved theme, check system preference
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
                setTheme(prefersDark.matches ? 'dark' : 'light');
            }}

            // Listen for changes in system preference
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {{
                // Only change if there's no manually saved theme
                if (!localStorage.getItem('theme')) {{
                    setTheme(e.matches ? 'dark' : 'light');
                }}
            }});

            // Fetch visitor stats
            function fetchVisitorStats() {{
                fetch('/api/visitors')
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('total-visitors').textContent = data.total;
                        document.getElementById('today-visitors').textContent = data.today;
                        document.getElementById('last-hour-visitors').textContent = data.last_hour;
                    }})
                    .catch(error => console.error('Error fetching visitor stats:', error));
            }}

            // Fetch stats on page load
            fetchVisitorStats();
            // Refresh stats every 30 seconds
            setInterval(fetchVisitorStats, 30000);
        }})();
    </script>
</body>
</html>
"""

def render_index_page():
    """Renders the content for the main index page."""
    index_content = """
        <h1 class="mb-4">Scraper Control Panel</h1>

        <!-- Navigation -->
        <ul class="nav nav-tabs">
            <li class="nav-item">
                <a class="nav-link active" aria-current="page" href="/">Scrapers</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/results">View Results</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/admin">Admin Panel</a>
            </li>
        </ul>

        <div class="tab-content" id="myTabContent">
            <div class="tab-pane fade show active" id="scrapers" role="tabpanel" aria-labelledby="scrapers-tab">
                
                <!-- Scraper Selection Dropdown -->
                <div class="card mt-4">
                    <div class="card-header">Select Scraper</div>
                    <div class="card-body">
                        <div class="input-group mb-3">
                            <select id="scraper-select" class="form-select" onchange="showScraperOptions()">
                                <option value="gmaps-api" selected>Google Maps API Scraper</option>
                                <option value="gmaps-headless">Headless Google Maps Scraper</option>
                                <option value="facebook">Facebook Scraper</option>
                                <option value="wikipedia">Wikipedia Test Scraper</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Scraper Options Container -->
                <div id="scraper-options-container"></div>

                <!-- Live Log Output -->
                <div class="card mt-4">
                    <div class="card-header">Live Logs</div>
                    <div class="card-body">
                        <div id="log-output" class="log-box"></div>
                    </div>
                </div>

            </div>
        </div>

        <script>
            let currentEventSource = null;

            function showScraperOptions() {
                const selection = document.getElementById('scraper-select').value;
                const container = document.getElementById('scraper-options-container');
                container.innerHTML = ''; // Clear previous options

                if (selection === 'gmaps-api') {
                    container.innerHTML = `
                        <div class="card mt-4">
                            <div class="card-header">Google Maps API Scraper</div>
                            <div class="card-body">
                                <div class="input-group mb-3">
                                    <input type="text" id="api-query" class="form-control" placeholder="Enter search query (e.g., 'restaurants in New York')">
                                    <button class="btn btn-primary" id="api-scrape-btn" onclick="scrapeAPI()">
                                        <span class="btn-text">Scrape</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                } else if (selection === 'gmaps-headless') {
                    container.innerHTML = `
                        <div class="card mt-4">
                            <div class="card-header">Headless Google Maps Scraper</div>
                            <div class="card-body">
                                <div class="input-group mb-3">
                                    <input type="text" id="headless-query" class="form-control" placeholder="Enter search query (e.g., 'plumbers in London')">
                                    <button class="btn btn-primary" id="headless-scrape-btn" onclick="scrapeHeadless()">
                                        <span class="btn-text">Scrape</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                } else if (selection === 'facebook') {
                    container.innerHTML = `
                        <div class="card mt-4">
                            <div class="card-header">Facebook Scraper</div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <input type="text" id="facebook-url" class="form-control" placeholder="Enter Facebook Post URL or Search Query">
                                </div>
                                <div class="row g-2 mb-3">
                                    <div class="col-md">
                                        <input type="email" id="facebook-email" class="form-control" placeholder="Facebook Email (optional)">
                                    </div>
                                    <div class="col-md">
                                        <input type="password" id="facebook-password" class="form-control" placeholder="Facebook Password (optional)">
                                    </div>
                                </div>
                                <button class="btn btn-primary" id="facebook-scrape-btn" onclick="scrapeFacebook()">
                                    <span class="btn-text">Scrape & View Live Logs</span>
                                </button>
                            </div>
                        </div>
                    `;
                } else if (selection === 'wikipedia') {
                    container.innerHTML = `
                        <div class="card mt-4">
                            <div class="card-header">Wikipedia Test Scraper</div>
                            <div class="card-body">
                                <div class="input-group mb-3">
                                    <input type="text" id="test-query" class="form-control" placeholder="Enter search query for Wikipedia">
                                    <button class="btn btn-info" id="test-scrape-btn" onclick="scrapeTest()">
                                        <span class="btn-text">Run Test Scrape</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                }
            }

            function setButtonLoading(buttonId, isLoading) {
                const button = document.getElementById(buttonId);
                const btnText = button.querySelector('.btn-text');
                
                if (isLoading) {
                    button.classList.add('btn-loading');
                    btnText.innerHTML = `
                        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                        Loading...
                    `;
                } else {
                    button.classList.remove('btn-loading');
                    // Reset button text based on button type
                    if (buttonId.includes('api')) {
                        btnText.innerHTML = 'Scrape';
                    } else if (buttonId.includes('headless')) {
                        btnText.innerHTML = 'Scrape';
                    } else if (buttonId.includes('facebook')) {
                        btnText.innerHTML = 'Scrape & View Live Logs';
                    } else if (buttonId.includes('test')) {
                        btnText.innerHTML = 'Run Test Scrape';
                    }
                }
            }

            function scrapeAPI() {
                const query = document.getElementById('api-query').value;
                if (!query.trim()) {
                    alert('Please enter a search query');
                    return;
                }
                
                const fullUrl = `/scrape/api?query=${encodeURIComponent(query)}`;
                setupEventSource(fullUrl, 'api-scrape-btn');
            }

            function scrapeHeadless() {
                const query = document.getElementById('headless-query').value;
                if (!query.trim()) {
                    alert('Please enter a search query');
                    return;
                }
                
                const fullUrl = `/scrape/headless?query=${encodeURIComponent(query)}`;
                setupEventSource(fullUrl, 'headless-scrape-btn');
            }

            function setupEventSource(url, buttonId) {
                // Close any existing event source
                if (currentEventSource) {
                    currentEventSource.close();
                }

                const logOutput = document.getElementById('log-output');
                logOutput.innerHTML = ''; // Clear previous logs
                
                // Set button to loading state
                setButtonLoading(buttonId, true);
                
                currentEventSource = new EventSource(url);

                currentEventSource.onopen = function() {
                    logOutput.innerHTML += 'Connection opened.<br>';
                };

                currentEventSource.onmessage = function(event) {
                    logOutput.innerHTML += event.data + '<br>';
                    logOutput.scrollTop = logOutput.scrollHeight;
                };

                currentEventSource.addEventListener('close', function() {
                    logOutput.innerHTML += 'Connection closed by server.<br>';
                    currentEventSource.close();
                    currentEventSource = null;
                    setButtonLoading(buttonId, false);
                });

                currentEventSource.onerror = function(err) {
                    logOutput.innerHTML += 'EventSource failed.<br>';
                    console.error("EventSource failed:", err);
                    currentEventSource.close();
                    currentEventSource = null;
                    setButtonLoading(buttonId, false);
                };
            }

            function scrapeFacebook() {
                const url = document.getElementById('facebook-url').value;
                if (!url.trim()) {
                    alert('Please enter a Facebook URL or search query');
                    return;
                }
                
                const email = document.getElementById('facebook-email').value;
                const password = document.getElementById('facebook-password').value;
                const fullUrl = `/scrape/facebook?url=${encodeURIComponent(url)}&email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;
                setupEventSource(fullUrl, 'facebook-scrape-btn');
            }

            function scrapeTest() {
                const query = document.getElementById('test-query').value;
                if (!query.trim()) {
                    alert('Please enter a search query');
                    return;
                }
                
                const fullUrl = `/scrape/test?query=${encodeURIComponent(query)}`;
                setupEventSource(fullUrl, 'test-scrape-btn');
            }

            // Show scraper options on page load
            document.addEventListener('DOMContentLoaded', () => {
                showScraperOptions();
            });

            // Clean up event source when page unloads
            window.addEventListener('beforeunload', () => {
                if (currentEventSource) {
                    currentEventSource.close();
                }
            });
        </script>
    """
    return render_base(index_content, "Scraper Control Panel")

def render_results_page():
    """Renders the content for the results page."""
    results_content = """
        <h1 class="mb-4">Scraped Results</h1>

        <!-- Navigation -->
        <ul class="nav nav-tabs">
            <li class="nav-item">
                <a class="nav-link" href="/">Scrapers</a>
            </li>
            <li class="nav-item">
                <a class="nav-link active" aria-current="page" href="/results">View Results</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="/admin">Admin Panel</a>
            </li>
        </ul>

        <!-- Filters -->
        <div class="card mt-4">
            <div class="card-header">Filters</div>
            <div class="card-body">
                <div class="row g-3">
                    <div class="col-md-3">
                        <input type="text" id="search-term-filter" class="form-control" placeholder="Search Term (fuzzy)">
                    </div>
                    <div class="col-md-3">
                        <input type="text" id="business-type-filter" class="form-control" placeholder="Business Name/Title (fuzzy)">
                    </div>
                    <div class="col-md-3">
                        <input type="text" id="address-filter" class="form-control" placeholder="Address (fuzzy)">
                    </div>
                    <div class="col-md-3">
                        <select id="source-filter" class="form-select">
                            <option value="">All Sources</option>
                            <option value="gmaps_api">Google Maps API</option>
                            <option value="gmaps_headless">Google Maps Headless</option>
                            <option value="facebook_comments">Facebook Comments</option>
                            <option value="facebook_posts">Facebook Posts</option>
                            <option value="wikipedia">Wikipedia</option>
                        </select>
                    </div>
                </div>
                <button class="btn btn-primary mt-3" onclick="fetchResults(1)">Apply Filters</button>
                <button class="btn btn-success mt-3" data-bs-toggle="modal" data-bs-target="#emailModal">Download XLSX</button>
            </div>
        </div>

        <!-- Email Modal -->
        <div class="modal fade" id="emailModal" tabindex="-1" aria-labelledby="emailModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="emailModalLabel">Download XLSX</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>Please provide your email id to receive a copy of the scrape session</p>
                        <input type="email" id="email-input" class="form-control" placeholder="Enter your email">
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" onclick="downloadXLSX()">Download</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Results Table -->
        <div class="table-responsive mt-4">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Source</th>
                        <th>Name / Title</th>
                        <th>Address / Content</th>
                        <th>Rating</th>
                        <th>Phone</th>
                        <th>URL / Link</th>
                        <th>Scraped At</th>
                    </tr>
                </thead>
                <tbody id="results-tbody">
                    <!-- Results will be injected here -->
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        <nav>
            <ul class="pagination" id="pagination">
                <!-- Pagination links will be injected here -->
            </ul>
        </nav>

        <script>
            let currentPage = 1;
            const pageSize = 15;

            function fetchResults(page) {
                currentPage = page;
                const searchTerm = document.getElementById('search-term-filter').value;
                const businessType = document.getElementById('business-type-filter').value;
                const address = document.getElementById('address-filter').value;
                const source = document.getElementById('source-filter').value;

                const url = `/api/results?page=${page}&page_size=${pageSize}&search_term=${encodeURIComponent(searchTerm)}&business_type=${encodeURIComponent(businessType)}&address=${encodeURIComponent(address)}&source=${source}`;

                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        const tbody = document.getElementById('results-tbody');
                        tbody.innerHTML = '';
                        if (data.results) {
                            data.results.forEach(item => {
                                const row = `
                                    <tr>
                                        <td>${item.source_display || 'N/A'}</td>
                                        <td>${item.name_title || 'N/A'}</td>
                                        <td>${item.address_content || 'N/A'}</td>
                                        <td>${item.rating || 'N/A'}</td>
                                        <td>${item.phone_number || 'N/A'}</td>
                                        <td>${item.url ? `<a href="${item.url}" target="_blank">Link</a>` : 'N/A'}</td>
                                        <td>${new Date(item.scraped_at).toLocaleString()}</td>
                                    </tr>
                                `;
                                tbody.innerHTML += row;
                            });
                        }
                        renderPagination(data.total_count, page, pageSize);
                    })
                    .catch(error => console.error('Error fetching results:', error));
            }

            function downloadXLSX() {
                const email = document.getElementById('email-input').value;
                if (!email) {
                    alert('Please enter your email address.');
                    return;
                }

                const searchTerm = document.getElementById('search-term-filter').value;
                const businessType = document.getElementById('business-type-filter').value;
                const address = document.getElementById('address-filter').value;
                const source = document.getElementById('source-filter').value;

                const url = `/download/xlsx?email=${encodeURIComponent(email)}&search_term=${encodeURIComponent(searchTerm)}&business_type=${encodeURIComponent(businessType)}&address=${encodeURIComponent(address)}&source=${source}`;
                
                window.location.href = url;
            }

            function renderPagination(totalCount, page, pageSize) {
                const paginationUl = document.getElementById('pagination');
                paginationUl.innerHTML = '';
                const totalPages = Math.ceil(totalCount / pageSize);

                if (totalPages <= 1) return;

                // Previous button
                const prevLi = document.createElement('li');
                prevLi.className = `page-item ${page === 1 ? 'disabled' : ''}`;
                const prevA = document.createElement('a');
                prevA.className = 'page-link';
                prevA.href = '#';
                prevA.innerText = 'Previous';
                prevA.onclick = (e) => { e.preventDefault(); if (page > 1) fetchResults(page - 1); };
                prevLi.appendChild(prevA);
                paginationUl.appendChild(prevLi);

                // Page numbers
                for (let i = 1; i <= totalPages; i++) {
                    const li = document.createElement('li');
                    li.className = `page-item ${i === page ? 'active' : ''}`;
                    const a = document.createElement('a');
                    a.className = 'page-link';
                    a.href = '#';
                    a.innerText = i;
                    a.onclick = (e) => { e.preventDefault(); fetchResults(i); };
                    li.appendChild(a);
                    paginationUl.appendChild(li);
                }

                // Next button
                const nextLi = document.createElement('li');
                nextLi.className = `page-item ${page === totalPages ? 'disabled' : ''}`;
                const nextA = document.createElement('a');
                nextA.className = 'page-link';
                nextA.href = '#';
                nextA.innerText = 'Next';
                nextA.onclick = (e) => { e.preventDefault(); if (page < totalPages) fetchResults(page + 1); };
                nextLi.appendChild(nextA);
                paginationUl.appendChild(nextLi);
            }

            // Initial fetch
            document.addEventListener('DOMContentLoaded', () => fetchResults(1));
        </script>
    """
    return render_base(results_content, "Scraped Results")

def render_admin_login_page():
    """Renders the admin login page."""
    login_content = """
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">Admin Panel Login</div>
                        <div class="card-body">
                            <div class="input-group mb-3">
                                <input type="password" id="admin-password" class="form-control" placeholder="Enter admin password">
                                <button class="btn btn-primary" onclick="loginAdmin()">Login</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function loginAdmin() {
                const password = document.getElementById('admin-password').value;
                fetch('/admin/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: password })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert('Incorrect password.');
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        </script>
    """
    return render_base(login_content, "Admin Panel Login")

def render_admin_page():
    """Renders the main admin panel page."""
    admin_content = """
        <h1 class="mb-4">Admin Panel</h1>
        <a href="/admin/logout" class="btn btn-secondary mb-4">Logout</a>

        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">Filters</div>
                    <div class="card-body">
                        <button class="btn btn-primary" onclick="updateDashboard('Google Maps API')">Google Maps API</button>
                        <button class="btn btn-primary" onclick="updateDashboard('Google Maps Headless')">Google Maps Headless</button>
                        <button class="btn btn-primary" onclick="updateDashboard('Facebook Comments')">Facebook Comments</button>
                        <button class="btn btn-primary" onclick="updateDashboard('Facebook Posts')">Facebook Posts</button>
                        <button class="btn btn-primary" onclick="updateDashboard('Wikipedia')">Wikipedia</button>
                        <button class="btn btn-secondary" onclick="updateDashboard(null)">Clear Filter</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Leads by Scraper</div>
                    <div class="card-body">
                        <canvas id="leads-by-scraper-chart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">Lead Sources</div>
                    <div class="card-body">
                        <canvas id="lead-sources-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">Visitors Over Time</div>
                    <div class="card-body">
                        <canvas id="visitors-over-time-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">Business Type Searches</div>
                    <div class="card-body">
                        <canvas id="business-type-chart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">Search Intent Searches</div>
                    <div class="card-body">
                        <canvas id="search-intent-chart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">Location Searches</div>
                    <div class="card-body">
                        <canvas id="location-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">SQL Search</div>
                    <div class="card-body">
                        <div class="input-group mb-3">
                            <textarea id="sql-query" class="form-control" placeholder="Enter SQL query"></textarea>
                            <button class="btn btn-primary" onclick="runSQLQuery()">Run Query</button>
                        </div>
                        <div id="sql-results-container"></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-md-12">
                <div class="card border-danger">
                    <div class="card-header bg-danger text-white">Admin: Purge Database</div>
                    <div class="card-body">
                        <div class="input-group mb-3">
                            <input type="password" id="db-password" class="form-control" placeholder="Enter database password to purge">
                            <button class="btn btn-danger" onclick="purgeDatabase()">Purge Database</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            // Chart 1: Leads by Scraper
            fetch('/api/admin/stats/leads_by_scraper')
                .then(response => response.json())
                .then(data => {
                    const ctx = document.getElementById('leads-by-scraper-chart').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: Object.keys(data),
                            datasets: [{
                                label: '# of Leads',
                                data: Object.values(data),
                                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                borderColor: 'rgba(54, 162, 235, 1)',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            }
                        }
                    });
                });

            // Chart 2: Lead Sources
            fetch('/api/admin/stats/lead_sources')
                .then(response => response.json())
                .then(data => {
                    const ctx = document.getElementById('lead-sources-chart').getContext('2d');
                    new Chart(ctx, {
                        type: 'pie',
                        data: {
                            labels: Object.keys(data),
                            datasets: [{
                                label: '# of Leads',
                                data: Object.values(data),
                                backgroundColor: [
                                    'rgba(255, 99, 132, 0.2)',
                                    'rgba(54, 162, 235, 0.2)',
                                    'rgba(255, 206, 86, 0.2)',
                                    'rgba(75, 192, 192, 0.2)',
                                    'rgba(153, 102, 255, 0.2)'
                                ],
                                borderColor: [
                                    'rgba(255, 99, 132, 1)',
                                    'rgba(54, 162, 235, 1)',
                                    'rgba(255, 206, 86, 1)',
                                    'rgba(75, 192, 192, 1)',
                                    'rgba(153, 102, 255, 1)'
                                ],
                                borderWidth: 1
                            }]
                        },
                        options: {
                            onClick: (evt, item) => {
                                if (item.length > 0) {
                                    const chart = item[0].chart;
                                    const label = chart.data.labels[item[0].index];
                                    updateDashboard(label);
                                }
                            }
                        }
                    });
                });

            // Chart 3: Visitors Over Time
            fetch('/api/admin/stats/visitors_over_time')
                .then(response => response.json())
                .then(data => {
                    const ctx = document.getElementById('visitors-over-time-chart').getContext('2d');
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: Object.keys(data),
                            datasets: [{
                                label: '# of Visitors',
                                data: Object.values(data),
                                fill: false,
                                borderColor: 'rgb(75, 192, 192)',
                                tension: 0.1
                            }]
                        }
                    });
                });

            // Chart 4: Business Type Searches
            fetch('/api/admin/stats/business_type_searches')
                .then(response => response.json())
                .then(data => {
                    const ctx = document.getElementById('business-type-chart').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: Object.keys(data),
                            datasets: [{
                                label: '# of Searches',
                                data: Object.values(data),
                                backgroundColor: 'rgba(255, 159, 64, 0.2)',
                                borderColor: 'rgba(255, 159, 64, 1)',
                                borderWidth: 1
                            }]
                        }
                    });
                });

            // Chart 5: Search Intent Searches
            fetch('/api/admin/stats/search_intent_searches')
                .then(response => response.json())
                .then(data => {
                    const ctx = document.getElementById('search-intent-chart').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: Object.keys(data),
                            datasets: [{
                                label: '# of Searches',
                                data: Object.values(data),
                                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                borderColor: 'rgba(75, 192, 192, 1)',
                                borderWidth: 1
                            }]
                        }
                    });
                });

            // Chart 6: Location Searches
            fetch('/api/admin/stats/location_searches')
                .then(response => response.json())
                .then(data => {
                    const ctx = document.getElementById('location-chart').getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: Object.keys(data),
                            datasets: [{
                                label: '# of Searches',
                                data: Object.values(data),
                                backgroundColor: 'rgba(153, 102, 255, 0.2)',
                                borderColor: 'rgba(153, 102, 255, 1)',
                                borderWidth: 1
                            }]
                        }
                    });
                });

            function runSQLQuery() {
                const query = document.getElementById('sql-query').value;
                fetch('/api/admin/sql', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                })
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('sql-results-container');
                    if (data.error) {
                        container.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                        return;
                    }

                    if (data.table_name) {
                        updateDashboard(data.table_name);
                    }

                    let table = '<table class="table table-striped mt-3"><thead><tr>';
                    data.columns.forEach(column => {
                        table += `<th>${column}</th>`;
                    });
                    table += '</tr></thead><tbody>';
                    data.rows.forEach(row => {
                        table += '<tr>';
                        row.forEach(cell => {
                            table += `<td>${cell}</td>`;
                        });
                        table += '</tr>';
                    });
                    table += '</tbody></table>';
                    container.innerHTML = table;
                })
                .catch(error => console.error('Error:', error));
            }

            function updateDashboard(filter) {
                const tableMap = {
                    'gmaps_api_leads': 'Google Maps API',
                    'gmaps_headless_leads': 'Google Maps Headless',
                    'facebook_comments': 'Facebook Comments',
                    'facebook_search_posts': 'Facebook Posts',
                    'wikipedia_results': 'Wikipedia'
                };

                let source_filter = tableMap[filter] || filter;

                let url_leads = '/api/admin/stats/leads_by_scraper';
                let url_visitors = '/api/admin/stats/visitors_over_time';

                if (source_filter) {
                    url_leads += `?source=${source_filter}`;
                    url_visitors += `?source=${source_filter}`;
                }

                // Update Leads by Scraper Chart
                fetch(url_leads)
                    .then(response => response.json())
                    .then(data => {
                        const chart = Chart.getChart("leads-by-scraper-chart");
                        chart.data.labels = Object.keys(data);
                        chart.data.datasets[0].data = Object.values(data);
                        chart.update();
                    });

                // Update Visitors Over Time Chart
                fetch(url_visitors)
                    .then(response => response.json())
                    .then(data => {
                        const chart = Chart.getChart("visitors-over-time-chart");
                        chart.data.labels = Object.keys(data);
                        chart.data.datasets[0].data = Object.values(data);
                        chart.update();
                    });
            }

            function purgeDatabase() {
                const password = document.getElementById('db-password').value;
                if (confirm('Are you sure you want to permanently delete all data?')) {
                    fetch('/purge_database', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ password: password })
                    })
                    .then(response => response.json())
                    .then(data => alert(data.message || data.error))
                    .catch(error => console.error('Error:', error));
                }
            }
        </script>
    """
    return render_base(admin_content, "Admin Panel")