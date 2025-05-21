import logging
import threading
import time
import datetime
from pymongo import MongoClient

class RetentionManager:
    def __init__(self, config):
        """
        Initialize the retention manager
        
        Parameters:
        -----------
        config : dict
            Application configuration
        """
        self.config = config
        self.logger = logging.getLogger("iris.retention_manager")
        
        self.source_client = MongoClient(config['source']['uri'])
        self.target_client = MongoClient(config['target']['uri'])
        
        self.source_db = self.source_client[config['source']['database']]
        self.target_db = self.target_client[config['target']['database']]
        
        self.source_retention_days = config['source']['retention_days']
        self.target_retention_days = config['target']['retention_days']
        
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the retention manager thread"""
        if self.thread and self.thread.is_alive():
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("Retention manager started")
        
    def stop(self):
        """Stop the retention manager thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=30)
        self.logger.info("Retention manager stopped")
        
    def _run(self):
        """Main retention manager loop"""
        while self.running:
            try:
                # Process source retention
                self._process_source_retention()
                
                # Process target retention
                self._process_target_retention()
                
            except Exception as e:
                self.logger.error(f"Error in retention manager: {str(e)}")
                
            # Sleep until next retention cycle (daily check is reasonable)
            # But we check more frequently to allow for clean shutdown
            for _ in range(24):  # Check every hour for 24 hours
                if not self.running:
                    break
                time.sleep(3600)  # 1 hour
                
    def _process_source_retention(self):
        """Apply retention policy to source database"""
        self.logger.info(f"Applying {self.source_retention_days} day retention policy to source")
        
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=self.source_retention_days)
        
        # Process each collection
        for collection_config in self.config['replication']['collections']:
            collection_name = collection_config['name']
            collection = self.source_db[collection_name]
            
            # Find the timestamp field (first indexed field with expireAfterSeconds)
            timestamp_field = None
            for index_config in collection_config.get('indexes', []):
                if 'expireAfterSeconds' in index_config.get('options', {}):
                    timestamp_field = next(iter(index_config['keys']))
                    break
                    
            if not timestamp_field:
                self.logger.warning(f"No timestamp field found for retention in {collection_name}")
                continue
                
            # Delete old documents
            result = collection.delete_many({timestamp_field: {'$lt': cutoff_date}})
            self.logger.info(f"Deleted {result.deleted_count} documents from source {collection_name}")
                
    def _process_target_retention(self):
        """Apply retention policy to target database"""
        self.logger.info(f"Applying {self.target_retention_days} day retention policy to target")
        
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=self.target_retention_days)
        
        # Process each collection
        for collection_config in self.config['replication']['collections']:
            collection_name = collection_config['name']
            collection = self.target_db[collection_name]
            
            # Find the timestamp field (first indexed field with expireAfterSeconds)
            timestamp_field = None
            for index_config in collection_config.get('indexes', []):
                if 'expireAfterSeconds' in index_config.get('options', {}):
                    timestamp_field = next(iter(index_config['keys']))
                    break
                    
            if not timestamp_field:
                self.logger.warning(f"No timestamp field found for retention in {collection_name}")
                continue
                
            # Delete old documents
            result = collection.delete_many({timestamp_field: {'$lt': cutoff_date}})
            self.logger.info(f"Deleted {result.deleted_count} documents from target {collection_name}")
