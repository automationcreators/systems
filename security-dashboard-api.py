#!/usr/bin/env python3
"""
Security Dashboard API
Provides JSON API for security dashboard HTML interface
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# Import the security monitoring dashboard
sys.path.insert(0, str(Path(__file__).parent))
import importlib.util
spec = importlib.util.spec_from_file_location("security_monitor", Path(__file__).parent / "security-monitoring-dashboard.py")
security_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(security_module)

class SecurityDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.dashboard = security_module.SecurityMonitoringDashboard()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/api/security':
            self.handle_security_api()
        elif parsed_path.path == '/api/scan':
            self.handle_scan_api()
        elif parsed_path.path.endswith('.html') or parsed_path.path == '/':
            # Serve the dashboard HTML
            if parsed_path.path == '/':
                self.path = '/security-dashboard.html'
            super().do_GET()
        else:
            super().do_GET()
    
    def handle_security_api(self):
        """Handle security dashboard API request"""
        try:
            # Get dashboard data
            dashboard_data = self.dashboard.get_security_dashboard_data()
            
            # Convert to JSON
            response = json.dumps(dashboard_data, indent=2)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response.encode())
            
        except Exception as e:
            self.send_error(500, f"Security API Error: {str(e)}")
    
    def handle_scan_api(self):
        """Handle security scan API request"""
        try:
            # Run new security scan
            report = self.dashboard.generate_comprehensive_security_report()
            
            # Get dashboard data
            dashboard_data = self.dashboard.get_security_dashboard_data()
            
            response = {
                "status": "scan_complete",
                "scan_time": report["generated_at"],
                "data": dashboard_data
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            self.send_error(500, f"Scan API Error: {str(e)}")

def generate_dashboard_json():
    """Generate dashboard JSON data and save to file"""
    dashboard = security_module.SecurityMonitoringDashboard()
    
    # Get dashboard data
    dashboard_data = dashboard.get_security_dashboard_data()
    
    # Save to JSON file
    json_file = Path(__file__).parent / "security-dashboard-data.json"
    with open(json_file, 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    print(f"✅ Dashboard data saved to: {json_file}")
    return dashboard_data

def start_dashboard_server(port=8080):
    """Start HTTP server for security dashboard"""
    import os
    
    # Change to systems directory to serve files
    os.chdir(Path(__file__).parent)
    
    httpd = HTTPServer(('localhost', port), SecurityDashboardHandler)
    
    print(f"🌐 Security Dashboard Server starting on http://localhost:{port}")
    print(f"📊 Dashboard available at: http://localhost:{port}/")
    print(f"🔧 API endpoints:")
    print(f"   • http://localhost:{port}/api/security (get current data)")
    print(f"   • http://localhost:{port}/api/scan (run new scan)")
    print("Press Ctrl+C to stop server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.shutdown()

def main():
    """CLI interface for security dashboard API"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Security Dashboard API")
    parser.add_argument("--action", choices=["serve", "generate", "test"], required=True)
    parser.add_argument("--port", type=int, default=8080, help="Server port")
    
    args = parser.parse_args()
    
    try:
        if args.action == "serve":
            start_dashboard_server(args.port)
        
        elif args.action == "generate":
            data = generate_dashboard_json()
            print("📊 Dashboard Data Summary:")
            print(f"  Overall Score: {data['security_overview']['overall_score']}/100")
            print(f"  Total Projects: {data['security_overview']['total_projects']}")
            print(f"  Critical Issues: {data['issue_summary']['critical']}")
            print(f"  Status: {data['security_overview']['status'].upper()}")
        
        elif args.action == "test":
            # Test the API
            dashboard = security_module.SecurityMonitoringDashboard()
            data = dashboard.get_security_dashboard_data()
            
            print("🧪 Security Dashboard API Test:")
            print("=" * 40)
            print(f"Overall Score: {data['security_overview']['overall_score']}")
            print(f"Projects: {data['security_overview']['total_projects']}")
            print(f"Critical Issues: {data['issue_summary']['critical']}")
            print(f"Vault Files: {data['vault_status']['encrypted_files']}")
            
            if data['top_recommendations']:
                print("\nTop Recommendations:")
                for rec in data['top_recommendations'][:3]:
                    print(f"  • {rec}")
            
            print("\nTop Projects by Security Score:")
            for project in data['recent_projects'][:5]:
                status_icon = "🔴" if project['status'] == 'critical' else "⚠️" if project['status'] == 'warning' else "✅"
                print(f"  {status_icon} {project['name']}: {project['score']}/100")
            
            print("\n✅ API test completed successfully")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()