#!/usr/bin/env node
/**
 * Active Chat Scraper - Extracts content from currently open Upwork chat
 * Specifically designed for AI analysis and reply suggestions
 */

// in variable put puppeteer-core
const puppeteerCore = require('puppeteer-core');

// ================================= 🛸💬scrape active chat ==============================
async function scrapeActiveChatContent() {
    try {
        // log
        console.log('🤖 Connecting to Chrome debugger for active chat analysis...');
        
        // variable to hold browser and retry
        let browser;
        let retries = 3;
        
        // 3 tries to connect to Chrome debugger
        while (retries > 0) {
            try {
                // log the conn attempt
                console.log(`🔄 Connection attempt ${4 - retries}/3...`);
                // in browser put puppeteerCore.connect and chrome debugger url + timeout
                browser = await puppeteerCore.connect({
                    browserURL: 'http://localhost:9222',
                    defaultViewport: null,
                    timeout: 15000
                });
                // if connected break the loop and log
                console.log('✅ Connected to Chrome debugger');
                break;
                // if error catch and retry
            } catch (err) {
                retries--;
                console.log(`⚠️ Connection failed: ${err.message}`);
                if (retries > 0) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                } else {
                    throw new Error(`Failed to connect after 3 attempts: ${err.message}`);
                }
            }
        }
        // in variable put pages opened in browser and log how many 
        const pages = await browser.pages();
        console.log(`📄 Found ${pages.length} open tabs`);
        
        // in variable put activeChatPage 
        let activeChatPage = null;
        
        // Find page that has active Upwork chat
        for (const page of pages) {
            try {
                // in url var put page.url and log
                const url = page.url();
                console.log(`🔍 Checking page: ${url}`);
                
                // Check for Upwork chat paths in url var
                if (url.includes('upwork.com') && 
                    (url.includes('/messages') || 
                     url.includes('/ab/messages') ||
                     url.includes('/nx/messages') ||
                     url.includes('rooms/room_'))) {

                    // if found, set activeChatPage and log
                    activeChatPage = page;
                    console.log('✅ Found Upwork chat tab');
                    break;
                }
            } catch (e) {
                console.log(`⚠️ Error checking page: ${e.message}`);
                continue;
            }
        }
        // If no active chat page found, output error and exit
        if (!activeChatPage) {
            const result = { 
                success: false, 
                error: `No active Upwork chat found. Found ${pages.length} total tabs. Please open a chat in Chrome.`,
                chatData: null
            };
            console.log(JSON.stringify(result));
            return;
        }

        console.log('✅ Found active chat page:', activeChatPage.url());

        // build chatData variable with pupeteer function evaluate()
        // that puts scraped data inside document variable
        const chatData = await activeChatPage.evaluate(() => {
            // Initialize result object that holds variables from below
            const result = {
                success: true,
                url: window.location.href,
                chatTitle: '',
                projectTitle: '',
                participants: [],
                messages: [],
                extractedAt: new Date().toISOString()
            };

            // initialize chatTitle object that contains document query selector for room title
            const roomTitleElement = document.querySelector('.room-title, #room-header-title, .room-header-title');
            if (roomTitleElement) {
                // in result.chatTitle object put trimed document query selector for room title
                result.chatTitle = roomTitleElement.textContent.trim();
            }

            // initialize subtitleElement object that holds .room-subtitle selector
            const subtitleElement = document.querySelector('.room-subtitle');
            if (subtitleElement) {
                // in result.projectTitle object put trimed document query selector for room-subtitle
                result.projectTitle = subtitleElement.textContent.trim();
            }

            // in variable put chat messages by selecting all story items and log how many found
            const storyItems = document.querySelectorAll('.up-d-story-item');
            console.log(`Found ${storyItems.length} story items`);
            // than loop through each story item
            storyItems.forEach((storyItem, index) => {
                try {
                    // initialize messageElement that holds .story-message .up-d-message or .up-d-message selector
                    const messageElement = storyItem.querySelector('.story-message .up-d-message, .up-d-message');
                    if (!messageElement) return;
                    // in variable messageText put trimed text content of messageElement
                    let messageText = messageElement.textContent?.trim();
                    if (!messageText || messageText.length === 0) return;
                    
                    // Clean up message text - remove "end-of-message" markers and extra whitespace
                    messageText = messageText.replace(/\s*end-of-message\s*/g, '').replace(/\s+/g, ' ').trim();
                    
                    // Skip if message is too short
                    if (messageText.length < 2) return;
                    
                    // Get author name
                    let author = 'System';
                    const nameElement = storyItem.querySelector('.user-name');
                    if (nameElement) {
                        author = nameElement.textContent?.trim() || 'Unknown';
                    } else {
                        // Check if this is a system message (like "sent an offer", "accepted an offer")
                        if (messageText.includes('sent an offer') || 
                            messageText.includes('accepted an offer') || 
                            messageText.includes('Contract started')) {
                            const strongElement = messageElement.querySelector('strong');
                            if (strongElement) {
                                author = strongElement.textContent?.trim() || 'System';
                            }
                        }
                    }
                    
                    // Add to participants list if not already there
                    if (author !== 'System' && author !== 'Unknown' && !result.participants.includes(author)) {
                        result.participants.push(author);
                    }
                    
                    // Get timestamp
                    let timestamp = '';
                    const timeElement = storyItem.querySelector('.story-timestamp');
                    if (timeElement) {
                        timestamp = timeElement.getAttribute('title') || timeElement.textContent?.trim() || '';
                    }
                    
                    // Get the date if available (from day header)
                    let date = '';
                    const dayHeader = storyItem.querySelector('.story-day-header .header-timestamp');
                    if (dayHeader) {
                        date = dayHeader.textContent?.trim() || '';
                    }
                    // inside messages append a new object that holds
                    // id, author, content, timestamp, date and type (system or user)
                    result.messages.push({
                        id: `msg_${index}`,
                        author: author,
                        content: messageText,
                        timestamp: timestamp,
                        date: date,
                        type: author === 'System' ? 'system' : 'user'
                    });
                    
                } catch (error) {
                    console.log(`Error processing story item ${index}:`, error);
                }
            });
            
            // Sort messages by timestamp if possible (assuming timestamp is in a parseable format)
            result.messageCount = result.messages.length;
            
            if (result.messages.length === 0) {
                result.success = false;
                result.error = 'No chat messages found';
                result.debug = {
                    storyItemsFound: storyItems.length,
                    hasMessageElements: document.querySelectorAll('.up-d-message').length > 0,
                    hasStoryMessages: document.querySelectorAll('.story-message').length > 0
                };
            }
            
            return result;
        });

        // Output the result as JSON
        console.log(JSON.stringify(chatData, null, 2));
        
        await browser.disconnect();

    } catch (error) {
        console.error('Error in scrapeActiveChatContent:', error);
        const errorResult = { 
            success: false,
            error: 'Failed to scrape chat content', 
            details: error.message
        };
        console.log(JSON.stringify(errorResult));
        process.exit(1);
    }
}

// Run the scraper
if (require.main === module) {
    scrapeActiveChatContent()
        .then(() => {
            process.exit(0);
        })
        .catch(error => {
            console.error('Script error:', error);
            const errorResult = { 
                success: false,
                error: 'Script execution failed', 
                details: error.message
            };
            console.log(JSON.stringify(errorResult));
            process.exit(1);
        });
}

module.exports = { scrapeActiveChatContent };