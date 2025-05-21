import logging
import threading
import time
from pymongo.errors import PyMongoError

class ChangeStreamListener(threading.Thread):
    def __init__(self, source_collection, operation_filter, operation_transformer, target_applier, monitoring_service):
        super().__init__()
        self.daemon = True
        self.source_collection = source_collection
        self.operation_filter = operation_filter
        self.operation_transformer = operation_transformer
        self.target_applier = target_applier
        self.monitoring_service = monitoring_service
        self.logger = logging.getLogger(f"iris.listener.{source_collection.name}")
        self.running = False
        self.change_stream = None
        
    def run(self):
        self.running = True
        self.logger.info(f"Starting change stream listener for {self.source_collection.name}")
        
        while self.running:
            try:
                # Open change stream
                self.change_stream = self.source_collection.watch(
                    full_document='updateLookup',
                    max_await_time_ms=1000
                )
                
                # Process changes
                while self.running and self.change_stream.alive:
                    change = next(self.change_stream, None)
                    if change:
                        self._process_change(change)
                    else:
                        time.sleep(0.1)  # Small sleep to prevent high CPU usage
                        
            except PyMongoError as e:
                self.logger.error(f"Change stream error: {str(e)}")
                self.monitoring_service.record_error(
                    collection=self.source_collection.name,
                    error_type="change_stream",
                    message=str(e)
                )
                time.sleep(5)  # Wait before reconnecting
                
            finally:
                if self.change_stream:
                    self.change_stream.close()
                    
        self.logger.info(f"Change stream listener stopped for {self.source_collection.name}")
        
    def _process_change(self, change):
        """Process a single change event"""
        operation_type = change['operationType']
        
        # Record operation
        self.monitoring_service.record_operation(
            collection=self.source_collection.name,
            operation_type=operation_type
        )
        
        # Filter operation
        if not self.operation_filter.should_process(change):
            self.logger.debug(f"Filtered out {operation_type} operation")
            return
            
        # Transform operation
        transformed_op = self.operation_transformer.transform(change)
        
        # Apply to target
        result = self.target_applier.apply(
            collection_name=self.source_collection.name,
            operation=transformed_op
        )
        
        if result.get('success'):
            self.logger.debug(f"Successfully applied {operation_type} to target")
        else:
            self.logger.error(f"Failed to apply {operation_type}: {result.get('error')}")
            self.monitoring_service.record_error(
                collection=self.source_collection.name,
                error_type="apply_operation",
                message=result.get('error')
            )
        
    def stop(self):
        """Stop the change stream listener"""
        self.running = False
        if self.change_stream:
            self.change_stream.close()
