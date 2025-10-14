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
        
        // First try to find upwork.com in the active pages
        for (const page of pages) {
            try {
                const isVisible = await page.evaluate(() => !document.hidden);
                if (isVisible && page.url().includes('upwork.com')) {
                    targetPage = page;
                    console.log('✅ Found active Upwork tab');
                    break;
                }
            } catch (e) {
                // Skip if can't evaluate
            }
        }
        
        // If no active Upwork page, find any Upwork page
        if (!targetPage) {
            targetPage = pages.find(page => page.url().includes('upwork.com'));
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
        
        // Try to find the active page (not hidden)
        for (const page of pages) {
            try {
                const isVisible = await page.evaluate(() => !document.hidden);
                if (isVisible) {
                    targetPage = page;
                    console.log('✅ Found active tab');
                    break;
                }
            } catch (e) {
                // Skip if can't evaluate
            }
        }
        
        // If no active page found, use the most recent tab
        if (!targetPage) {
            targetPage = pages[pages.length - 1];
            console.log('⚠️ No active tab found, using most recent tab');
        }
        
        const currentUrl = await targetPage.url();
        console.log(`📄 Scraping any content from: ${currentUrl}`);
        
        // Universal content extraction
        const pageData = await targetPage.evaluate(() => {
            const results = [];
            
            // More specific selectors for better filtering
            const jobSelectors = [
                // Upwork specific selectors
                '[data-test="job-tile"]',
                '[data-ev-label="job_tile"]',
                '.job-tile',
                '.air3-card',
                // Generic job selectors (but more specific)
                'article[class*="job"]',
                'div[class*="job-card"]',
                'a[href*="/jobs/~"][href*="?"]'  // More specific Upwork job URLs
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
                if (index >= 20) return; // Limit to 20 for better quality
                
                let title = element.textContent?.trim() || '';
                let url = element.href || '';
                let className = element.className || '';
                let tagName = element.tagName || '';
                
                // Try to get more context from parent elements
                let description = '';
                const parent = element.closest('div, article, section');
                if (parent) {
                    description = parent.textContent?.trim().substring(0, 200) || '';
                }
                
                if (title && title.length > 3) {
                    results.push({
                        title: title.substring(0, 100),
                        url: url,
                        description: description,
                        budget: '',
                        className: className,
                        tagName: tagName,
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
        
        // Save results - UPDATED PATH for frontend integration
        const dataDir = path.join(__dirname, '..', '..', '..', 'backend', 'notification_push', 'data');
        const outputFile = path.join(dataDir, 'extracted_jobs.json');
        
        // Ensure data directory exists
        await fs.mkdir(dataDir, { recursive: true });
        
        await fs.writeFile(outputFile, JSON.stringify(extractedData, null, 2));
        
        // logging success
        console.log(`✅ Extraction completed:`);
        if (Array.isArray(extractedData)) {
            console.log(`   📋 Jobs found: ${extractedData.length}`);
        } else {
            console.log(`   📋 Jobs found: ${extractedData.jobs?.length || 0}`);
            console.log(`   📄 Page info: ${extractedData.pageInfo ? 'Yes' : 'No'}`);
        }
        console.log(`   💾 Saved to: ${outputFile}`);
        
        return extractedData;
        
    } catch (error) {
        console.error('❌ Extraction failed:', error.message);
        
        // Create empty result to avoid Django 500 error
        const emptyResult = { jobs: [], pageInfo: { error: error.message } };
        const dataDir = path.join(__dirname, '..', '..', '..', 'backend', 'notification_push', 'data');
        const outputFile = path.join(dataDir, 'extracted_jobs.json');
        
        try {
            await fs.mkdir(dataDir, { recursive: true });
            await fs.writeFile(outputFile, JSON.stringify(emptyResult, null, 2));
            console.log(`💾 Saved empty result due to error: ${outputFile}`);
        } catch (writeError) {
            console.error('❌ Could not save error result:', writeError.message);
        }
        
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = { extractFromLoggedInChrome, extractFromAnyPage };