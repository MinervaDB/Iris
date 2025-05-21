import copy
import datetime

class OperationTransformer:
    def __init__(self):
        """Initialize the operation transformer"""
        pass
        
    def transform(self, change_event):
        """
        Transform a change event before applying to target
        
        Parameters:
        -----------
        change_event : dict
            MongoDB change event document
            
        Returns:
        --------
        dict
            Transformed operation
        """
        # Create a deep copy to avoid modifying the original event
        transformed = copy.deepcopy(change_event)
        
        # Add metadata about the replication
        if 'fullDocument' in transformed and transformed['fullDocument']:
            transformed['fullDocument']['_minervadb_iris_metadata'] = {
                'replicated_at': datetime.datetime.utcnow(),
                'source_operation_type': transformed['operationType'],
                'source_timestamp': transformed.get('clusterTime')
            }
            
        return transformed
