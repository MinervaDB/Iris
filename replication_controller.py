import logging
import time
from pymongo import MongoClient
from .change_stream_listener import ChangeStreamListener
from .operation_filter import OperationFilter
from .operation_transformer import OperationTransformer
from .target_applier import TargetApplier
from .monitoring_service import MonitoringService

class ReplicationController:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("iris.replication_controller")
        
        # Initialize components
        self.source_client = MongoClient(config['source']['uri'])
        self.target_client = MongoClient(config['target']['uri'])
        
        self.source_db = self.source_client[config['source']['database']]
        self.target_db = self.target_client[config['target']['database']]
        
        self.operation_filter = OperationFilter(config['replication']['exclude_operations'])
        self.operation_transformer = OperationTransformer()
        self.target_applier = TargetApplier(self.target_db)
        
        self.monitoring_service = MonitoringService(config['monitoring'])
        
        self.listeners = {}
        
    def start(self):
        """Start the replication process for all configured collections"""
        self.logger.info("Starting MinervaDB Iris replication")
        
        # Create collections in target if they don't exist
        self._prepare_target_collections()
        
        # Start monitoring service
        self.monitoring_service.start()
        
        # Start change stream listeners for each collection
        for collection_config in self.config['replication']['collections']:
            collection_name = collection_config['name']
            self._start_collection_replication(collection_name)
            
        self.logger.info("Replication started for all collections")
        
    def _prepare_target_collections(self):
        """Ensure target collections exist with proper indexes"""
        for collection_config in self.config['replication']['collections']:
            collection_name = collection_config['name']
            
            # Create collection if it doesn't exist
            if collection_name not in self.target_db.list_collection_names():
                self.target_db.create_collection(collection_name)
                
            # Create indexes
            target_collection = self.target_db[collection_name]
            for index_config in collection_config.get('indexes', []):
                target_collection.create_index(**index_config)
                
            self.logger.info(f"Prepared target collection: {collection_name}")
            
    def _start_collection_replication(self, collection_name):
        """Start replication for a specific collection"""
        # Create and start listener
        source_collection = self.source_db[collection_name]
        
        listener = ChangeStreamListener(
            source_collection,
            self.operation_filter,
            self.operation_transformer,
            self.target_applier,
            self.monitoring_service
        )
        
        listener.start()
        self.listeners[collection_name] = listener
        self.logger.info(f"Started replication for collection: {collection_name}")
        
    def stop(self):
        """Stop all replication processes"""
        for name, listener in self.listeners.items():
            listener.stop()
            self.logger.info(f"Stopped replication for collection: {name}")
            
        self.monitoring_service.stop()
        self.logger.info("Stopped MinervaDB Iris replication")
