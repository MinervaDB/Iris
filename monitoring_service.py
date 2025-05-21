import logging
import threading
import time
import datetime
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pymongo import MongoClient

class MonitoringService:
    def __init__(self, config):
        """
        Initialize the monitoring service
        
        Parameters:
        -----------
        config : dict
            Monitoring configuration
        """
        self.config = config
        self.logger = logging.getLogger("iris.monitoring")
        
        # Use in-memory storage for metrics
        self.metrics = {
            'operations': {},  # Collection -> operation type -> count
            'errors': [],      # List of error records
            'status': {
                'start_time': datetime.datetime.utcnow(),
                'collections': {}  # Collection status
            }
        }
        
        # Web server for monitoring
        self.server = None
        self.server_thread = None
        
    def start(self):
        """Start the monitoring service"""
        # Start HTTP server
        server_address = ('', self.config['port'])
        self.server = HTTPServer(server_address, lambda *args: MonitoringRequestHandler(self, *args))
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        self.logger.info(f"Monitoring service started on port {self.config['port']}")
        
    def stop(self):
        """Stop the monitoring service"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join()
            self.logger.info("Monitoring service stopped")
            
    def record_operation(self, collection, operation_type):
        """Record an operation in the metrics"""
        if collection not in self.metrics['operations']:
            self.metrics['operations'][collection] = {}
            
        if operation_type not in self.metrics['operations'][collection]:
            self.metrics['operations'][collection][operation_type] = 0
            
        self.metrics['operations'][collection][operation_type] += 1
        
        # Update collection status
        if collection not in self.metrics['status']['collections']:
            self.metrics['status']['collections'][collection] = {}
            
        self.metrics['status']['collections'][collection]['last_operation'] = {
            'type': operation_type,
            'timestamp': datetime.datetime.utcnow()
        }
        
    def record_error(self, collection, error_type, message):
        """Record an error in the metrics"""
        error_record = {
            'collection': collection,
            'error_type': error_type,
            'message': message,
            'timestamp': datetime.datetime.utcnow()
        }
        
        self.metrics['errors'].append(error_record)
        
        # Keep only recent errors (30 days)
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        self.metrics['errors'] = [e for e in self.metrics['errors'] if e['timestamp'] > cutoff]
        
        # Update collection status
        if collection not in self.metrics['status']['collections']:
            self.metrics['status']['collections'][collection] = {}
            
        self.metrics['status']['collections'][collection]['last_error'] = {
            'type': error_type,
            'message': message,
            'timestamp': datetime.datetime.utcnow()
        }

class MonitoringRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, monitoring_service, *args):
        self.monitoring_service = monitoring_service
        super().__init__(*args)
        
    def do_GET(self):
        """Handle GET requests for monitoring data"""
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Convert datetime objects to strings for JSON serialization
            metrics_copy = self._prepare_metrics_for_json(self.monitoring_service.metrics)
            
            self.wfile.write(json.dumps(metrics_copy).encode())
            
        elif self.path == '/':
            # Serve a simple HTML dashboard
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = self._generate_dashboard_html()
            self.wfile.write(html.encode())
            
        else:
            self.send_response(404)
            self.end_headers()
            
    def _prepare_metrics_for_json(self, metrics):
        """Prepare metrics for JSON serialization by converting datetime objects to strings"""
        if isinstance(metrics, dict):
            result = {}
            for key, value in metrics.items():
                result[key] = self._prepare_metrics_for_json(value)
            return result
        elif isinstance(metrics, list):
            return [self._prepare_metrics_for_json(item) for item in metrics]
        elif isinstance(metrics, datetime.datetime):
            return metrics.isoformat()
        else:
            return metrics
            
    def _generate_dashboard_html(self):
        """Generate a simple HTML dashboard for monitoring"""
        # This would be a more comprehensive HTML in a real implementation
        # Just a simple example here
        metrics = self._prepare_metrics_for_json(self.monitoring_service.metrics)
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MinervaDB Iris Monitoring</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #2c3e50; }
                .card { background: #f8f9fa; border-radius: 5px; padding: 15px; margin-bottom: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                .error { color: red; }
            </style>
        </head>
        <body>
            <h1>MinervaDB Iris Monitoring Dashboard</h1>
            
            <div class="card">
                <h2>Status</h2>
                <p>Started: {start_time}</p>
                <p>Uptime: {uptime}</p>
            </div>
            
            <div class="card">
                <h2>Collections</h2>
                <table>
                    <tr>
                        <th>Collection</th>
                        <th>Last Operation</th>
                        <th>Last Error</th>
                    </tr>
                    {collection_rows}
                </table>
            </div>
            
            <div class="card">
                <h2>Recent Errors</h2>
                <table>
                    <tr>
                        <th>Timestamp</th>
                        <th>Collection</th>
                        <th>Error Type</th>
                        <th>Message</th>
                    </tr>
                    {error_rows}
                </table>
            </div>
            
            <script>
                // Refresh the page every 30 seconds
                setTimeout(function() {
                    location.reload();
                }, 30000);
            </script>
        </body>
        </html>
        """
        
        # Calculate uptime
        start_time = datetime.datetime.fromisoformat(metrics['status']['start_time'])
        uptime = datetime.datetime.utcnow() - start_time
        uptime_str = f"{uptime.days} days, {uptime.seconds // 3600} hours, {(uptime.seconds // 60) % 60} minutes"
        
        # Generate collection rows
        collection_rows = ""
        for collection, status in metrics['status'].get('collections', {}).items():
            last_op = status.get('last_operation', {})
            last_error = status.get('last_error', {})
            
            last_op_str = f"{last_op.get('type', 'N/A')} at {last_op.get('timestamp', 'N/A')}" if last_op else "N/A"
            last_error_str = f"{last_error.get('type', 'N/A')} at {last_error.get('timestamp', 'N/A')}: {last_error.get('message', '')}" if last_error else "None"
            
            collection_rows += f"""
            <tr>
                <td>{collection}</td>
                <td>{last_op_str}</td>
                <td class="error">{last_error_str}</td>
            </tr>
            """
            
        # Generate error rows
        error_rows = ""
        for error in metrics.get('errors', []):
            error_rows += f"""
            <tr>
                <td>{error['timestamp']}</td>
                <td>{error['collection']}</td>
                <td>{error['error_type']}</td>
                <td>{error['message']}</td>
            </tr>
            """
            
        return html.format(
            start_time=metrics['status']['start_time'],
            uptime=uptime_str,
            collection_rows=collection_rows,
            error_rows=error_rows
        )
