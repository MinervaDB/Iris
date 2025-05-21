# Iris
MinervaDB Iris is a specialized toolkit for MongoDB replication that allows asymmetric delete operations between source and target databases. This enables organizations to maintain different retention policies across their database infrastructure - specifically designed for environments requiring 6-month retention at source and 18-month retention at target.


## Key Features

* Selective Delete Propagation: Prevents delete operations from propagating from source to target
* Differential Retention Policies: Supports 6-month retention at source and 18-month retention at target
* Change Stream Monitoring: Uses MongoDB's change streams to capture operations in real-time
* Automated Purging: Implements automated purging based on configurable retention policies
* Audit Trail: Maintains comprehensive logs of all replication activities
* Monitoring Dashboard: Web-based interface for monitoring replication status and health
* Alert System: Configurable alerts for replication lag, failures, or other issues

## Architecture

MinervaDB Iris consists of the following components:

* Replication Controller: Core component managing the replication process
* Change Stream Listener: Monitors the source database for changes
* Operation Filter: Filters out delete operations
* Operation Transformer: Transforms operations as needed before applying to target
* Target Applier: Applies filtered operations to the target database
* Retention Manager: Enforces differential retention policies
* Monitoring Service: Tracks replication metrics and health
* Administration API: RESTful API for configuration and management

### Installation

 #### Prerequisites

* MongoDB 4.2+ (source and target)
* Python 3.8+
* pip (Python package manager)
* Linux-based system (recommended)


### Setup

```

# Clone the repository
git clone https://github.com/minervadb/iris.git
cd iris

# Install dependencies
pip install -r requirements.txt

# Configure the application
cp config/example.yaml config/config.yaml
# Edit config.yaml with your MongoDB connection details

# Run the setup script
./setup.sh

```

The main dependencies include:

* pymongo (for MongoDB connectivity)
* pyyaml (for configuration parsing)
* Flask (for the admin API)

### 2. Configuration
Create your configuration file by copying the example:

``` cp config/example.yaml config/config.yaml ```

Then edit the configuration file to match your environment:

```

source:
  uri: "mongodb://username:password@source-mongodb:27017"
  database: "production"
  auth_source: "admin"
  retention_days: 180  # 6 months

target:
  uri: "mongodb://username:password@target-mongodb:27017"
  database: "archive"
  auth_source: "admin"
  retention_days: 540  # 18 months

replication:
  collections:
    - name: "orders"
      indexes:
        - keys: {"timestamp": 1}
          options: {"expireAfterSeconds": 15552000}  # 180 days
    - name: "transactions"
      indexes:
        - keys: {"created_at": 1}
          options: {"expireAfterSeconds": 15552000}  # 180 days
  
  batch_size: 1000
  max_lag_seconds: 300
  exclude_operations: ["delete"]

monitoring:
  port: 8080
  log_level: "info"
  metrics_retention_days: 30
  alert_email: "dba@example.com"

```

Make sure to:

* Specify the correct MongoDB connection URIs
* List all collections you want to replicate
* Define timestamp fields for each collection (needed for retention policies)
* Set appropriate retention periods (in days)

### 3. Running the Application

Start MinervaDB Iris:

``` ./iris.py --config config/config.yaml  ```

You should see the MinervaDB Iris banner and log messages indicating that replication has started.

For production use, you may want to set it up as a service:

```

# Example systemd service file (save as /etc/systemd/system/minervadb-iris.service)
[Unit]
Description=MinervaDB Iris MongoDB Replication Service
After=network.target

[Service]
User=mongodb
WorkingDirectory=/opt/minervadb-iris
ExecStart=/opt/minervadb-iris/iris.py --config /opt/minervadb-iris/config/config.yaml
Restart=on-failure

[Install]
WantedBy=multi-user.target

```

Then activate the service:

```
sudo systemctl enable minervadb-iris
sudo systemctl start minervadb-iris

```

### 4. Monitoring

Access the monitoring dashboard by opening a web browser and navigating to:

```
http://your-server:8080/
```

This dashboard provides:

* Real-time replication status
* Operation counts by collection and type
* Error logs and alerts
* Performance metrics

### 5. Administration
   
You can manage MinervaDB Iris using the REST API:

#### View Status

```

curl http://your-server:8080/api/status

```

#### Add a Collection

```

curl -X POST http://your-server:8080/api/collections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new_collection",
    "indexes": [
      {
        "keys": {"created_at": 1},
        "options": {"expireAfterSeconds": 15552000}
      }
    ]
  }'

```

#### Remove a Collection

```

curl -X DELETE http://your-server:8080/api/collections/collection_name

```

### 6. Checking Replication Status

To verify that replication is working properly:

1. Insert a document into a source collection

```
db.orders.insertOne({
  order_id: "ORD123456",
  customer: "Example Corp",
  items: [...],
  timestamp: new Date()
})

```

2. Verify it appears in the target database

```
db.orders.findOne({order_id: "ORD123456"})

```

3. Test delete filtering by removing from source

```
db.orders.deleteOne({order_id: "ORD123456"})

```

4. Verify the document still exists in target

```
db.orders.findOne({order_id: "ORD123456"})

```

## 7. Retention Testing

The retention policies operate on a schedule (daily by default). To test:

1. Insert documents with timestamps in the past

```
// In source database
db.orders.insertOne({
  order_id: "OLD-ORD-123",
  timestamp: new Date(Date.now() - (200 * 24 * 60 * 60 * 1000))  // 200 days old
})

```

2. Wait for the next retention cycle or trigger manually:

```
curl http://your-server:8080/api/retention/run

```

3. The document should be removed from source (> 180 days) but remain in target (< 540 days)

## Troubleshooting

If you encounter issues:

1. Check logs:

```
tail -f iris.log

```

2. Verify MongoDB connectivity:

```
mongo $SOURCE_URI
mongo $TARGET_URI

```

3. Ensure change streams are enabled (requires replica sets)
4. Verify network connectivity between the Iris server and both MongoDB instances

#### For additional assistance, contact support@minervadb.com.



# Administration API
The MinervaDB Iris toolkit also includes a RESTful API for administration and configuration. This allows for programmatic control of the replication process.

## API Endpoints

* GET /api/status: Get overall replication status
* GET /api/collections: List all collections being replicated
* GET /api/collections/{name}: Get details for a specific collection
* POST /api/collections: Add a new collection to replication
* DELETE /api/collections/{name}: Remove a collection from replication
* GET /api/metrics: Get replication metrics
* POST /api/config: Update configuration

## Best Practices

### 1. Database Security:

* Use TLS/SSL for all MongoDB connections
* Implement authentication for both source and target databases
* Create dedicated users with appropriate privileges


### 2. Performance Optimization:

* Monitor replication lag and adjust batch sizes accordingly
* Index fields used in retention policies
* Consider hardware requirements for high-throughput scenarios


### 3. Monitoring:

* Set up alerts for replication errors or excessive lag
* Monitor disk space on the target database
* Review logs regularly


### 4. Backup:

* Implement regular backups of both source and target databases
* Test restoration procedures periodically



# Troubleshooting

## Common Issues

### 1. Replication Lag:

* Check network connectivity between source and target
* Increase batch size for higher throughput
* Verify source server is not overloaded


### 2. Authentication Failures:

* Verify credentials in configuration
* Check that users have appropriate privileges
* Ensure authentication database is correctly specified


### 3. Data Inconsistency:

* Check for errors in operation transformation
* Verify indexes match between source and target
* Use validation tools to compare databases



## Support
For customization, enhancements, or support, please contact:

* Email: support@minervadb.com
* Website: https://minervadb.com

### License

MinervaDB Iris is licensed under GNU General Public License v3.0.
Copyright © 2010-2025. All Rights Reserved by MinervaDB®.
