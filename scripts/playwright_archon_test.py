#!/usr/bin/env python3
"""
Playwright Archon Web Interface Test
Access and interact with Archon dashboard at http://localhost:3737/

This script demonstrates:
- Playwright browser automation
- Connection testing and error handling
- Screenshot capture for debugging
- Element discovery and interaction
- Service availability detection
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError

class ArchonPlaywrightTester:
    """Playwright-based tester for Archon web interface"""
    
    def __init__(self):
        self.base_url = "http://localhost:8151"
        self.screenshots_dir = Path("data/playwright_screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
    async def test_archon_access(self):
        """Test access to Archon web interface"""
        
        print("🎭 PLAYWRIGHT ARCHON WEB INTERFACE TEST")
        print("=" * 60)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: {self.base_url}")
        print()
        
        async with async_playwright() as p:
            try:
                # Launch browser
                print("🚀 Launching browser...")
                browser = await p.chromium.launch(
                    headless=False,  # Show browser for demonstration
                    slow_mo=1000     # Slow down for visibility
                )
                
                # Create context and page
                context = await browser.new_context()
                page = await context.new_page()
                
                # Set up console and error logging
                page.on("console", lambda msg: print(f"🖥️  Console: {msg.text}"))
                page.on("pageerror", lambda err: print(f"❌ Page Error: {err}"))
                
                print("✅ Browser launched successfully")
                
                # Attempt to navigate to Archon
                print(f"\n🔗 Navigating to {self.base_url}...")
                
                try:
                    # Wait for navigation with timeout
                    await page.goto(self.base_url, timeout=10000, wait_until="domcontentloaded")
                    
                    print("✅ Successfully connected to Archon web interface!")
                    
                    # Take screenshot of successful connection
                    screenshot_path = self.screenshots_dir / f"archon_success_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    await page.screenshot(path=str(screenshot_path))
                    print(f"📸 Screenshot saved: {screenshot_path}")
                    
                    # Get page title
                    title = await page.title()
                    print(f"📑 Page Title: {title}")
                    
                    # Discover Archon UI elements
                    await self._discover_archon_elements(page)
                    
                    # Test navigation
                    await self._test_archon_navigation(page)
                    
                except TimeoutError:
                    print("⚠️  Connection timeout - Archon web interface not responding")
                    await self._handle_connection_failure(page)
                    
                except Exception as nav_error:
                    print(f"❌ Navigation failed: {nav_error}")
                    await self._handle_connection_failure(page)
                
                # Keep browser open for inspection
                print(f"\n⏸️  Browser will remain open for 30 seconds for inspection...")
                await asyncio.sleep(30)
                
                await browser.close()
                print("✅ Browser closed")
                
            except Exception as e:
                print(f"❌ Browser launch failed: {e}")
                return False
    
    async def _discover_archon_elements(self, page):
        """Discover and analyze Archon UI elements"""
        
        print(f"\n🔍 DISCOVERING ARCHON UI ELEMENTS:")
        
        try:
            # Look for common Archon elements
            archon_selectors = [
                {"name": "Main Navigation", "selector": "nav, [role='navigation']"},
                {"name": "Dashboard Header", "selector": "h1, .dashboard-header, [data-testid='header']"},
                {"name": "Knowledge Base Section", "selector": "[data-testid='knowledge'], .knowledge-base, .kb-section"},
                {"name": "Projects Section", "selector": "[data-testid='projects'], .projects, .project-section"},
                {"name": "Settings Link", "selector": "[data-testid='settings'], .settings, a[href*='settings']"},
                {"name": "MCP Dashboard", "selector": "[data-testid='mcp'], .mcp-dashboard, .mcp-section"},
                {"name": "Status Indicators", "selector": ".status, .health, [data-testid='status']"}
            ]
            
            elements_found = 0
            
            for element_info in archon_selectors:
                try:
                    elements = await page.query_selector_all(element_info["selector"])
                    if elements:
                        elements_found += 1
                        print(f"   ✅ {element_info['name']}: {len(elements)} element(s) found")
                        
                        # Get text content of first element
                        if elements:
                            text = await elements[0].text_content()
                            if text and text.strip():
                                print(f"      📝 Content: {text.strip()[:100]}...")
                    else:
                        print(f"   ❌ {element_info['name']}: Not found")
                        
                except Exception as e:
                    print(f"   ⚠️  {element_info['name']}: Error checking - {e}")
            
            print(f"\n📊 Discovery Summary: {elements_found}/{len(archon_selectors)} element types found")
            
        except Exception as e:
            print(f"❌ Element discovery failed: {e}")
    
    async def _test_archon_navigation(self, page):
        """Test Archon navigation and interactions"""
        
        print(f"\n🧪 TESTING ARCHON NAVIGATION:")
        
        try:
            # Test common navigation patterns
            navigation_tests = [
                {"name": "Knowledge Base Link", "selector": "a[href*='knowledge'], .knowledge-link"},
                {"name": "Projects Link", "selector": "a[href*='projects'], .projects-link"},
                {"name": "Settings Link", "selector": "a[href*='settings'], .settings-link"},
                {"name": "MCP Dashboard Link", "selector": "a[href*='mcp'], .mcp-link"}
            ]
            
            for test in navigation_tests:
                try:
                    element = await page.query_selector(test["selector"])
                    if element:
                        print(f"   ✅ {test['name']}: Available for interaction")
                        
                        # Check if clickable
                        is_visible = await element.is_visible()
                        is_enabled = await element.is_enabled()
                        print(f"      👁️  Visible: {is_visible}, Enabled: {is_enabled}")
                    else:
                        print(f"   ❌ {test['name']}: Not found")
                        
                except Exception as e:
                    print(f"   ⚠️  {test['name']}: Error testing - {e}")
            
            # Test page responsiveness
            await self._test_page_responsiveness(page)
            
        except Exception as e:
            print(f"❌ Navigation testing failed: {e}")
    
    async def _test_page_responsiveness(self, page):
        """Test Archon page responsiveness"""
        
        print(f"\n📱 TESTING PAGE RESPONSIVENESS:")
        
        try:
            # Test different viewport sizes
            viewports = [
                {"name": "Desktop", "width": 1920, "height": 1080},
                {"name": "Tablet", "width": 768, "height": 1024},
                {"name": "Mobile", "width": 375, "height": 667}
            ]
            
            for viewport in viewports:
                await page.set_viewport_size(viewport["width"], viewport["height"])
                await asyncio.sleep(1)  # Wait for responsive layout
                
                # Take screenshot
                screenshot_path = self.screenshots_dir / f"archon_{viewport['name'].lower()}_{datetime.now().strftime('%H%M%S')}.png"
                await page.screenshot(path=str(screenshot_path))
                
                print(f"   📸 {viewport['name']} ({viewport['width']}x{viewport['height']}): Screenshot saved")
                
        except Exception as e:
            print(f"❌ Responsiveness testing failed: {e}")
    
    async def _handle_connection_failure(self, page):
        """Handle connection failure scenarios"""
        
        print(f"\n🔧 ANALYZING CONNECTION FAILURE:")
        
        # Take screenshot of error state
        screenshot_path = self.screenshots_dir / f"archon_connection_failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await page.screenshot(path=str(screenshot_path))
        print(f"📸 Error screenshot saved: {screenshot_path}")
        
        # Check page content for error information
        try:
            page_content = await page.content()
            if "ERR_CONNECTION_REFUSED" in page_content:
                print("   ❌ Connection refused - Service not running")
            elif "ERR_NAME_NOT_RESOLVED" in page_content:
                print("   ❌ DNS resolution failed")
            elif "timeout" in page_content.lower():
                print("   ❌ Connection timeout")
            else:
                print("   ❓ Unknown connection error")
                
        except Exception as e:
            print(f"   ⚠️  Could not analyze error page: {e}")
        
        # Provide service startup guidance
        print(f"\n💡 ARCHON SERVICE STARTUP GUIDANCE:")
        print(f"   1. Ensure Docker is installed and running")
        print(f"   2. Navigate to archon-mcp directory: cd archon-mcp")
        print(f"   3. Setup environment: cp .env.example .env")
        print(f"   4. Configure Supabase credentials in .env")
        print(f"   5. Start services: docker-compose up --build -d")
        print(f"   6. Wait for services to initialize (2-3 minutes)")
        print(f"   7. Access Archon UI at: http://localhost:3737")

async def main():
    """Main execution"""
    
    tester = ArchonPlaywrightTester()
    await tester.test_archon_access()
    
    print(f"\n📋 TEST COMPLETION SUMMARY:")
    print(f"   🎯 Target URL: http://localhost:3737")
    print(f"   📁 Screenshots: {tester.screenshots_dir}")
    print(f"   🔧 Status: Connection test completed")
    print(f"   💡 Next Steps: Start Archon services if connection failed")

if __name__ == "__main__":
    asyncio.run(main())
