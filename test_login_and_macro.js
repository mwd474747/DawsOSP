const puppeteer = require('puppeteer');

async function testMacroCycles() {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    try {
        const page = await browser.newPage();
        
        // Navigate to login page
        console.log('Navigating to login page...');
        await page.goto('http://localhost:5000/macro-cycles');
        
        // Wait for login form
        await page.waitForSelector('input[type="password"]');
        
        // Fill in password (email is pre-filled)
        console.log('Filling in password...');
        await page.type('input[type="password"]', 'Password123');
        
        // Click Sign In button
        console.log('Clicking Sign In...');
        await page.click('button:has-text("SIGN IN")');
        
        // Wait for navigation to complete
        await page.waitForNavigation({ waitUntil: 'networkidle0' });
        
        // Check if we're on the macro cycles page
        const url = page.url();
        console.log('Current URL:', url);
        
        // Wait for macro cycles content to load
        await page.waitForTimeout(3000);
        
        // Get page content
        const content = await page.content();
        const hasSTDC = content.includes('STDC') || content.includes('Short-Term');
        const hasLTDC = content.includes('LTDC') || content.includes('Long-Term');
        const hasEmpire = content.includes('Empire');
        const hasCivil = content.includes('Civil');
        
        console.log('Page has STDC content:', hasSTDC);
        console.log('Page has LTDC content:', hasLTDC);  
        console.log('Page has Empire content:', hasEmpire);
        console.log('Page has Civil content:', hasCivil);
        
        // Take screenshot
        await page.screenshot({ path: 'macro_cycles_page.png', fullPage: true });
        console.log('Screenshot saved as macro_cycles_page.png');
        
    } catch (error) {
        console.error('Error:', error);
    } finally {
        await browser.close();
    }
}

testMacroCycles();
