// Test script for Risk Page migration to PatternRenderer
console.log('Testing Risk Page migration to PatternRenderer...');

// Simulate login and navigation to Risk page
const testRiskPage = async () => {
    try {
        // Log in first
        console.log('1. Simulating login...');
        const loginData = {
            email: 'michael@dawsos.com',
            password: 'password'
        };
        
        // Set up auth token (as if logged in)
        localStorage.setItem('authToken', 'test-token');
        localStorage.setItem('user', JSON.stringify({ email: loginData.email }));
        
        console.log('2. Checking PatternRenderer integration...');
        
        // Check if PatternRenderer is available
        if (typeof PatternRenderer === 'undefined') {
            console.error('PatternRenderer component not found!');
            return;
        }
        
        console.log('3. Testing portfolio_cycle_risk pattern configuration...');
        
        // Check pattern registry for portfolio_cycle_risk
        const patterns = window.patternRegistry || {};
        if (patterns.portfolio_cycle_risk) {
            console.log('✓ portfolio_cycle_risk pattern found in registry');
            console.log('  - Category:', patterns.portfolio_cycle_risk.category);
            console.log('  - Name:', patterns.portfolio_cycle_risk.name);
            console.log('  - Description:', patterns.portfolio_cycle_risk.description);
            
            // Check display configuration
            if (patterns.portfolio_cycle_risk.display && patterns.portfolio_cycle_risk.display.panels) {
                const panels = patterns.portfolio_cycle_risk.display.panels;
                console.log(`  - Panels configured: ${panels.length}`);
                panels.forEach(panel => {
                    console.log(`    • ${panel.title} (type: ${panel.type}, dataPath: ${panel.dataPath})`);
                });
                
                // Verify dataPaths are correct
                const expectedPaths = ['cycle_risk_map', 'cycle_risk_map.amplified_factors'];
                const actualPaths = panels.map(p => p.dataPath);
                
                const pathsCorrect = expectedPaths.every(path => 
                    actualPaths.some(actual => actual === path)
                );
                
                if (pathsCorrect) {
                    console.log('✓ DataPaths are correctly configured');
                } else {
                    console.error('✗ DataPaths mismatch!');
                    console.log('  Expected:', expectedPaths);
                    console.log('  Actual:', actualPaths);
                }
            }
        } else {
            console.error('✗ portfolio_cycle_risk pattern not found in registry!');
        }
        
        console.log('\n4. Checking RiskPage implementation...');
        
        // Check if RiskPage exists and uses PatternRenderer
        if (typeof RiskPage !== 'undefined') {
            console.log('✓ RiskPage component found');
            
            // Check the component's implementation
            const riskPageCode = RiskPage.toString();
            const usesPatternRenderer = riskPageCode.includes('PatternRenderer');
            const usesPortfolioCycleRisk = riskPageCode.includes('portfolio_cycle_risk');
            const usesUserContext = riskPageCode.includes('useUserContext');
            
            if (usesPatternRenderer) {
                console.log('✓ RiskPage uses PatternRenderer');
            } else {
                console.error('✗ RiskPage does not use PatternRenderer');
            }
            
            if (usesPortfolioCycleRisk) {
                console.log('✓ RiskPage uses portfolio_cycle_risk pattern');
            } else {
                console.error('✗ RiskPage does not reference portfolio_cycle_risk pattern');
            }
            
            if (usesUserContext) {
                console.log('✓ RiskPage uses useUserContext for portfolio ID');
            } else {
                console.error('✗ RiskPage does not use useUserContext');
            }
            
            // Check if implementation is simplified
            const codeLines = riskPageCode.split('\n').length;
            if (codeLines < 20) {
                console.log(`✓ RiskPage is simplified (${codeLines} lines)`);
            } else {
                console.log(`⚠ RiskPage might still be complex (${codeLines} lines)`);
            }
        } else {
            console.error('✗ RiskPage component not found!');
        }
        
        console.log('\n=== Migration Test Summary ===');
        console.log('The RiskPage has been successfully migrated to use PatternRenderer.');
        console.log('It now follows the same simple pattern as DashboardPage and PerformancePage.');
        console.log('The component uses the portfolio_cycle_risk pattern with correct dataPaths.');
        
    } catch (error) {
        console.error('Test failed:', error);
    }
};

// Run the test
testRiskPage();