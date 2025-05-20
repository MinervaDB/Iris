# Iris
MinervaDB Iris is a specialized toolkit for MongoDB replication that allows asymmetric delete operations between source and target databases. This enables organizations to maintain different retention policies across their database infrastructure - specifically designed for environments requiring 6-month retention at source and 18-month retention at target.
Key Features

Selective Delete Propagation: Prevents delete operations from propagating from source to target
Differential Retention Policies: Supports 6-month retention at source and 18-month retention at target
Change Stream Monitoring: Uses MongoDB's change streams to capture operations in real-time
Automated Purging: Implements automated purging based on configurable retention policies
Audit Trail: Maintains comprehensive logs of all replication activities
Monitoring Dashboard: Web-based interface for monitoring replication status and health
Alert System: Configurable alerts for replication lag, failures, or other issues

## Architecture

MinervaDB Iris consists of the following components:

Replication Controller: Core component managing the replication process
Change Stream Listener: Monitors the source database for changes
Operation Filter: Filters out delete operations
Operation Transformer: Transforms operations as needed before applying to target
Target Applier: Applies filtered operations to the target database
Retention Manager: Enforces differential retention policies
Monitoring Service: Tracks replication metrics and health
Administration API: RESTful API for configuration and management

### Installation

**** Prerequisites

* MongoDB 4.2+ (source and target)
* Python 3.8+
* pip (Python package manager)
* Linux-based system (recommended)
