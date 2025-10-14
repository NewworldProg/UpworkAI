#!/usr/bin/env node
/**
 * Upwork Message Extractor - Scraper for incoming messages/notifications
 * Extracts messages from Upwork notification panel and conversations
 */
// in variable put puppeteerCore library
const puppeteerCore = require('puppeteer-core');
// in variable put fs library with promises
const fs = require('fs').promises;
// in variable put path library
const path = require('path');
// Add http module for API calls
const http = require('http');

//================================ 🚀 Direct Database Save Function ==============================

async function saveMessagesToDatabase(messagesData, pageInfo) {
    try {
        if (!messagesData || messagesData.length === 0) {
            console.log('⚠️ No messages to save');
            return { success: true, saved: 0 };
        }

        const postData = JSON.stringify({
            messages: messagesData,
            pageInfo: pageInfo,
            timestamp: new Date().toISOString()
        });

        const options = {
            hostname: 'localhost',
            port: 8000,
            path: '/api/messages/save-messages/',
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
                        const response = JSON.parse(data);
                        console.log(`✅ Successfully saved ${response.data?.saved_messages || messagesData.length} messages to database`);
                        resolve({ success: true, response: response });
                    } else {
                        console.error(`❌ API request failed with status ${res.statusCode}: ${data}`);
                        reject(new Error(`HTTP ${res.statusCode}: ${data}`));
                    }
                });
            });

            req.on('error', (err) => {
                console.error('❌ API request error:', err.message);
                reject(err);
            });

            req.write(postData);
            req.end();
        });

    } catch (error) {
        console.error('❌ Could not save messages to database:', error.message);
        throw error;
    }
}

//================================ 🗨️ Message Scraper Functions ==============================

async function extractMessagesFromLoggedInChrome() {
    // ====================== 🧱🔨 connect to Chrome and extract pages ======================
    
    // Retry logic for Chrome connection
    let browser;
    for (let attempt = 1; attempt <= 3; attempt++) {
        try {
            console.log(`🔗 Connecting to your logged-in Chrome for messages... (attempt ${attempt}/3)`);

            // in variable browser input Promise class to call function and wait for first to resolve
            browser = await Promise.race([
            // inside browser input object of puppeteerCore call function .connect()
            puppeteerCore.connect({
                // params for
                // browserUrl - the URL of the Chrome instance to connect to
                browserURL: 'http://localhost:9222',
                // defaultViewport - the default viewport size for the browser
                defaultViewport: null,
                // timeout - the connection timeout in milliseconds
                timeout: 30000
            }),
            // if not connected in 30 seconds, reject with error
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Chrome connection timeout after 30 seconds')), 30000)
            )
            ]);
            break; // Connection successful, exit retry loop
        } catch (connectionError) {
            console.log(`❌ Connection attempt ${attempt} failed: ${connectionError.message}`);
            if (attempt === 3) {
                throw connectionError; // Re-throw error after all attempts failed
            }
            console.log('⏳ Waiting 2 seconds before retry...');
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }

    try {
        // in variable pages put browser.pages() input all open pages/tabs in the browser
        const pages = await browser.pages();
        console.log(`📄 Found ${pages.length} open tabs`);
        
        // variable to hold the target page
        let targetPage = null;
        
        // Function to check if URL is a messages page
        const isMessagesPage = (url) => {
            return url.includes('upwork.com') && 
                (url.includes('/ab/messages') ||
                 url.includes('/messages/rooms') ||
                 url.includes('/messages/') ||
                 url.includes('/nx/message'));
        };
        
        // List all tabs for debugging
        for (const [index, page] of pages.entries()) {
            try {
                const url = page.url();
                const title = await page.title();
                console.log(`Tab ${index}: ${title} - ${url}`);
            } catch (e) {
                console.log(`Tab ${index}: Error reading tab - ${e.message}`);
            }
        }
        
        // First try to find active messages page
        for (const page of pages) {
            try {
                const url = page.url();
                console.log(`🔍 Checking page: ${url}`);
                
                const isVisible = await page.evaluate(() => !document.hidden);
                console.log(`📋 Page visible: ${isVisible}`);
                
                if (isVisible && isMessagesPage(url)) {
                    targetPage = page;
                    console.log('✅ Found active Upwork messages tab');
                    break;
                }
            } catch (e) {
                console.log(`⚠️ Error checking page: ${e.message}`);
            }
        }
        
        // If no active messages page, find any messages page
        if (!targetPage) {
            for (const page of pages) {
                try {
                    const url = page.url();
                    if (isMessagesPage(url)) {
                        targetPage = page;
                        console.log('✅ Found Upwork messages tab (not active)');
                        break;
                    }
                } catch (e) {
                    // Skip if can't get URL
                }
            }
        }
        
        // If still no messages page, use any Upwork page as fallback
        if (!targetPage) {
            targetPage = pages.find(page => page.url().includes('upwork.com'));
            if (targetPage) {
                console.log('⚠️ Using fallback Upwork tab (not a messages page)');
            }
        }
        
        // If still no Upwork page, use the most recent tab
        if (!targetPage) {
            targetPage = pages[pages.length - 1];
            console.log('⚠️ No Upwork page found, using most recent tab');
        } else {
            console.log('✅ Found Upwork page: ' + targetPage.url());
        }

        // Add progress tracking
        console.log('📊 Starting message extraction process...');
        const startTime = Date.now();

        //======================= 🛸💬 message extraction ======================
        
        // inside messages variable input data from a page with upwork messages targetPage.evaluate()
        const messages = await targetPage.evaluate(() => {
            // array to store extracted messages
            const messageList = [];
            
            // inside existingId variable store elements of message with unique ID
            function generateMessageId(element, index) {
                // Try to find existing ID in element
                const existingId = element.getAttribute('data-message-id') || 
                                  element.getAttribute('data-id') || 
                                  element.getAttribute('id');
                // If existing ID is found, use it
                if (existingId) {
                    return `upwork_${existingId}`;
                }

                // if no existing ID fallback to hash-based ID

                // store content and timestamp of messages in variables
                const content = element.textContent?.trim() || ''; // content of the message
                const timestamp = extractTimestamp(element) || Date.now(); // and timestamp 
                // store content and timestamp inside hash variable
                // with simpleHash function
                const hash = simpleHash(content + timestamp);
                // return unique message ID
                return `msg_${hash}_${index}`;
            }

            // Helper function to generate chat URL
            function generateChatUrl(element) {
                // Try to find chat link in element
                const linkElement = element.querySelector('a[href*="/messages/"]') ||
                                   element.querySelector('a[href*="/conversation/"]') ||
                                   element.closest('a[href*="/messages/"]') ||
                                   element.closest('a[href*="/conversation/"]');
                
                if (linkElement) {
                    return linkElement.href;
                }
                
                // else try to construct URL from conversation ID
                const conversationId = extractConversationId(element);
                if (conversationId) {
                    // Return API endpoint instead of direct Upwork URL
                    return `/api/upwork-messages/chrome/open-message/?conversation_id=${conversationId}`;
                }
                
                return '';
            }

            // Helper function to create simple hash
            function simpleHash(str) {
                let hash = 0;
                // loop through each character in the string and code it into the hash
                for (let i = 0; i < str.length; i++) {
                    const char = str.charCodeAt(i);
                    hash = ((hash << 5) - hash) + char;
                    hash = hash & hash; // Convert to 32-bit integer
                }
                return Math.abs(hash).toString(36);
            }
            
            // messageSelectors array to store CSS selectors for message elements
            const messageSelectors = [
                // Glavni room list items u sidebar-u
                '.room-list-item',
                'a.room-list-item',
                '.rooms-panel-room-list .room-list-item',
                
                // Story/message items u chat-u
                '.up-d-story-item',
                '.story-list .up-d-story-item',
                
                // Fallback selektori
                '[data-test="room-list-item"]',
                '[data-test="story-container"]',
                '[class*="room-list-item"]',
                '[class*="story-item"]',
                
                // Upwork-specific message containers
                '.air-card', // Common Upwork card component
                '.up-card'   // Another common component
            ];

            // put selectors inside selector variable
            for (const selector of messageSelectors) {
                // inside elements variable put all elements found with the selector
                const elements = document.querySelectorAll(selector);
                // if elements found, log the count
                if (elements.length > 0) {
                    console.log(`🎯 Found ${elements.length} elements with selector: ${selector}`);
                    // Loop through found elements and give them index
                    elements.forEach((element, index) => {
                        try {
                            // if found element extract
                            // message data with proper IDs
                            const messageData = {
                                // Generate 
                                // id
                                // timestamp
                                // selector_used
                                id: generateMessageId(element, index),
                                timestamp: extractTimestamp(element) || new Date().toISOString(),
                                selector_used: selector,
                                
                                // conversation ID for chat grouping
                                conversationId: extractConversationId(element) || `chat_${Date.now()}`,
                                
                                // Message content
                                sender: extractSender(element),
                                content: element.textContent?.trim() || '',
                                text: element.textContent?.trim() || '', // For backward compatibility
                                preview: extractPreview(element),
                                
                                // Message status
                                isRead: extractReadStatus(element),
                                isUnread: !extractReadStatus(element),
                                
                                // Chat URL generation
                                chatUrl: generateChatUrl(element),
                                
                                // Technical data
                                html: element.outerHTML.substring(0, 500) + '...',
                                classes: element.className,
                                attributes: Array.from(element.attributes).map(attr => `${attr.name}="${attr.value}"`).join(' ')
                            };
                            
                            // Only add if the length of the text is more than 10 characters
                            if (messageData.text.length > 10) {
                                messageList.push(messageData);
                            }
                        } catch (err) {
                            console.error('Error extracting message data:', err);
                        }
                    });
                    
                    // If we found messages with this selector, break
                    if (messageList.length > 0) {
                        break;
                    }
                }
            }

            // Helper functions for extraction
            function extractSender(element) {
                const senderSelectors = [
                    '.story-header-name',       // Main sender name in story header
                    '.up-d-story-header-name',  // Upwork story header name
                    '.story-inner .sender-name', // Sender name in story inner
                    '.user-name',               // Upwork user name class
                    '.room-list-item-base-text.item-title', // Room title
                    '[data-test="room-name"]',  // Data test attribute
                    '.profile-title',           // Profile title
                    '.sender-name',
                    '.client-name', 
                    '.freelancer-name',
                    '[class*="name"]',          // This worked in debug!
                    'h3', 'h4', 'h5',
                    '.title'
                ];
                // for each selector in senderSelectors array
                // return text content if found
                for (const sel of senderSelectors) {
                    const senderEl = element.querySelector(sel);  // Fixed: was 'seal'
                    if (senderEl && senderEl.textContent.trim()) {
                        return senderEl.textContent.trim();
                    }
                }
                return 'Unknown';
            }

            // Extract a short preview of the message content
            function extractPreview(element) {
                const previewSelectors = [
                    '.story-message .up-d-message',    // Specific story message content
                    '.up-d-message',                   // Upwork message content
                    '.story-message',                  // Story message container 
                    '.story-inner .story-section',     // Story section content
                    '.room-list-item-story',           // Room story content
                    '[data-test="story-message"]',     // Data test attribute
                    '.message-content',                // Generic message content
                    '.story-content',                  // Story content
                    '.message-preview',
                    '.preview-text',
                    '.summary',
                    'p:first-of-type',
                    '.description'
                ];
                
                for (const sel of previewSelectors) {
                    const previewEl = element.querySelector(sel);
                    if (previewEl && previewEl.textContent.trim()) {
                        // Clean up the text - remove extra whitespace and buttons
                        let text = previewEl.textContent.trim()
                            .replace(/\s+/g, ' ')                    // Normalize whitespace
                            .replace(/Reply to message.*/g, '')     // Remove action buttons
                            .replace(/Favorite message.*/g, '')     // Remove action buttons
                            .replace(/More options.*/g, '')         // Remove action buttons
                            .replace(/Editing is only.*/g, '')      // Remove editing notice
                            .trim();
                        return text.substring(0, 200);
                    }
                }
                return '';
            }
            // Extract timestamp from element
            function extractTimestamp(element) {
                const timeSelectors = [
                    '.header-timestamp',           // Day header timestamp (worked in debug!)
                    '.story-timestamp',            // Upwork story timestamp
                    '.up-d-story-time',           // Story time
                    '.story-time',                // Story time variant
                    '.timestamp.text-base-sm',    // Room timestamp
                    '[class*="time"]',            // Worked in debug!
                    'time',
                    '.timestamp',
                    '.time',
                    '[datetime]',
                    '.date'
                ];
                
                for (const sel of timeSelectors) {
                    const timeEl = element.querySelector(sel);
                    if (timeEl) {
                        let timeText = timeEl.getAttribute('datetime') || timeEl.textContent.trim();
                        // Clean up timestamp text
                        timeText = timeText
                            .replace(/\s+/g, ' ')           // Normalize whitespace
                            .replace(/^\s*|\s*$/g, '')      // Trim
                            .split(/\s+/)                   // Split by whitespace
                            .filter(part => part.match(/\d/)) // Keep parts with numbers
                            .join(' ');                     // Rejoin
                        return timeText;
                    }
                }
                return '';
            }
            /// Extract read/unread status
            function extractReadStatus(element) {
                // Check for unread indicators
                const unreadIndicators = [
                    '.unread',
                    '.new-message',
                    '[class*="unread"]',
                    '.notification-dot'
                ];
                
                for (const sel of unreadIndicators) {
                    if (element.querySelector(sel)) {
                        return false; // Has unread indicator
                    }
                }
                return true; // Assume read if no unread indicator
            }
            // Extract conversation/room ID
            function extractConversationId(element) {
                // Try to find conversation/room ID from data attributes
                const idAttributes = ['data-conversation-id', 'data-room-id', 'data-id', 'id'];
                
                for (const attr of idAttributes) {
                    const value = element.getAttribute(attr);
                    if (value) {
                        return value;
                    }
                }
                
                // Try to extract from href links - Upwork uses room_ prefix
                const linkElement = element.querySelector('a[href*="/messages/"], a[href*="/conversations/"], a[href*="/rooms/"]') || 
                                   element.closest('a[href*="/messages/"], a[href*="/conversations/"], a[href*="/rooms/"]');
                
                if (linkElement) {
                    const href = linkElement.getAttribute('href');
                    // Match Upwork patterns like room_xxxxx
                    const matches = href.match(/room_([a-f0-9]+)|(?:messages|conversations)\/([^\/\?]+)/);
                    if (matches) {
                        return matches[1] || matches[2]; // Return the room ID without prefix
                    }
                }
                
                // Check for ID in element itself (like room_xxxxx)
                const elementId = element.id;
                if (elementId && elementId.startsWith('room_')) {
                    return elementId.substring(5); // Remove 'room_' prefix
                }
                
                // Try to extract from URL patterns in onclick or other attributes
                const clickHandler = element.getAttribute('onclick');
                if (clickHandler) {
                    const matches = clickHandler.match(/(?:conversation|room|message)[:=]\s*['"]([^'"]+)['"]/i);
                    if (matches && matches[1]) {
                        return matches[1];
                    }
                }
                
                // Fallback: generate from sender + timestamp
                const sender = extractSender(element);
                const timestamp = extractTimestamp(element);
                if (sender && timestamp) {
                    return `conv_${simpleHash(sender + timestamp)}`;
                }
                
                return '';
            }

            return messageList;
        });

        console.log(`📬 Extracted ${messages.length} messages`);
        
        const extractionTime = Date.now() - startTime;
        console.log(`⏱️ Extraction completed in ${extractionTime}ms`);

        // Close browser connection
        await browser.disconnect();

        return {
            messages,
            pageInfo: {
                url: targetPage.url(),
                timestamp: new Date().toISOString(),
                totalMessages: messages.length,
                source: 'logged-in-chrome'
            }
        };

    } catch (error) {
        console.error('❌ Message extraction failed:', error.message);
        return { messages: [], pageInfo: { error: error.message } };
    }
}

//================================ 📂 File Operations (DEPRECATED - Use API instead) ==============================

async function saveMessages(messages, pageInfo) {
    console.log('⚠️ saveMessages function is deprecated. Use saveMessagesToDatabase instead.');
    return await saveMessagesToDatabase(messages, pageInfo);
}

//================================ 🚀 Main Execution ==============================

async function main() {
    try {
        console.log('🗨️ Starting Upwork Message Extraction...');
        
        const result = await extractMessagesFromLoggedInChrome();
        
        if (result.messages.length > 0) {
            await saveMessages(result.messages, result.pageInfo);
            console.log('✅ Message extraction completed successfully!');
        } else {
            console.log('⚠️ No messages found');
        }
        
        return result;
        
    } catch (error) {
        console.error('❌ Message extraction failed:', error.message);
        
        // Don't create JSON files - just return error result
        const emptyResult = { messages: [], pageInfo: { error: error.message } };
        return emptyResult;
    }
}

// Export functions for use in other modules
module.exports = { extractMessagesFromLoggedInChrome, saveMessages, saveMessagesToDatabase, main };

// Run if called directly
if (require.main === module) {
    main();
}