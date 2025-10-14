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
        console.log(`📄 Found ${pages.length} open tabs`);        // make dict to store page URLs and titles
        // index key and page info as value
        for (const [index, page] of pages.entries()) {
            try {
                const url = page.url();
                const title = await page.title();
                console.log(`Tab ${index}: ${title} - ${url}`);
            } catch (e) {
                console.log(`Tab ${index}: [Error getting info]`);
            }
        }

        let targetPage = null;
        
        // for loop to Find active Upwork page
        for (const page of pages) {
            try {
                // in variable url put page.url()
                const url = page.url();
                console.log(`🔍 Checking page: ${url}`);
                // if in url there is 'upwork.com'
                if (url.includes('upwork.com')) {
                    const isVisible = await page.evaluate(() => !document.hidden);
                    console.log(`📋 Page visible: ${isVisible}`);
                    
                    if (isVisible) {
                        targetPage = page;
                        console.log('✅ Found active Upwork tab');
                        break;
                    }
                }
            } catch (e) {
                console.log(`⚠️ Error checking page: ${e.message}`);
                continue;
            }
        }

        // If no active Upwork page, find any Upwork page
        if (!targetPage) {
            targetPage = pages.find(page => page.url().includes('upwork.com'));
        }

        if (!targetPage) {
            console.log('⚠️ No Upwork page found');
            return { messages: [], pageInfo: { error: 'No Upwork page found' } };
        }

        console.log('✅ Found Upwork page:', targetPage.url());

        // Add progress tracking
        console.log('📊 Starting message extraction process...');
        const startTime = Date.now();
// ====================== 🧱🔨 connect to Chrome and extract pages ======================

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
                    '.user-name',           // Upwork user name class
                    '.room-list-item-base-text.item-title', // Room title
                    '[data-test="room-name"]', // Data test attribute
                    '.profile-title',       // Profile title
                    '.sender-name',
                    '.client-name', 
                    '.freelancer-name',
                    '[class*="name"]',
                    'h3', 'h4', 'h5',
                    '.title'
                ];
                // for each selector in senderSelectors array
                // return text content if found
                for (const sel of senderSelectors) {
                    const senderEl = element.querySelector(seal);
                    if (senderEl && senderEl.textContent.trim()) {
                        return senderEl.textContent.trim();
                    }
                }
                return 'Unknown';
            }

            // Extract a short preview of the message content
            function extractPreview(element) {
                const previewSelectors = [
                    '.up-d-message',        // Upwork message content
                    '.room-list-item-story', // Room story content
                    '.story-message .up-d-message', // Story message
                    '[data-test="story-message"]',
                    '.message-preview',
                    '.preview-text',
                    '.summary',
                    'p:first-of-type',
                    '.description'
                ];
                
                for (const sel of previewSelectors) {
                    const previewEl = element.querySelector(sel);
                    if (previewEl && previewEl.textContent.trim()) {
                        return previewEl.textContent.trim().substring(0, 200);
                    }
                }
                return '';
            }
            // Extract timestamp from element
            function extractTimestamp(element) {
                const timeSelectors = [
                    '.story-timestamp',     // Upwork story timestamp
                    '.timestamp.text-base-sm', // Room timestamp
                    'time',
                    '.timestamp',
                    '.time',
                    '[datetime]',
                    '.date'
                ];
                
                for (const sel of timeSelectors) {
                    const timeEl = element.querySelector(sel);
                    if (timeEl) {
                        return timeEl.getAttribute('datetime') || timeEl.textContent.trim();
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

//================================ 📂 File Operations ==============================

async function saveMessages(messages, pageInfo) {
    try {
        const dataDir = path.join(__dirname, '..', '..', '..', 'backend', 'notification_push', 'data');
        await fs.mkdir(dataDir, { recursive: true });
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `upwork_messages_${timestamp}.json`;
        const filepath = path.join(dataDir, filename);
        
        const data = {
            messages,
            pageInfo,
            extractedAt: new Date().toISOString()
        };
        
        await fs.writeFile(filepath, JSON.stringify(data, null, 2));
        console.log(`💾 Messages saved to: ${filepath}`);
        
        return filepath;
    } catch (error) {
        console.error('❌ Could not save messages:', error.message);
        throw error;
    }
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
        
        const emptyResult = { messages: [], pageInfo: { error: error.message } };
        const dataDir = path.join(__dirname, '..', '..', '..', 'backend', 'notification_push', 'data');
        
        try {
            await fs.mkdir(dataDir, { recursive: true });
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `upwork_messages_error_${timestamp}.json`;
            await fs.writeFile(path.join(dataDir, filename), JSON.stringify(emptyResult, null, 2));
        } catch (writeError) {
            console.error('❌ Could not save error result:', writeError.message);
        }
        
        return emptyResult;
    }
}

// Export functions for use in other modules
module.exports = { extractMessagesFromLoggedInChrome, saveMessages, main };

// Run if called directly
if (require.main === module) {
    main();
}