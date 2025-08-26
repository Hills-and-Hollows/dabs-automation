"""
DABS EDI Email Delivery System
Sends NAXML EDI invoices to SSCS CDB system via v6242s1@edidelivery.com

Business Context:
- Automated delivery to SSCS EDI processing system
- Ensures proper file naming and email formatting
- Maintains audit trail for Utah Package Agency compliance
- Enables 90% time reduction in DABS processing
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from pathlib import Path
import os
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EDIDeliveryResult:
    """Result of EDI email delivery"""
    success: bool
    filename: str
    edi_email: str
    timestamp: str
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None

class DABSEDIMailer:
    """Email delivery system for DABS EDI invoices"""
    
    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None):
        """
        Initialize EDI mailer with SMTP configuration
        
        Args:
            smtp_config: SMTP server configuration
        """
        self.edi_email = "v6242s1@edidelivery.com"
        
        # Default SMTP configuration (can be overridden)
        self.smtp_config = smtp_config or {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        }
        
        # Validate SMTP configuration
        if not self.smtp_config['username'] or not self.smtp_config['password']:
            logger.warning("SMTP credentials not configured - email delivery will fail")
    
    def send_edi_invoice(self, 
                        naxml_content: str, 
                        invoice_number: str,
                        sender_email: Optional[str] = None) -> EDIDeliveryResult:
        """
        Send DABS EDI invoice via email to SSCS
        
        Args:
            naxml_content: NAXML formatted invoice content
            invoice_number: Invoice number for tracking
            sender_email: Optional sender email (defaults to SMTP username)
            
        Returns:
            EDIDeliveryResult with delivery status and details
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"DABS_{timestamp}_ItemPrice.xml"
        
        logger.info(f"Preparing EDI email delivery: {filename}")
        
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['To'] = self.edi_email
            msg['From'] = sender_email or self.smtp_config['username']
            msg['Subject'] = f"DABS_ItemPrice_{datetime.now().strftime('%Y%m%d')}.xml"
            
            # Email body with invoice details
            item_count = naxml_content.count('<Item>')
            body = f"""DABS Vendor Price Update
Invoice: {invoice_number}
Date: {datetime.now().strftime('%Y-%m-%d')}
Items: {item_count}
Format: NAXML ItemSynch v2.0
Store: Hills & Hollows LLC - Boulder, UT
Vendor: Utah Division of Alcoholic Beverage Control

This is an automated EDI delivery for SSCS CDB processing.
File: {filename}"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach NAXML file
            attachment = MIMEApplication(naxml_content.encode('utf-8'))
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            attachment.add_header('Content-Type', 'application/xml')
            msg.attach(attachment)
            
            # Send email
            delivery_result = self._send_email(msg, filename, len(naxml_content.encode('utf-8')))
            
            if delivery_result.success:
                logger.info(f"EDI invoice delivered successfully: {filename}")
                # Log for audit trail
                self._log_delivery(delivery_result, invoice_number, item_count)
            else:
                logger.error(f"EDI delivery failed: {delivery_result.error_message}")
            
            return delivery_result
            
        except Exception as e:
            logger.error(f"EDI email delivery error: {str(e)}")
            return EDIDeliveryResult(
                success=False,
                filename=filename,
                edi_email=self.edi_email,
                timestamp=datetime.now().isoformat(),
                error_message=str(e)
            )
    
    def _send_email(self, msg: MIMEMultipart, filename: str, file_size: int) -> EDIDeliveryResult:
        """
        Send email via SMTP
        
        Args:
            msg: Email message to send
            filename: Attachment filename
            file_size: File size in bytes
            
        Returns:
            EDIDeliveryResult with delivery status
        """
        try:
            # Create SMTP connection
            if self.smtp_config['use_tls']:
                context = ssl.create_default_context()
                server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
                server.starttls(context=context)
            else:
                server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
            
            # Login and send
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            text = msg.as_string()
            server.sendmail(msg['From'], msg['To'], text)
            server.quit()
            
            return EDIDeliveryResult(
                success=True,
                filename=filename,
                edi_email=self.edi_email,
                timestamp=datetime.now().isoformat(),
                file_size=file_size
            )
            
        except smtplib.SMTPAuthenticationError as e:
            return EDIDeliveryResult(
                success=False,
                filename=filename,
                edi_email=self.edi_email,
                timestamp=datetime.now().isoformat(),
                error_message=f"SMTP Authentication failed: {str(e)}",
                file_size=file_size
            )
        except smtplib.SMTPException as e:
            return EDIDeliveryResult(
                success=False,
                filename=filename,
                edi_email=self.edi_email,
                timestamp=datetime.now().isoformat(),
                error_message=f"SMTP error: {str(e)}",
                file_size=file_size
            )
        except Exception as e:
            return EDIDeliveryResult(
                success=False,
                filename=filename,
                edi_email=self.edi_email,
                timestamp=datetime.now().isoformat(),
                error_message=f"Unexpected error: {str(e)}",
                file_size=file_size
            )
    
    def _log_delivery(self, result: EDIDeliveryResult, invoice_number: str, item_count: int):
        """
        Log EDI delivery for audit trail
        
        Args:
            result: Delivery result
            invoice_number: Invoice number
            item_count: Number of items in invoice
        """
        log_entry = {
            'timestamp': result.timestamp,
            'invoice_number': invoice_number,
            'filename': result.filename,
            'edi_email': result.edi_email,
            'item_count': item_count,
            'file_size': result.file_size,
            'success': result.success,
            'error': result.error_message
        }
        
        # Create audit log directory
        log_dir = Path("logs/edi_deliveries")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Log to daily file for Utah compliance (7-year retention)
        log_file = log_dir / f"edi_deliveries_{datetime.now().strftime('%Y%m%d')}.log"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            import json
            f.write(json.dumps(log_entry) + '\n')
        
        logger.info(f"EDI delivery logged to: {log_file}")
    
    def send_test_email(self) -> EDIDeliveryResult:
        """
        Send test email to verify SMTP configuration
        
        Returns:
            EDIDeliveryResult with test status
        """
        test_content = """<?xml version="1.0" encoding="UTF-8"?>
<ItemSynch version="2.0" timestamp="2025-08-25T13:30:00Z" vendor="DABS">
  <VendorInfo>
    <VendorID>DABS</VendorID>
    <VendorName>Utah Division of Alcoholic Beverage Control</VendorName>
    <InvoiceNumber>DABS_TEST_001</InvoiceNumber>
    <InvoiceDate>2025-08-25</InvoiceDate>
    <TotalItems>1</TotalItems>
    <StoreLocationID>HILLS_HOLLOWS_BOULDER</StoreLocationID>
    <TransmissionDate>2025-08-25</TransmissionDate>
  </VendorInfo>
  <Items>
    <Item>
      <PLU>99999</PLU>
      <ItemName>TEST ITEM - DO NOT PROCESS</ItemName>
      <Price>0.01</Price>
      <Cost>0.01</Cost>
      <Category>TEST</Category>
      <Size>TEST</Size>
      <VendorItemCode>99999</VendorItemCode>
      <LastUpdated>2025-08-25T13:30:00Z</LastUpdated>
      <Status>Test</Status>
    </Item>
  </Items>
  <InvoiceTotals>
    <SubTotal>0.01</SubTotal>
    <Tax>0.00</Tax>
    <Total>0.01</Total>
    <ItemCount>1</ItemCount>
  </InvoiceTotals>
</ItemSynch>"""
        
        return self.send_edi_invoice(test_content, "DABS_TEST_001")
    
    def validate_smtp_config(self) -> Dict[str, Any]:
        """
        Validate SMTP configuration
        
        Returns:
            Validation results
        """
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['smtp_server', 'smtp_port', 'username', 'password']
        for field in required_fields:
            if not self.smtp_config.get(field):
                validation['errors'].append(f"Missing required SMTP field: {field}")
                validation['valid'] = False
        
        # Check port is numeric
        try:
            int(self.smtp_config['smtp_port'])
        except (ValueError, TypeError):
            validation['errors'].append("SMTP port must be numeric")
            validation['valid'] = False
        
        # Test connection (optional)
        if validation['valid']:
            try:
                if self.smtp_config['use_tls']:
                    context = ssl.create_default_context()
                    server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
                    server.starttls(context=context)
                else:
                    server = smtplib.SMTP(self.smtp_config['smtp_server'], self.smtp_config['smtp_port'])
                
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.quit()
                validation['warnings'].append("SMTP connection test successful")
                
            except Exception as e:
                validation['warnings'].append(f"SMTP connection test failed: {str(e)}")
        
        return validation

class EDIDeliveryManager:
    """High-level manager for EDI delivery operations"""
    
    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None):
        self.mailer = DABSEDIMailer(smtp_config)
        
    def deliver_dabs_invoice(self, naxml_content: str, invoice_number: str) -> EDIDeliveryResult:
        """
        Complete EDI delivery workflow with validation and logging
        
        Args:
            naxml_content: NAXML invoice content
            invoice_number: Invoice number for tracking
            
        Returns:
            EDIDeliveryResult with delivery status
        """
        logger.info(f"Starting EDI delivery workflow for invoice: {invoice_number}")
        
        # Validate NAXML content
        from .dabs_edi_generator import DABSEDIGenerator
        generator = DABSEDIGenerator()
        validation = generator.validate_naxml(naxml_content)
        
        if not validation['valid']:
            logger.error(f"NAXML validation failed: {validation['errors']}")
            return EDIDeliveryResult(
                success=False,
                filename=f"DABS_{datetime.now().strftime('%Y%m%d_%H%M%S')}_ItemPrice.xml",
                edi_email=self.mailer.edi_email,
                timestamp=datetime.now().isoformat(),
                error_message=f"NAXML validation failed: {'; '.join(validation['errors'])}"
            )
        
        # Send EDI invoice
        result = self.mailer.send_edi_invoice(naxml_content, invoice_number)
        
        # Additional logging for business metrics
        if result.success:
            logger.info(f"EDI delivery successful - Invoice: {invoice_number}, Items: {validation['item_count']}, Cost: ${validation['total_cost']:.2f}")
        
        return result

# Example usage and testing
if __name__ == "__main__":
    import os
    
    # Test SMTP configuration (use environment variables)
    smtp_config = {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': os.getenv('SMTP_USERNAME'),
        'password': os.getenv('SMTP_PASSWORD'),
        'use_tls': True
    }
    
    # Initialize mailer
    mailer = DABSEDIMailer(smtp_config)
    
    # Validate configuration
    validation = mailer.validate_smtp_config()
    print(f"SMTP Validation: {validation}")
    
    if validation['valid']:
        # Send test email
        print("Sending test EDI email...")
        result = mailer.send_test_email()
        print(f"Test Result: Success={result.success}, File={result.filename}")
        if not result.success:
            print(f"Error: {result.error_message}")
    else:
        print("SMTP configuration invalid - cannot send test email")
        for error in validation['errors']:
            print(f"ERROR: {error}")
