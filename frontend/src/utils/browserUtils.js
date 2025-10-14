/**
 * Utility funkcije za browser operacije
 */

/**
 * Otvara URL u external browser-u (Chrome) umesto u trenutnom Simple Browser-u
 * @param {string} url - URL za otvaranje
 */
export async function openInExternalBrowser(url) {
    try {
        // PRIORITET: Pokušaj da otvoris tab u Chrome debugger-u (port 9222)
        console.log('Pokušavam da otvorim URL u Chrome debugger-u:', url);
        
        const chromeResponse = await fetch(`http://localhost:9222/json/new?${encodeURIComponent(url)}`, {
            method: 'PUT'
        });
        
        if (chromeResponse.ok) {
            const tabInfo = await chromeResponse.json();
            console.log('URL uspešno otvoren u Chrome debugger-u:', tabInfo);
            
            // Pokušaj da aktiviraš tab
            try {
                await fetch(`http://localhost:9222/json/activate/${tabInfo.id}`, {
                    method: 'POST'
                });
                console.log('Tab aktiviran u Chrome-u');
                
                // Pokušaj da dovedemo Chrome u fokus (ako je moguće)
                if (window.focus) {
                    setTimeout(() => {
                        // Signal za fokusiranje - možda pomaže
                        console.log('Pokušavam da fokusiram Chrome window');
                    }, 200);
                }
                
            } catch (activateError) {
                console.log('Nije moguće aktivirati tab:', activateError);
            }
            
            return;
        } else {
            console.log('Chrome debugger odgovor:', chromeResponse.status, chromeResponse.statusText);
        }
    } catch (chromeError) {
        console.log('Chrome debugger nije dostupan na portu 9222:', chromeError.message);
    }

    try {
        // Metod 2: Pokušaj da koristi VS Code API ako je dostupan
        console.log('Chrome debugger fallback - pokušavam VS Code API metod');
        if (typeof window !== 'undefined' && window.parent !== window) {
            // Ako smo u iframe-u (Simple Browser), pošalji poruku parent window-u
            console.log('Šaljem poruku parent window-u za external opening');
            window.parent.postMessage({
                type: 'openExternal',
                url: url
            }, '*');
            
            // Fallback after small delay
            setTimeout(() => {
                console.log('VS Code API timeout - pokušavam window.open fallback');
                // Metod 3: Koristi window.open sa specific target
                const newWindow = window.open('', '_system');
                if (newWindow) {
                    newWindow.location = url;
                } else {
                    console.log('window.open failed - pokušavam invisible link');
                    // Metod 4: Kreiraj invisible link i klikni
                    const link = document.createElement('a');
                    link.href = url;
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                    
                    // Dodaj link u DOM, klikni ga, i ukloni
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }
            }, 100);
        } else {
            // Normalni browser - koristi window.open
            console.log('Normalni browser - koristim window.open');
            window.open(url, '_blank', 'noopener,noreferrer');
        }
    } catch (error) {
        console.error('Greška pri otvaranju linka:', error);
        
        // Ultimate fallback - kopiraj URL u clipboard
        if (navigator.clipboard) {
            navigator.clipboard.writeText(url).then(() => {
                alert(`Chrome debugger (port 9222) nije dostupan.\nURL kopiran u clipboard: ${url}\nMolimo vas da ga paste-ujete u Chrome sa debug portom.`);
            });
        } else {
            alert(`Chrome debugger nije dostupan.\nMolimo vas da otvorite ovaj URL u Chrome:\n${url}`);
        }
    }
}

/**
 * Kopiraj tekst u clipboard
 * @param {string} text - Tekst za kopiranje
 * @returns {Promise<boolean>} - Da li je kopiranje uspešno
 */
export async function copyToClipboard(text) {
    try {
        if (navigator.clipboard) {
            await navigator.clipboard.writeText(text);
            return true;
        } else {
            // Fallback za starije browser-e
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            const result = document.execCommand('copy');
            document.body.removeChild(textArea);
            return result;
        }
    } catch (error) {
        console.error('Greška pri kopiranju:', error);
        return false;
    }
}

/**
 * Proveri da li smo u Simple Browser-u
 * @returns {boolean}
 */
export function isInSimpleBrowser() {
    try {
        return window.parent !== window && 
               window.location.hostname === 'localhost' &&
               document.referrer.includes('vscode');
    } catch (error) {
        return false;
    }
}