#!/usr/bin/env python3
"""
DABS Invoice and Purchase Analysis System - Hills & Hollows LLC
Advanced analytics for purchase tracking, price trends, and invoice management

Analyzes:
- Purchase patterns and frequency
- Price variance tracking across time periods
- Vendor invoice reconciliation
- SKU performance and demand forecasting
- Compliance reporting preparation

Author: DABS Automation System
Created: 2025-01-11
"""

import asyncio
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DABS_INVOICE_ANALYZER - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@dataclass
class PurchaseAnalytics:
    """Purchase analytics results"""
    analysis_period: str
    total_orders: int
    total_value: Decimal
    unique_products: int
    top_products: List[Dict[str, Any]]
    price_trends: Dict[str, Any]
    purchase_frequency: Dict[str, Any]
    variance_alerts: List[Dict[str, Any]]

@dataclass
class PriceTrend:
    """Price trend analysis for a product"""
    item_code: str
    description: str
    price_history: List[Tuple[str, Decimal]]  # (date, price)
    current_price: Decimal
    avg_price: Decimal
    min_price: Decimal
    max_price: Decimal
    price_variance: Decimal
    trend_direction: str  # 'increasing', 'decreasing', 'stable'

class DABSInvoiceAnalyzer:
    """
    Advanced analytics system for DABS order and invoice data
    
    Capabilities:
    - Purchase pattern analysis
    - Price trend monitoring
    - Invoice reconciliation
    - Demand forecasting
    - Compliance reporting preparation
    """
    
    def __init__(self):
        self.project_root = Path('/Volumes/Expansion/4. CURSOR/DABC Pricing - Inventory')
        self.data_dir = self.project_root / 'data/dabs_orders'
        self.analysis_dir = self.data_dir / 'analysis'
        self.reports_dir = self.project_root / 'data/reports'
        
        # Create directories
        for dir_path in [self.analysis_dir, self.reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self.orders_data = None
        self.line_items_data = None
        
        logger.info("DABS Invoice Analyzer initialized")
    
    async def load_extracted_data(self, data_file_pattern: str = "dabs_orders_*.json") -> bool:
        """Load previously extracted DABS order data"""
        
        try:
            # Find latest data file
            data_files = list(self.data_dir.glob("extracted_data/" + data_file_pattern))
            if not data_files:
                logger.error(f"No data files found matching pattern: {data_file_pattern}")
                return False
            
            latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"Loading data from: {latest_file.name}")
            
            with open(latest_file, 'r') as f:
                orders_data = json.load(f)
            
            # Convert to DataFrames for analysis
            orders_list = []
            line_items_list = []
            
            for order in orders_data:
                # Order-level data
                order_record = {
                    'order_id': order['order_id'],
                    'delivery_date': pd.to_datetime(order['delivery_date']),
                    'sales_order': order['sales_order'],
                    'store': order['store'],
                    'status': order['status'],
                    'total_quantities': order['total_quantities'],
                    'total_cost': Decimal(str(order['total_cost'])),
                    'line_items_count': len(order['line_items'])
                }
                orders_list.append(order_record)
                
                # Line items data
                for item in order['line_items']:
                    line_item_record = {
                        'order_id': order['order_id'],
                        'delivery_date': pd.to_datetime(order['delivery_date']),
                        'item_code': item['item_code'],
                        'description': item['description'],
                        'unit_price': Decimal(str(item['unit_price'])),
                        'quantity': item['quantity'],
                        'extended_price': Decimal(str(item['extended_price'])),
                        'sales_order': order['sales_order'],
                        'status': order['status']
                    }
                    line_items_list.append(line_item_record)
            
            self.orders_data = pd.DataFrame(orders_list)
            self.line_items_data = pd.DataFrame(line_items_list)
            
            logger.info(f"Loaded {len(self.orders_data)} orders with {len(self.line_items_data)} line items")
            return True
            
        except Exception as e:
            logger.error(f"Error loading extracted data: {e}")
            return False
    
    async def analyze_price_trends(self, lookback_days: int = 180) -> Dict[str, PriceTrend]:
        """Analyze price trends for all products over time"""
        
        if self.line_items_data is None:
            raise ValueError("No data loaded. Run load_extracted_data() first.")
        
        logger.info(f"Analyzing price trends over {lookback_days} days")
        
        # Filter data by lookback period
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        recent_data = self.line_items_data[self.line_items_data['delivery_date'] >= cutoff_date]
        
        price_trends = {}
        
        # Group by item code and analyze trends
        for item_code, group in recent_data.groupby('item_code'):
            try:
                # Sort by delivery date
                group_sorted = group.sort_values('delivery_date')
                
                # Extract price history
                price_history = [
                    (row['delivery_date'].strftime('%Y-%m-%d'), row['unit_price'])
                    for _, row in group_sorted.iterrows()
                ]
                
                # Calculate price statistics
                prices = [float(price) for _, price in price_history]
                current_price = prices[-1] if prices else 0
                avg_price = np.mean(prices) if prices else 0
                min_price = min(prices) if prices else 0
                max_price = max(prices) if prices else 0
                
                # Calculate variance
                price_variance = ((max_price - min_price) / avg_price * 100) if avg_price > 0 else 0
                
                # Determine trend direction
                if len(prices) >= 2:
                    recent_avg = np.mean(prices[-3:])  # Last 3 purchases
                    older_avg = np.mean(prices[:-3]) if len(prices) > 3 else prices[0]
                    
                    if recent_avg > older_avg * 1.05:  # 5% threshold
                        trend_direction = 'increasing'
                    elif recent_avg < older_avg * 0.95:
                        trend_direction = 'decreasing'
                    else:
                        trend_direction = 'stable'
                else:
                    trend_direction = 'insufficient_data'
                
                # Create trend object
                trend = PriceTrend(
                    item_code=item_code,
                    description=group_sorted.iloc[0]['description'],
                    price_history=price_history,
                    current_price=Decimal(str(current_price)),
                    avg_price=Decimal(str(avg_price)),
                    min_price=Decimal(str(min_price)),
                    max_price=Decimal(str(max_price)),
                    price_variance=Decimal(str(price_variance)),
                    trend_direction=trend_direction
                )
                
                price_trends[item_code] = trend
                
            except Exception as e:
                logger.warning(f"Error analyzing price trend for {item_code}: {e}")
                continue
        
        logger.info(f"Analyzed price trends for {len(price_trends)} products")
        return price_trends
    
    async def identify_purchase_patterns(self) -> Dict[str, Any]:
        """Identify purchasing patterns and anomalies"""
        
        if self.line_items_data is None:
            raise ValueError("No data loaded. Run load_extracted_data() first.")
        
        logger.info("Analyzing purchase patterns")
        
        # Purchase frequency analysis
        item_frequency = self.line_items_data.groupby('item_code').agg({
            'order_id': 'count',
            'quantity': 'sum',
            'extended_price': 'sum',
            'delivery_date': ['min', 'max'],
            'description': 'first'
        }).round(2)
        
        item_frequency.columns = ['order_count', 'total_quantity', 'total_value', 'first_purchase', 'last_purchase', 'description']
        
        # Calculate purchase intervals
        item_frequency['days_between_orders'] = (
            (item_frequency['last_purchase'] - item_frequency['first_purchase']).dt.days / 
            item_frequency['order_count'].clip(lower=1)
        ).round(1)
        
        # Categorize products
        high_frequency = item_frequency[item_frequency['order_count'] >= 5]  # 5+ orders
        medium_frequency = item_frequency[(item_frequency['order_count'] >= 2) & (item_frequency['order_count'] < 5)]
        low_frequency = item_frequency[item_frequency['order_count'] == 1]
        
        # Seasonal pattern analysis
        self.line_items_data['month'] = self.line_items_data['delivery_date'].dt.month
        self.line_items_data['quarter'] = self.line_items_data['delivery_date'].dt.quarter
        
        seasonal_patterns = self.line_items_data.groupby(['item_code', 'month']).agg({
            'quantity': 'sum',
            'extended_price': 'sum'
        }).reset_index()
        
        patterns = {
            'analysis_date': datetime.now().isoformat(),
            'frequency_categories': {
                'high_frequency_products': len(high_frequency),
                'medium_frequency_products': len(medium_frequency),
                'single_purchase_products': len(low_frequency)
            },
            'top_products': {
                'by_order_count': item_frequency.nlargest(20, 'order_count').to_dict('records'),
                'by_total_value': item_frequency.nlargest(20, 'total_value').to_dict('records'),
                'by_quantity': item_frequency.nlargest(20, 'total_quantity').to_dict('records')
            },
            'purchase_intervals': {
                'frequent_items': high_frequency[['description', 'days_between_orders', 'order_count']].to_dict('records'),
                'avg_reorder_days': float(item_frequency['days_between_orders'].mean()),
                'median_reorder_days': float(item_frequency['days_between_orders'].median())
            },
            'seasonal_insights': seasonal_patterns.groupby('month').agg({
                'quantity': 'sum',
                'extended_price': 'sum'
            }).to_dict('records')
        }
        
        return patterns
    
    async def generate_price_variance_alerts(self, variance_threshold: float = 20.0) -> List[Dict[str, Any]]:
        """Generate alerts for products with significant price variance"""
        
        price_trends = await self.analyze_price_trends()
        alerts = []
        
        for item_code, trend in price_trends.items():
            if trend.price_variance > variance_threshold:
                alert = {
                    'item_code': item_code,
                    'description': trend.description,
                    'current_price': float(trend.current_price),
                    'avg_price': float(trend.avg_price),
                    'price_variance_percent': float(trend.price_variance),
                    'min_price': float(trend.min_price),
                    'max_price': float(trend.max_price),
                    'trend_direction': trend.trend_direction,
                    'alert_level': 'HIGH' if trend.price_variance > 50 else 'MEDIUM',
                    'recommendation': self._generate_price_recommendation(trend)
                }
                alerts.append(alert)
        
        # Sort by variance (highest first)
        alerts.sort(key=lambda x: x['price_variance_percent'], reverse=True)
        
        logger.info(f"Generated {len(alerts)} price variance alerts")
        return alerts
    
    def _generate_price_recommendation(self, trend: PriceTrend) -> str:
        """Generate price recommendation based on trend analysis"""
        
        if trend.trend_direction == 'increasing' and trend.price_variance > 30:
            return "REVIEW: Significant price increases detected. Verify with vendor."
        elif trend.trend_direction == 'decreasing' and trend.price_variance > 30:
            return "OPPORTUNITY: Price decreases detected. Consider stock-up."
        elif trend.price_variance > 50:
            return "CRITICAL: Extreme price volatility. Immediate review required."
        else:
            return "MONITOR: Normal price fluctuation within acceptable range."
    
    async def generate_inventory_insights(self) -> Dict[str, Any]:
        """Generate inventory management insights from purchase data"""
        
        if self.line_items_data is None:
            raise ValueError("No data loaded. Run load_extracted_data() first.")
        
        logger.info("Generating inventory management insights")
        
        # Calculate inventory turnover metrics
        product_metrics = self.line_items_data.groupby('item_code').agg({
            'quantity': ['sum', 'mean', 'std'],
            'extended_price': ['sum', 'mean'],
            'order_id': 'count',
            'delivery_date': ['min', 'max'],
            'description': 'first'
        })
        
        product_metrics.columns = [
            'total_quantity', 'avg_quantity_per_order', 'quantity_std',
            'total_value', 'avg_order_value', 'order_count',
            'first_order', 'last_order', 'description'
        ]
        
        # Calculate days between orders for reorder frequency
        product_metrics['days_active'] = (
            product_metrics['last_order'] - product_metrics['first_order']
        ).dt.days
        
        product_metrics['avg_days_between_orders'] = (
            product_metrics['days_active'] / product_metrics['order_count'].clip(lower=1)
        ).round(1)
        
        # Identify fast-moving vs slow-moving inventory
        fast_movers = product_metrics[
            (product_metrics['order_count'] >= 3) & 
            (product_metrics['avg_days_between_orders'] <= 30)
        ]
        
        slow_movers = product_metrics[
            (product_metrics['order_count'] <= 2) |
            (product_metrics['avg_days_between_orders'] > 60)
        ]
        
        # Calculate ABC analysis (Pareto principle)
        product_metrics['value_rank'] = product_metrics['total_value'].rank(ascending=False)
        total_value = product_metrics['total_value'].sum()
        product_metrics['value_percentage'] = (product_metrics['total_value'] / total_value * 100).round(2)
        product_metrics['cumulative_value_percentage'] = product_metrics['value_percentage'].cumsum()
        
        # ABC classification
        a_items = product_metrics[product_metrics['cumulative_value_percentage'] <= 80]
        b_items = product_metrics[
            (product_metrics['cumulative_value_percentage'] > 80) & 
            (product_metrics['cumulative_value_percentage'] <= 95)
        ]
        c_items = product_metrics[product_metrics['cumulative_value_percentage'] > 95]
        
        insights = {
            'analysis_date': datetime.now().isoformat(),
            'inventory_classification': {
                'a_items_count': len(a_items),
                'b_items_count': len(b_items),
                'c_items_count': len(c_items),
                'a_items_value_percentage': float(a_items['value_percentage'].sum()),
                'top_a_items': a_items.nlargest(10, 'total_value')[['description', 'total_value', 'order_count']].to_dict('records')
            },
            'turnover_analysis': {
                'fast_movers_count': len(fast_movers),
                'slow_movers_count': len(slow_movers),
                'avg_reorder_frequency_days': float(product_metrics['avg_days_between_orders'].mean()),
                'fastest_movers': fast_movers.nsmallest(10, 'avg_days_between_orders')[['description', 'avg_days_between_orders', 'order_count']].to_dict('records'),
                'slowest_movers': slow_movers.nlargest(10, 'avg_days_between_orders')[['description', 'avg_days_between_orders', 'order_count']].to_dict('records')
            },
            'demand_forecasting': {
                'predictable_demand_items': fast_movers[fast_movers['quantity_std'] < fast_movers['avg_quantity_per_order'] * 0.3].shape[0],
                'volatile_demand_items': product_metrics[product_metrics['quantity_std'] > product_metrics['avg_quantity_per_order']].shape[0]
            }
        }
        
        return insights
    
    async def reconcile_with_dabs_pricing(self, dabs_pricing_file: Optional[str] = None) -> Dict[str, Any]:
        """Reconcile order data with current DABS pricing to identify discrepancies"""
        
        if self.line_items_data is None:
            raise ValueError("No order data loaded. Run load_extracted_data() first.")
        
        logger.info("Reconciling order data with DABS pricing")
        
        reconciliation_result = {
            'reconciliation_date': datetime.now().isoformat(),
            'discrepancies': [],
            'matched_items': 0,
            'unmatched_items': 0,
            'price_differences': []
        }
        
        try:
            # Load latest DABS pricing file if provided
            if dabs_pricing_file:
                pricing_df = pd.read_excel(dabs_pricing_file)
            else:
                # Find latest DABS backup file
                dabs_backups = list((self.project_root / 'data/dabs_backups').glob('DABS Price Changes*.xlsx'))
                if dabs_backups:
                    latest_pricing = max(dabs_backups, key=lambda x: x.stat().st_mtime)
                    pricing_df = pd.read_excel(latest_pricing)
                    logger.info(f"Using DABS pricing file: {latest_pricing.name}")
                else:
                    logger.warning("No DABS pricing file found for reconciliation")
                    return reconciliation_result
            
            # Get latest order prices for each product
            latest_order_prices = self.line_items_data.loc[
                self.line_items_data.groupby('item_code')['delivery_date'].idxmax()
            ][['item_code', 'description', 'unit_price', 'delivery_date']]
            
            # Compare with DABS pricing
            for _, order_item in latest_order_prices.iterrows():
                item_code = order_item['item_code']
                order_price = float(order_item['unit_price'])
                
                # Find matching item in DABS pricing
                dabs_match = pricing_df[pricing_df['SKU'].astype(str) == str(item_code)]
                
                if not dabs_match.empty:
                    dabs_price = float(dabs_match.iloc[0]['RetailPrice'])
                    price_difference = order_price - dabs_price
                    percent_difference = (price_difference / dabs_price * 100) if dabs_price > 0 else 0
                    
                    reconciliation_result['matched_items'] += 1
                    
                    # Flag significant differences (>5%)
                    if abs(percent_difference) > 5:
                        discrepancy = {
                            'item_code': item_code,
                            'description': order_item['description'],
                            'order_price': order_price,
                            'dabs_price': dabs_price,
                            'difference': round(price_difference, 2),
                            'percent_difference': round(percent_difference, 2),
                            'last_order_date': order_item['delivery_date'].strftime('%Y-%m-%d'),
                            'severity': 'HIGH' if abs(percent_difference) > 20 else 'MEDIUM'
                        }
                        reconciliation_result['discrepancies'].append(discrepancy)
                        reconciliation_result['price_differences'].append({
                            'item_code': item_code,
                            'difference': price_difference,
                            'percent_difference': percent_difference
                        })
                else:
                    reconciliation_result['unmatched_items'] += 1
            
            logger.info(f"Reconciliation complete: {reconciliation_result['matched_items']} matched, {len(reconciliation_result['discrepancies'])} discrepancies found")
            
        except Exception as e:
            logger.error(f"Price reconciliation failed: {e}")
            reconciliation_result['error'] = str(e)
        
        return reconciliation_result
    
    async def generate_purchase_tracking_report(self) -> Dict[str, Any]:
        """Generate comprehensive purchase tracking and analysis report"""
        
        logger.info("Generating comprehensive purchase tracking report")
        
        # Load data if not already loaded
        if self.orders_data is None:
            await self.load_extracted_data()
        
        # Perform all analyses
        price_trends = await self.analyze_price_trends()
        purchase_patterns = await self.identify_purchase_patterns()
        inventory_insights = await self.generate_inventory_insights()
        price_alerts = await self.generate_price_variance_alerts()
        reconciliation = await self.reconcile_with_dabs_pricing()
        
        # Compile comprehensive report
        report = {
            'report_generated': datetime.now().isoformat(),
            'report_period': {
                'start_date': self.orders_data['delivery_date'].min().strftime('%Y-%m-%d') if not self.orders_data.empty else None,
                'end_date': self.orders_data['delivery_date'].max().strftime('%Y-%m-%d') if not self.orders_data.empty else None,
                'total_orders': len(self.orders_data) if self.orders_data is not None else 0,
                'total_line_items': len(self.line_items_data) if self.line_items_data is not None else 0
            },
            'executive_summary': {
                'total_spend': float(self.orders_data['total_cost'].sum()) if not self.orders_data.empty else 0,
                'avg_order_value': float(self.orders_data['total_cost'].mean()) if not self.orders_data.empty else 0,
                'unique_products_purchased': len(self.line_items_data['item_code'].unique()) if self.line_items_data is not None else 0,
                'high_variance_products': len([a for a in price_alerts if a['alert_level'] == 'HIGH']),
                'price_discrepancies': len(reconciliation.get('discrepancies', []))
            },
            'price_trends': {
                'trending_up': len([t for t in price_trends.values() if t.trend_direction == 'increasing']),
                'trending_down': len([t for t in price_trends.values() if t.trend_direction == 'decreasing']),
                'stable_prices': len([t for t in price_trends.values() if t.trend_direction == 'stable'])
            },
            'purchase_patterns': purchase_patterns,
            'inventory_insights': inventory_insights,
            'price_variance_alerts': price_alerts[:20],  # Top 20 alerts
            'price_reconciliation': reconciliation,
            'recommendations': self._generate_recommendations(price_trends, purchase_patterns, price_alerts)
        }
        
        return report
    
    def _generate_recommendations(self, price_trends: Dict[str, PriceTrend], 
                                purchase_patterns: Dict[str, Any], 
                                price_alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analysis"""
        
        recommendations = []
        
        # High-priority price variance recommendations
        high_variance_items = [alert for alert in price_alerts if alert['alert_level'] == 'HIGH']
        if high_variance_items:
            recommendations.append({
                'category': 'Price Management',
                'priority': 'HIGH',
                'title': 'Review High Price Variance Items',
                'description': f"{len(high_variance_items)} products show extreme price volatility (>50%)",
                'action': 'Review vendor contracts and consider price locks for volatile items',
                'affected_items': len(high_variance_items)
            })
        
        # Inventory optimization recommendations
        if purchase_patterns.get('frequency_categories', {}).get('high_frequency_products', 0) > 0:
            recommendations.append({
                'category': 'Inventory Optimization',
                'priority': 'MEDIUM',
                'title': 'Optimize High-Frequency Product Ordering',
                'description': f"Streamline ordering for {purchase_patterns['frequency_categories']['high_frequency_products']} frequently ordered products",
                'action': 'Consider bulk ordering or automatic reorder points for frequent items',
                'potential_savings': 'Reduce ordering overhead and potentially negotiate better prices'
            })
        
        # Single-purchase item review
        single_purchase_count = purchase_patterns.get('frequency_categories', {}).get('single_purchase_products', 0)
        if single_purchase_count > 50:
            recommendations.append({
                'category': 'Product Mix',
                'priority': 'LOW',
                'title': 'Review Single-Purchase Items',
                'description': f"{single_purchase_count} products ordered only once",
                'action': 'Evaluate if these items should be regular inventory or special orders',
                'potential_impact': 'Optimize inventory mix and reduce slow-moving stock'
            })
        
        return recommendations
    
    async def export_analysis_reports(self, report: Dict[str, Any]) -> Dict[str, str]:
        """Export analysis reports in multiple formats for easy review"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON report
        json_file = self.reports_dir / f"dabs_purchase_analysis_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Excel report with multiple sheets
        excel_file = self.reports_dir / f"dabs_purchase_analysis_{timestamp}.xlsx"
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Executive summary
            summary_df = pd.DataFrame([report['executive_summary']])
            summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
            
            # Price variance alerts
            if report['price_variance_alerts']:
                alerts_df = pd.DataFrame(report['price_variance_alerts'])
                alerts_df.to_excel(writer, sheet_name='Price Alerts', index=False)
            
            # Top products
            if report['purchase_patterns']['top_products']['by_total_value']:
                top_products_df = pd.DataFrame(report['purchase_patterns']['top_products']['by_total_value'])
                top_products_df.to_excel(writer, sheet_name='Top Products', index=False)
            
            # Recommendations
            if report['recommendations']:
                recommendations_df = pd.DataFrame(report['recommendations'])
                recommendations_df.to_excel(writer, sheet_name='Recommendations', index=False)
        
        # CSV summary for quick import
        csv_file = self.reports_dir / f"dabs_orders_summary_{timestamp}.csv"
        if self.orders_data is not None:
            self.orders_data.to_csv(csv_file, index=False)
        
        logger.info(f"Analysis reports exported to {self.reports_dir}")
        
        return {
            'json_report': str(json_file),
            'excel_report': str(excel_file),
            'csv_summary': str(csv_file) if self.orders_data is not None else None
        }

async def run_complete_analysis():
    """Run complete DABS order data analysis"""
    
    print("📊 DABS Invoice and Purchase Analysis System")
    print("=" * 60)
    print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    analyzer = DABSInvoiceAnalyzer()
    
    try:
        # Load extracted data
        print("📥 Loading extracted order data...")
        data_loaded = await analyzer.load_extracted_data()
        
        if not data_loaded:
            print("❌ No extracted data found. Run order extraction first.")
            return False
        
        # Generate comprehensive analysis
        print("🔍 Generating comprehensive purchase tracking report...")
        report = await analyzer.generate_purchase_tracking_report()
        
        # Export reports
        print("📊 Exporting analysis reports...")
        export_files = await analyzer.export_analysis_reports(report)
        
        # Display summary
        print(f"\n📋 ANALYSIS SUMMARY:")
        print(f"   Total Orders: {report['report_period']['total_orders']}")
        print(f"   Total Spend: ${report['executive_summary']['total_spend']:,.2f}")
        print(f"   Unique Products: {report['executive_summary']['unique_products_purchased']}")
        print(f"   High Variance Items: {report['executive_summary']['high_variance_products']}")
        print(f"   Price Discrepancies: {report['executive_summary']['price_discrepancies']}")
        
        print(f"\n📁 REPORTS GENERATED:")
        for report_type, file_path in export_files.items():
            if file_path:
                print(f"   ✅ {report_type}: {Path(file_path).name}")
        
        if report['recommendations']:
            print(f"\n💡 TOP RECOMMENDATIONS:")
            for rec in report['recommendations'][:3]:
                print(f"   {rec['priority']}: {rec['title']}")
        
        print(f"\n✅ Analysis completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        logger.error(f"Complete analysis failed: {e}")
        return False

async def main():
    """Main execution with command line options"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='DABS Order Automation and Analysis System')
    parser.add_argument('--extract', action='store_true', help='Extract order data from DABS system')
    parser.add_argument('--analyze', action='store_true', help='Analyze extracted order data')
    parser.add_argument('--days', type=int, default=90, help='Days of historical data to process')
    parser.add_argument('--schedule', action='store_true', help='Setup automated scheduling')
    
    args = parser.parse_args()
    
    if args.extract:
        # Run order extraction
        from .dabs_order_automation import DABSOrderAutomation
        automation = DABSOrderAutomation()
        result = await automation.run_complete_automation(args.days)
        return result['status'] == 'completed_success'
    
    elif args.analyze:
        # Run analysis on existing data
        return await run_complete_analysis()
    
    elif args.schedule:
        # Setup automated scheduling
        automation = DABSOrderAutomation()
        await automation.schedule_regular_extraction()
        print("✅ Automated scheduling configured")
        return True
    
    else:
        # Default: run both extraction and analysis
        print("🚀 Running complete DABS order automation and analysis...")
        
        # Extract data
        from .dabs_order_automation import DABSOrderAutomation
        automation = DABSOrderAutomation()
        extract_result = await automation.run_complete_automation(args.days)
        
        if extract_result['status'] == 'completed_success':
            # Analyze data
            analysis_result = await run_complete_analysis()
            return analysis_result
        else:
            print("❌ Extraction failed, skipping analysis")
            return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
