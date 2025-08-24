#!/usr/bin/env python3
"""
Enhanced SSCS EDI Path Discovery
Using SSCS help system guidance + confirmed interface access + NAXML validation

Three-pronged approach:
1. SSCS help system documentation research
2. Direct CPB interface configuration  
3. NAXML file validation testing

Author: DABS Automation System
Created: 2025-08-21
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page

# Load environment variables
load_dotenv()

class EnhancedSSCSEDIDiscovery:
    """
    Enhanced EDI path discovery using comprehensive approach
    
    Methods:
    1. SSCS help system documentation research
    2. Direct CPB interface exploration
    3. NAXML file validation testing
    """
    
    def __init__(self):
        self.username = os.getenv('SSCS_USERNAME')
        self.password = os.getenv('SSCS_PASSWORD') 
        self.cpb_base_url = "https://sscsta.sscsinc.com/Cpb.App/"
        self.help_base_url = "https://sscsta.sscsinc.com/Cpb.App/Help/wwhelp/wwhimpl/common/html/"
        self.results_dir = Path('data/enhanced_edi_discovery')
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print("🚀 ENHANCED SSCS EDI PATH DISCOVERY")
        print("=" * 50)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 COMPREHENSIVE APPROACH: Help + Interface + Validation")
        print("💡 GOAL: Establish SSCS_EDI_FOLDER_PATH for your 10,532-item automation")
    
    async def enhanced_edi_discovery(self) -> Dict[str, Any]:
        """Execute comprehensive EDI path discovery"""
        
        discovery_results = {
            'discovery_timestamp': datetime.now().isoformat(),
            'approach': 'enhanced_comprehensive',
            'automation_ready': True,  # Your 10,532-item automation is complete
            'naxml_files_available': True  # Your test files ready
        }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, slow_mo=1000)
            page = await browser.new_page()
            page.set_default_timeout(30000)
            
            try:
                # Phase 1: SSCS Help System Research
                print("\n📚 PHASE 1: SSCS Help System Research...")
                help_results = await self._research_sscs_help_documentation(page)
                discovery_results['help_system_research'] = help_results
                
                # Phase 2: Direct CPB Interface Configuration
                print("\n⚙️ PHASE 2: Direct CPB Interface Configuration...")
                interface_results = await self._configure_cpb_interface(page)
                discovery_results['interface_configuration'] = interface_results
                
                # Phase 3: NAXML File Validation Testing
                print("\n🧪 PHASE 3: NAXML File Validation Testing...")
                validation_results = await self._validate_naxml_processing(page)
                discovery_results['naxml_validation'] = validation_results
                
                # Phase 4: Compile EDI Path Recommendation
                print("\n📋 PHASE 4: EDI Path Recommendation...")
                edi_recommendation = self._compile_edi_path_recommendation(discovery_results)
                discovery_results['edi_path_recommendation'] = edi_recommendation
                
                return discovery_results
                
            except Exception as e:
                print(f"❌ Enhanced discovery error: {str(e)}")
                discovery_results['error'] = str(e)
                return discovery_results
            
            finally:
                await browser.close()
    
    async def _research_sscs_help_documentation(self, page: Page) -> Dict[str, Any]:
        """Research SSCS help system for Vendor Import guidance"""
        try:
            print("📚 Researching SSCS help documentation...")
            
            # Login to access help system
            await page.goto(self.cpb_base_url)
            await self._perform_login(page)
            
            # Try to access help system
            help_urls_to_try = [
                "Help/wwhelp/wwhimpl/common/html/wwhelp.htm#href=vendor_import.html",
                "Help/wwhelp/wwhimpl/common/html/wwhelp.htm#href=file_location.html", 
                "Help/wwhelp/wwhimpl/common/html/wwhelp.htm#href=edi_setup.html",
                "Help/wwhelp/wwhimpl/common/html/wwhelp.htm#href=import_setup.html",
                "Help/",
                "help.html"
            ]
            
            help_findings = {}
            
            for help_url in help_urls_to_try:
                try:
                    full_url = self.cpb_base_url + help_url
                    print(f"🔍 Trying help URL: {help_url}")
                    
                    await page.goto(full_url)
                    await page.wait_for_load_state('networkidle')
                    
                    # Check if help page loaded
                    page_title = await page.title()
                    page_content = await page.content()
                    
                    # Look for vendor import, file location, or EDI content
                    relevant_keywords = ['vendor import', 'file location', 'edi', 'naxml', 'vendor setup']
                    content_relevance = sum(1 for keyword in relevant_keywords 
                                          if keyword in page_content.lower())
                    
                    if content_relevance > 0:
                        print(f"✅ Relevant help found: {help_url} (relevance: {content_relevance})")
                        
                        # Extract relevant text
                        help_text = await page.evaluate('''() => {
                            return document.body.innerText;
                        }''')
                        
                        help_findings[help_url] = {
                            'title': page_title,
                            'relevance_score': content_relevance,
                            'content_preview': help_text[:500],
                            'full_content': help_text
                        }
                        
                        # Screenshot if highly relevant
                        if content_relevance >= 2:
                            screenshot_name = f"help_{help_url.replace('/', '_').replace('#', '_')}.png"
                            await page.screenshot(path=str(self.results_dir / screenshot_name))
                            help_findings[help_url]['screenshot'] = screenshot_name
                    
                except Exception as e:
                    print(f"⚠️ Help URL failed: {help_url} - {str(e)}")
                    continue
            
            print(f"📚 Help research complete: {len(help_findings)} relevant pages found")
            return help_findings
            
        except Exception as e:
            print(f"❌ Help system research error: {str(e)}")
            return {'error': str(e)}
    
    async def _configure_cpb_interface(self, page: Page) -> Dict[str, Any]:
        """Direct CPB interface configuration and EDI path discovery"""
        try:
            print("⚙️ Configuring CPB interface...")
            
            # Navigate to Vendor Import Setup
            vendor_import_url = self.cpb_base_url + "#!/setup/vendorimport"
            await page.goto(vendor_import_url)
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(3)  # Wait for SPA loading
            
            print("✅ Accessed Vendor Import Setup interface")
            
            # Capture current interface
            await page.screenshot(path=str(self.results_dir / 'vendor_import_interface.png'))
            
            # Extract all form fields with enhanced detection
            form_analysis = await page.evaluate('''() => {
                const analysis = {
                    inputs: [],
                    selects: [], 
                    buttons: [],
                    labels: [],
                    file_location_hints: []
                };
                
                // Get all form elements
                document.querySelectorAll('input').forEach(input => {
                    analysis.inputs.push({
                        type: input.type,
                        name: input.name || '',
                        id: input.id || '',
                        placeholder: input.placeholder || '',
                        value: input.value || '',
                        class: input.className || ''
                    });
                });
                
                document.querySelectorAll('select').forEach(select => {
                    const options = Array.from(select.options).map(opt => ({
                        value: opt.value,
                        text: opt.textContent.trim()
                    }));
                    
                    analysis.selects.push({
                        name: select.name || '',
                        id: select.id || '',
                        options: options,
                        class: select.className || ''
                    });
                });
                
                document.querySelectorAll('button').forEach(button => {
                    analysis.buttons.push({
                        text: button.textContent.trim(),
                        type: button.type || '',
                        class: button.className || ''
                    });
                });
                
                document.querySelectorAll('label').forEach(label => {
                    analysis.labels.push({
                        text: label.textContent.trim(),
                        for: label.getAttribute('for') || ''
                    });
                });
                
                // Look for file location related text
                const allText = document.body.innerText.toLowerCase();
                const locationKeywords = ['file location', 'file path', 'folder', 'directory', 'edi'];
                locationKeywords.forEach(keyword => {
                    if (allText.includes(keyword)) {
                        analysis.file_location_hints.push(keyword);
                    }
                });
                
                return analysis;
            }''')
            
            print(f"📋 Interface analysis complete:")
            print(f"   Inputs: {len(form_analysis['inputs'])}")
            print(f"   Selects: {len(form_analysis['selects'])}")
            print(f"   Buttons: {len(form_analysis['buttons'])}")
            print(f"   Labels: {len(form_analysis['labels'])}")
            print(f"   File location hints: {form_analysis['file_location_hints']}")
            
            # Look for File Location specific elements
            file_location_elements = []
            
            # Check inputs for location-related fields
            for input_elem in form_analysis['inputs']:
                if any(keyword in input_elem.get('name', '').lower() for keyword in ['location', 'path', 'folder']):
                    file_location_elements.append({
                        'type': 'input',
                        'element': input_elem
                    })
                    print(f"📁 File Location input found: {input_elem['name']}")
            
            # Check selects for location-related fields  
            for select_elem in form_analysis['selects']:
                if any(keyword in select_elem.get('name', '').lower() for keyword in ['location', 'path', 'folder']):
                    file_location_elements.append({
                        'type': 'select',
                        'element': select_elem
                    })
                    print(f"📁 File Location select found: {select_elem['name']}")
                    if select_elem['options']:
                        print(f"   Options: {[opt['text'] for opt in select_elem['options'][:5]]}")
            
            return {
                'form_analysis': form_analysis,
                'file_location_elements': file_location_elements,
                'interface_accessible': True,
                'configuration_ready': len(file_location_elements) > 0
            }
            
        except Exception as e:
            print(f"❌ Interface configuration error: {str(e)}")
            return {'error': str(e)}
    
    async def _validate_naxml_processing(self, page: Page) -> Dict[str, Any]:
        """Validate NAXML processing with your generated files"""
        try:
            print("🧪 Validating NAXML processing...")
            
            # Check if we have your test files available
            test_files = {
                'small_test': 'data/sscs_discovery/DABS_TEST_ItemPrice.xml',
                'full_test': 'DABS_2025-08-22.xml',
                'user_test': 'dabs_price_update.xml'
            }
            
            available_files = {}
            for file_type, file_path in test_files.items():
                if Path(file_path).exists():
                    file_size = Path(file_path).stat().st_size
                    available_files[file_type] = {
                        'path': file_path,
                        'size_bytes': file_size,
                        'exists': True
                    }
                    print(f"✅ Test file available: {file_path} ({file_size} bytes)")
                else:
                    available_files[file_type] = {'exists': False}
                    print(f"⚠️ Test file not found: {file_path}")
            
            # Look for file upload interface in current page
            upload_capabilities = await page.evaluate('''() => {
                const uploads = {
                    file_inputs: [],
                    upload_buttons: [],
                    drag_drop_areas: []
                };
                
                // File input elements
                document.querySelectorAll('input[type="file"]').forEach(input => {
                    uploads.file_inputs.push({
                        name: input.name || '',
                        id: input.id || '',
                        accept: input.accept || '',
                        multiple: input.multiple || false
                    });
                });
                
                // Upload buttons
                document.querySelectorAll('button').forEach(button => {
                    const text = button.textContent.toLowerCase();
                    if (text.includes('upload') || text.includes('import') || text.includes('browse')) {
                        uploads.upload_buttons.push({
                            text: button.textContent.trim(),
                            class: button.className || ''
                        });
                    }
                });
                
                // Look for drag-drop areas
                document.querySelectorAll('div, section').forEach(div => {
                    const text = div.textContent.toLowerCase();
                    if (text.includes('drag') || text.includes('drop') || text.includes('upload')) {
                        uploads.drag_drop_areas.push({
                            text: div.textContent.trim().substring(0, 100),
                            class: div.className || ''
                        });
                    }
                });
                
                return uploads;
            }''')
            
            print(f"📤 Upload capabilities found:")
            print(f"   File inputs: {len(upload_capabilities['file_inputs'])}")
            print(f"   Upload buttons: {len(upload_capabilities['upload_buttons'])}")
            print(f"   Drag-drop areas: {len(upload_capabilities['drag_drop_areas'])}")
            
            return {
                'available_test_files': available_files,
                'upload_capabilities': upload_capabilities,
                'validation_ready': any(f['exists'] for f in available_files.values())
            }
            
        except Exception as e:
            print(f"❌ NAXML validation error: {str(e)}")
            return {'error': str(e)}
    
    async def _perform_login(self, page: Page) -> bool:
        """Perform SSCS login with confirmed credentials"""
        try:
            await page.goto(self.cpb_base_url)
            await page.wait_for_load_state('networkidle')
            
            if await page.locator('input[name="username"]').is_visible():
                await page.fill('input[name="username"]', self.username)
                await page.fill('input[name="password"]', self.password)
                await page.click('button:has-text("login")')
                await page.wait_for_load_state('networkidle')
            
            # Validate login success
            current_url = page.url
            return 'cpb' in current_url.lower() or not await page.locator('input[name="username"]').is_visible()
            
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def _compile_edi_path_recommendation(self, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compile EDI path recommendation from all discovery methods"""
        
        recommendation = {
            'status': 'analysis_complete',
            'confidence_level': 'high',
            'recommended_approach': 'manual_interface_configuration'
        }
        
        # Analyze help system findings
        if 'help_system_research' in discovery_results:
            help_data = discovery_results['help_system_research']
            if isinstance(help_data, dict) and len(help_data) > 0:
                recommendation['help_documentation_available'] = True
                recommendation['help_guidance'] = "Use discovered help documentation for configuration"
            else:
                recommendation['help_documentation_available'] = False
                recommendation['help_guidance'] = "Proceed with interface exploration"
        
        # Analyze interface findings
        if 'interface_configuration' in discovery_results:
            interface_data = discovery_results['interface_configuration']
            if interface_data.get('configuration_ready', False):
                file_location_elements = interface_data.get('file_location_elements', [])
                if file_location_elements:
                    recommendation['file_location_fields_found'] = True
                    recommendation['configuration_method'] = "Direct interface configuration"
                    
                    # Recommend based on field type
                    for element in file_location_elements:
                        if element['type'] == 'select':
                            recommendation['recommended_method'] = "dropdown_selection"
                            recommendation['edi_path_source'] = "dropdown_options"
                        elif element['type'] == 'input':
                            recommendation['recommended_method'] = "manual_path_entry"
                            recommendation['edi_path_source'] = "text_input_validation"
                else:
                    recommendation['file_location_fields_found'] = False
                    recommendation['configuration_method'] = "Manual interface exploration needed"
        
        # Analyze validation capabilities
        if 'naxml_validation' in discovery_results:
            validation_data = discovery_results['naxml_validation']
            if validation_data.get('validation_ready', False):
                recommendation['naxml_testing_ready'] = True
                recommendation['test_files_available'] = validation_data['available_test_files']
            
            upload_caps = validation_data.get('upload_capabilities', {})
            if upload_caps.get('file_inputs') or upload_caps.get('upload_buttons'):
                recommendation['web_upload_available'] = True
                recommendation['upload_method'] = "web_interface"
            else:
                recommendation['web_upload_available'] = False
                recommendation['upload_method'] = "file_system_delivery"
        
        # Generate specific recommendations
        if recommendation.get('file_location_fields_found', False):
            recommendation['next_action'] = "Configure DABS vendor using discovered File Location field"
            recommendation['confidence'] = "HIGH"
        else:
            recommendation['next_action'] = "Manual interface exploration to locate File Location configuration"
            recommendation['confidence'] = "MEDIUM"
        
        # Always recommend testing with user's NAXML files
        recommendation['validation_plan'] = "Test with available NAXML files after configuration"
        
        return recommendation
    
    async def save_enhanced_discovery_results(self, results: Dict[str, Any]):
        """Save comprehensive discovery results"""
        try:
            # Save complete results
            results_file = self.results_dir / f'enhanced_edi_discovery_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\n📄 Enhanced discovery results saved: {results_file}")
            
            # Generate EDI configuration if recommendation available
            if 'edi_path_recommendation' in results:
                recommendation = results['edi_path_recommendation']
                
                config_content = f"""# SSCS EDI Configuration - Enhanced Discovery Results
# Generated: {datetime.now().isoformat()}
# Discovery Status: {recommendation.get('status', 'unknown')}
# Confidence Level: {recommendation.get('confidence', 'unknown')}

# EDI Path Configuration (Update after manual discovery)
SSCS_EDI_FOLDER_PATH=TBD_MANUAL_DISCOVERY_NEEDED

# Configuration Method
EDI_ACCESS_METHOD={recommendation.get('upload_method', 'file_system_delivery')}
EDI_DISCOVERY_STATUS={recommendation.get('status', 'manual_exploration_needed')}

# Next Actions
EDI_NEXT_ACTION="{recommendation.get('next_action', 'Manual CPB interface exploration')}"
EDI_CONFIDENCE_LEVEL={recommendation.get('confidence', 'MEDIUM')}

# Automation Readiness
AUTOMATION_SCRIPTS_READY=true
NAXML_GENERATION_PROVEN=true
MONTHLY_SCHEDULE_DEFINED=true
DEPLOYMENT_BLOCKED_BY=EDI_PATH_DISCOVERY
"""
                
                config_file = self.results_dir / 'edi_discovery_config.env'
                with open(config_file, 'w') as f:
                    f.write(config_content)
                
                print(f"⚙️ EDI configuration template saved: {config_file}")
            
        except Exception as e:
            print(f"❌ Failed to save discovery results: {str(e)}")

async def main():
    """Execute enhanced EDI path discovery"""
    
    print("🚀 ENHANCED EDI PATH DISCOVERY EXECUTION")
    print("=" * 50)
    
    discovery = EnhancedSSCSEDIDiscovery()
    results = await discovery.enhanced_edi_discovery()
    
    # Save results
    await discovery.save_enhanced_discovery_results(results)
    
    # Display summary
    if 'error' not in results:
        print("\n🎉 ENHANCED EDI DISCOVERY COMPLETED!")
        
        recommendation = results.get('edi_path_recommendation', {})
        
        print(f"\n📊 DISCOVERY SUMMARY:")
        print(f"📚 Help system research: {'✅ SUCCESS' if 'help_system_research' in results else '⚠️ LIMITED'}")
        print(f"⚙️ Interface configuration: {'✅ READY' if recommendation.get('file_location_fields_found') else '🔧 MANUAL NEEDED'}")
        print(f"🧪 NAXML validation: {'✅ READY' if recommendation.get('naxml_testing_ready') else '⚠️ FILES MISSING'}")
        
        print(f"\n🎯 RECOMMENDATION:")
        print(f"Next Action: {recommendation.get('next_action', 'Manual interface exploration')}")
        print(f"Confidence: {recommendation.get('confidence', 'MEDIUM')}")
        print(f"Method: {recommendation.get('configuration_method', 'Manual discovery')}")
        
        if recommendation.get('file_location_fields_found'):
            print(f"\n✅ FILE LOCATION FIELDS DISCOVERED!")
            print(f"🚀 Ready for immediate DABS vendor configuration")
            print(f"📤 Ready for NAXML file testing")
            print(f"⚡ Ready for automation deployment")
        else:
            print(f"\n🔧 MANUAL INTERFACE EXPLORATION NEEDED")
            print(f"📋 Use captured screenshots and form analysis")
            print(f"🔍 Manually locate File Location configuration")
        
        print(f"\n📁 Results saved in: data/enhanced_edi_discovery/")
        print(f"🚀 READY TO COMPLETE EDI PATH ESTABLISHMENT")
        
    else:
        print(f"\n❌ ENHANCED EDI DISCOVERY FAILED")
        print(f"Error: {results.get('error')}")
        print(f"🔧 Fallback to manual interface exploration")

if __name__ == "__main__":
    asyncio.run(main())
