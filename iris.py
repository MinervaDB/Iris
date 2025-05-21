#!/usr/bin/env python3
import os
import sys
import logging
import yaml
import argparse
import signal
from replication_controller import ReplicationController
from retention_manager import RetentionManager

def setup_logging(config):
    """Set up logging based on configuration"""
    log_level = getattr(logging, config['monitoring']['log_level'].upper())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('iris.log')
        ]
    )

def load_config(config_path):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description='MinervaDB Iris: MongoDB Replication with Differential Retention')
    parser.add_argument('-c', '--config', default='config/config.yaml', help='Path to configuration file')
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Set up logging
    setup_logging(config)
    
    logger = logging.getLogger("iris.main")
    logger.info("Starting MinervaDB Iris")
    
    # Print banner
    print("""
    ╔═══════════════════════════════════════════════╗
    ║                MinervaDB Iris                 ║
    ║                                               ║
    ║      MongoDB Replication with Differential    ║
    ║                Retention Policies             ║
    ║                                               ║
    ║      Copyright © 2010-2025. MinervaDB®        ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    # Initialize components
    replication_controller = ReplicationController(config)
    retention_manager = RetentionManager(config)
    
    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        retention_manager.stop()
        replication_controller.stop()
        logger.info("MinervaDB Iris stopped")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start components
        replication_controller.start()
        retention_manager.start()
        
        # Keep running until interrupted
        signal.pause()
        
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
