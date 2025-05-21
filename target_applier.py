import logging
from pymongo.errors import PyMongoError

class TargetApplier:
    def __init__(self, target_db):
        """
        Initialize the target applier
        
        Parameters:
        -----------
        target_db : pymongo.database.Database
            Target MongoDB database
        """
        self.target_db = target_db
        self.logger = logging.getLogger("iris.target_applier")
        
    def apply(self, collection_name, operation):
        """
        Apply an operation to the target database
        
        Parameters:
        -----------
        collection_name : str
            Name of the collection
        operation : dict
            Transformed operation to apply
            
        Returns:
        --------
        dict
            Result of the operation with success flag and error if applicable
        """
        try:
            collection = self.target_db[collection_name]
            operation_type = operation['operationType']
            
            if operation_type == 'insert':
                document = operation['fullDocument']
                result = collection.insert_one(document)
                return {'success': True, 'result': str(result.inserted_id)}
                
            elif operation_type == 'update':
                document_id = operation['documentKey']['_id']
                update_doc = operation['updateDescription']['updatedFields']
                result = collection.update_one(
                    {'_id': document_id},
                    {'$set': update_doc}
                )
                return {'success': True, 'matched': result.matched_count, 'modified': result.modified_count}
                
            elif operation_type == 'replace':
                document_id = operation['documentKey']['_id']
                document = operation['fullDocument']
                result = collection.replace_one(
                    {'_id': document_id},
                    document
                )
                return {'success': True, 'matched': result.matched_count, 'modified': result.modified_count}
                
            # Note: We explicitly don't handle 'delete' here since it's filtered out
            # But we include this for completeness in case filtering is changed
            else:
                return {'success': False, 'error': f"Unsupported operation type: {operation_type}"}
                
        except PyMongoError as e:
            self.logger.error(f"Failed to apply operation to target: {str(e)}")
            return {'success': False, 'error': str(e)}
