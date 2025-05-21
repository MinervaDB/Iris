class OperationFilter:
    def __init__(self, excluded_operations=None):
        """
        Initialize the operation filter
        
        Parameters:
        -----------
        excluded_operations : list
            List of operation types to exclude (e.g., ["delete"])
        """
        self.excluded_operations = excluded_operations or []
        
    def should_process(self, change_event):
        """
        Determine if an operation should be processed or filtered out
        
        Parameters:
        -----------
        change_event : dict
            MongoDB change event document
            
        Returns:
        --------
        bool
            True if the operation should be processed, False otherwise
        """
        operation_type = change_event['operationType']
        
        # Check if operation type is in exclusion list
        if operation_type in self.excluded_operations:
            return False
            
        return True
