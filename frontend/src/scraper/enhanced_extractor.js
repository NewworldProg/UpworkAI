#!/usr/bin/env node
/**
 * Enhanced Job Extractor - Dual Mode
 * Mode 1: Logged-in Scraper - čita trenutnu stranicu u Chrome-u
 * Mode 2: Universal DOM Scraper - čita bilo koji content
 * MOVED TO FRONTEND - Optimized for single npm installation
 */

const puppeteerCore = require('puppeteer-core');
const fs = require('fs').promises;
const path = require('path');
const https = require('https');
const http = require('http');

// Function to save jobs directly to database via API
async function saveJobsToDatabase(extractedData, mode) {
    try {
        const jobs = Array.isArray(extractedData) ? extractedData : extractedData.jobs || [];
        
        if (jobs.length === 0) {
            console.log('⚠️ No jobs to save');
            return;
        }

        const postData = JSON.stringify({
            jobs: jobs,
            mode: mode,
            timestamp: new Date().toISOString()
        });

        const options = {
            hostname: 'localhost',
            port: 8000,
            path: '/api/notification-push/save-jobs/',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            }
        };

        return new Promise((resolve, reject) => {
            const req = http.request(options, (res) => {
                let data = '';
                res.on('data', (chunk) => {
                    data += chunk;
                });
                res.on('end', () => {
                    if (res.statusCode === 200 || res.statusCode === 201) {
                        console.log(`✅ Successfully saved ${jobs.length} jobs to database`);
                        resolve(JSON.parse(data));
                    } else {
                        console.log(`⚠️ API response: ${res.statusCode} - ${data}`);
                        resolve(null);
                    }
                });
            });

            req.on('error', (err) => {
                console.log(`⚠️ Could not save to database: ${err.message}`);
                resolve(null); // Don't fail the whole process
            });

            req.write(postData);
            req.end();
        });

    } catch (error) {
        console.log(`⚠️ Error preparing database save: ${error.message}`);
    }
}

//================================ 🛸 Mode 1: Logged-in Scraper ==============================
async function extractFromLoggedInChrome() {
    try {
        console.log('🔗 Mode 1: Connecting to your logged-in Chrome...');
        
        // in the browser variable add: 
        // gets the first to resolve
        // puppeteer-core library .connect method to connect to a running instance of Chrome
        const browser = await Promise.race([ 
            puppeteerCore.connect({
                browserURL: 'http://localhost:9222',// browser debugging port
                defaultViewport: null, // use full size of the window
                timeout: 3000  // Very short 3 second timeout
            }),// if it takes too long, reject
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Chrome connection timeout after 3 seconds')), 3000)
            )
        ]);
        // If connection is successful,
        // make variable to hold pages that are currently open in browser
        const pages = await browser.pages();
        // List all open tabs
        console.log(`📄 Found ${pages.length} open tabs`);

        // variable to hold the target page
        let targetPage = null;
        
        // Function to check if URL is a jobs page
        const isJobsPage = (url) => {
            return url.includes('upwork.com') && 
                (url.includes('/nx/search/jobs') ||
                 url.includes('/nx/find-work') ||
                 url.includes('/freelancers') ||
                 url.includes('/jobs'));
        };
        
        // First try to find active jobs page
        for (const page of pages) {
            try {
                const url = page.url();
                console.log(`🔍 Checking tab: ${url}`);
                
                const isVisible = await page.evaluate(() => !document.hidden);
                if (isVisible && isJobsPage(url)) {
                    targetPage = page;
                    console.log('✅ Found active Upwork jobs tab');
                    break;
                }
            } catch (e) {
                console.log(`⚠️ Error checking page: ${e.message}`);
            }
        }
        
        // If no active jobs page, find any jobs page
        if (!targetPage) {
            for (const page of pages) {
                try {
                    const url = page.url();
                    if (isJobsPage(url)) {
                        targetPage = page;
                        console.log('✅ Found Upwork jobs tab (not active)');
                        break;
                    }
                } catch (e) {
                    // Skip if can't get URL
                }
            }
        }
        
        // If still no jobs page, use any Upwork page as fallback
        if (!targetPage) {
            targetPage = pages.find(page => page.url().includes('upwork.com'));
            if (targetPage) {
                console.log('⚠️ Using fallback Upwork tab (not a jobs page)');
            }
        }
        
        // If still no Upwork page, use the most recent tab
        if (!targetPage) {
            targetPage = pages[pages.length - 1];
            console.log('⚠️ No Upwork page found, using most recent tab');
        } else {
            console.log('✅ Found Upwork page');
        }
        
        // if targetPage is found
        // get its URL, and proceed to scrape
        const currentUrl = await targetPage.url();
        console.log(`📄 Scraping: ${currentUrl}`);
        
        // inside varible jobData use targetPage.evaluate() and append to results array
        const jobData = await targetPage.evaluate(() => {
            const results = [];
            
            // Multiple selectors for different Upwork page types
            let jobElements = document.querySelectorAll('[data-test="job-tile"]');
            
            if (jobElements.length === 0) {
                // Try alternative selectors
                jobElements = document.querySelectorAll('[data-ev-label="job_tile"], .job-tile, .air3-card');
            }
            
            if (jobElements.length === 0) {
                // Fallback to any job links
                jobElements = document.querySelectorAll('a[href*="/jobs/"]');
            }
            // logging how many job elements were found
            console.log(`Found ${jobElements.length} job elements`);
            // Iterate and extract details
            jobElements.forEach((element, index) => {
                if (index >= 20) return; // Limit to 20
                
                let title = '';
                let url = '';
                let description = '';
                let budget = '';
                // Check if element is a link or a job tile
                if (element.tagName === 'A') {
                    // It's a link
                    title = element.textContent.trim();
                    url = element.href;
                } else {
                    // It's a job tile
                    const titleElement = element.querySelector('[data-test="job-title-link"], a[href*="/jobs/"], h4 a, h3 a');
                    if (titleElement) {
                        title = titleElement.textContent.trim();
                        url = titleElement.href;
                    }
                    // description element
                    const descElement = element.querySelector('[data-test="job-description-text"], .job-description');
                    if (descElement) {
                        description = descElement.textContent.trim();
                    }
                    // budget element
                    const budgetElement = element.querySelector('[data-test="budget"], .budget');
                    if (budgetElement) {
                        budget = budgetElement.textContent.trim();
                    }
                }
                // if title or url exists, push to results
                if (title || url) {
                    results.push({
                        title: title || 'No title',
                        url: url || '',
                        description: description || '',
                        budget: budget || '',
                        extracted_at: new Date().toISOString(),
                        source: 'logged-in-chrome'
                    });
                }
            });
            
            return results;
        });
        
        await browser.disconnect();
        return jobData;
        
    } catch (error) {
        console.error('❌ Logged-in scraper failed:', error.message);
        return [];
    }
}

//================================ 🌐 Mode 2: Universal DOM Scraper ==============================
async function extractFromAnyPage() {
    try {// logging start
        console.log('🌐 Mode 2: Universal DOM scraper...');
        
        // in the browser variable add: 
        // gets the first to resolve
        // puppeteer-core library .connect method to connect to a running instance of Chrome
        // Add timeout to connection
        console.log('🔗 Attempting to connect to Chrome de-bugging...');
        const browser = await Promise.race([
            puppeteerCore.connect({
                browserURL: 'http://localhost:9222',
                defaultViewport: null,
                timeout: 3000  // Very short 3 second timeout
            }),
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Chrome connection timeout after 3 seconds')), 3000)
            )
        ]);
        // If connection is successful,
        // make variable to hold pages that are currently open in browser
        console.log('✅ Connected to Chrome successfully');
        const pages = await browser.pages();
        console.log(`📄 Found ${pages.length} open tabs`);
        
        // Find the currently active/focused tab
        let targetPage = null;
        
        // Function to check if URL is a jobs page
        const isJobsPage = (url) => {
            return url.includes('upwork.com') && 
                (url.includes('/nx/search/jobs') ||
                 url.includes('/nx/find-work') ||
                 url.includes('/freelancers') ||
                 url.includes('/jobs'));
        };
        
        // First try to find active jobs page
        for (const page of pages) {
            try {
                const url = page.url();
                console.log(`🔍 Checking tab: ${url}`);
                
                const isVisible = await page.evaluate(() => !document.hidden);
                if (isVisible && isJobsPage(url)) {
                    targetPage = page;
                    console.log('✅ Found active Upwork jobs tab');
                    break;
                }
            } catch (e) {
                console.log(`⚠️ Error checking page: ${e.message}`);
            }
        }
        
        // If no active jobs page, find any jobs page
        if (!targetPage) {
            for (const page of pages) {
                try {
                    const url = page.url();
                    if (isJobsPage(url)) {
                        targetPage = page;
                        console.log('✅ Found Upwork jobs tab (not active)');
                        break;
                    }
                } catch (e) {
                    // Skip if can't get URL
                }
            }
        }
        
        // If no jobs page, try to find the active page
        if (!targetPage) {
            for (const page of pages) {
                try {
                    const isVisible = await page.evaluate(() => !document.hidden);
                    if (isVisible) {
                        targetPage = page;
                        console.log('⚠️ Using active tab (not a jobs page)');
                        break;
                    }
                } catch (e) {
                    // Skip if can't evaluate
                }
            }
        }
        
        // If still no page, use the most recent tab
        if (!targetPage) {
            targetPage = pages[pages.length - 1];
            console.log('⚠️ No active tab found, using most recent tab');
        }
        
        const currentUrl = await targetPage.url();
        console.log(`📄 Scraping any content from: ${currentUrl}`);
        
        // Universal content extraction
        const pageData = await targetPage.evaluate(() => {
            const results = [];
            
            // More specific selectors for better filtering - IMPROVED
            const jobSelectors = [
                // Upwork find-work page specific selectors
                'section.air3-card-section.air3-card-hover',  // Main job card container
                'section[class*="air3-card-section"]',         // Fallback for variations
                '.air3-card-section',                          // Shorter version
                // Original selectors as fallback
                '[data-test="job-tile"]',
                '[data-ev-label="job_tile"]',
                '.job-tile',
                'article[class*="job"]'
            ];
            // var to hold found elements
            let foundElements = [];
            
            for (const selector of jobSelectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    foundElements = [...foundElements, ...Array.from(elements)];
                }
            }
            
            console.log(`Found ${foundElements.length} potential job elements with specific selectors`);
            
            // If no specific job elements found, try broader search but with better filtering
            if (foundElements.length === 0) {
                console.log('No specific job elements found, trying broader search...');
                const broadElements = document.querySelectorAll('a[href*="job"], [class*="job"], [data-*="job"]');
                
                // Filter out navigation, footer, and other non-content elements
                foundElements = Array.from(broadElements).filter(element => {
                    const text = element.textContent?.trim() || '';
                    const classes = element.className || '';
                    const href = element.href || '';
                    
                    // Skip if it's navigation, footer, or other UI elements
                    const isNavigation = classes.includes('nav') || classes.includes('header') || classes.includes('footer');
                    const hasRealContent = text.length > 20; // Has substantial text content
                    const isJobLink = href.includes('/jobs/') && href.length > 30;
                    
                    return !isNavigation && (hasRealContent || isJobLink);
                });
                
                console.log(`After filtering: ${foundElements.length} elements`);
            }
            
            // Remove duplicates
            const uniqueElements = [...new Set(foundElements)];
            
            uniqueElements.forEach((element, index) => {
                if (index >= 15) return; // Limit to 15 for better quality
                
                // Improved data extraction for job cards
                let title = '';
                let url = '';
                let description = '';
                let client = '';
                let budget = '';
                
                // Extract job title - try multiple approaches
                const titleSelectors = ['h4', 'h3', 'h2', 'h5', '[data-test*="title"]', 'a[href*="/jobs/"]'];
                for (const selector of titleSelectors) {
                    const titleEl = element.querySelector(selector);
                    if (titleEl && titleEl.textContent?.trim()) {
                        title = titleEl.textContent.trim();
                        if (titleEl.href) url = titleEl.href;
                        break;
                    }
                }
                
                // Fallback - use element's own text if no title found
                if (!title) {
                    title = element.textContent?.trim() || '';
                    url = element.href || '';
                }
                
                // Extract job URL if not found yet
                if (!url) {
                    const linkEl = element.querySelector('a[href*="/jobs/"]');
                    if (linkEl) url = linkEl.href;
                }
                
                // Extract description
                description = element.textContent?.trim().substring(0, 300) || '';
                
                // Extract client name - look for client info
                const clientEl = element.querySelector('[data-test*="client"], .client-name, [class*="client"]');
                if (clientEl) {
                    client = clientEl.textContent?.trim() || '';
                }
                
                // Extract budget - look for price info
                const budgetEl = element.querySelector('[data-test*="budget"], [class*="budget"], [class*="price"]');
                if (budgetEl) {
                    budget = budgetEl.textContent?.trim() || '';
                }
                
                if (title && title.length > 3) {
                    // Generate truly unique ID with multiple factors
                    const titleHash = title.split('').reduce((a, b) => {
                        a = ((a << 5) - a) + b.charCodeAt(0);
                        return a & a;
                    }, 0);
                    
                    const uniqueId = url && url.includes('/jobs/~') && url.length > 50 ? 
                        url : 
                        `job_${Date.now()}_${index}_${Math.abs(titleHash)}_${Math.random().toString(36).substr(2, 5)}`;
                    
                    results.push({
                        id: uniqueId,
                        title: title.substring(0, 100),
                        url: url,
                        description: description,
                        client: client,
                        budget: budget,
                        className: element.className || '',
                        tagName: element.tagName || '',
                        extracted_at: new Date().toISOString(),
                        source: 'universal-dom'
                    });
                }
            });
            
            // Also try to extract general page info
            const pageInfo = {
                title: document.title,
                url: window.location.href,
                extracted_at: new Date().toISOString(),
                source: 'page-info'
            };
            
            return { jobs: results, pageInfo: pageInfo };
        });
        
        await browser.disconnect();
        return pageData;
        
    } catch (error) {
        console.error('❌ Universal scraper failed:', error.message);
        return { jobs: [], pageInfo: null };
    }
}

//================================ 🚀 Main Function ==============================
async function checkChromeAvailable() {
    try {
        // http module to check if Chrome debugging port is open
        const http = require('http');
        return new Promise((resolve) => {
            const req = http.get('http://localhost:9222/json/version', { timeout: 5000 }, (res) => {
                resolve(res.statusCode === 200);
            });
            req.on('error', () => resolve(false));
            req.on('timeout', () => {
                req.destroy();
                resolve(false);
            });
        });
    } catch (error) {
        return false;
    }
}

async function main() {
    try {
        // Determine mode from command line args
        const mode = process.argv[2] || 'logged-in';
        
        // Check if Chrome debugging is available
        console.log('🔍 Checking Chrome debugging availability...');
        const chromeAvailable = await checkChromeAvailable();
        
        if (!chromeAvailable) {
            throw new Error('Chrome debugging not available on port 9222. Please start Chrome with debugging enabled.');
        }
        
        console.log('✅ Chrome debugging is available');

        // make variable to hold extracted data
        let extractedData;
        // check mode and call appropriate function
        if (mode === 'universal') {
            console.log('🌐 Running Universal DOM Scraper...');
            extractedData = await extractFromAnyPage();
        } else {
            console.log('👤 Running Logged-in Scraper...');
            extractedData = await extractFromLoggedInChrome();
        }
        
        // Save results directly to database via API
        await saveJobsToDatabase(extractedData, mode);
        
        // logging success
        console.log(`✅ Extraction completed and saved to database:`);
        if (Array.isArray(extractedData)) {
            console.log(`   📋 Jobs found: ${extractedData.length}`);
        } else {
            console.log(`   📋 Jobs found: ${extractedData.jobs?.length || 0}`);
            console.log(`   📄 Page info: ${extractedData.pageInfo ? 'Yes' : 'No'}`);
        }
        console.log(`   💾 Saved to database via API`);
        
        return extractedData;
        
    } catch (error) {
        console.error('❌ Extraction failed:', error.message);
        
        // Log error to database via API
        await saveJobsToDatabase({ jobs: [], pageInfo: { error: error.message } }, mode || 'unknown');
        
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { extractFromLoggedInChrome, extractFromAnyPage };