import boto3
from src.nosqldatabase.ICloudDatabase import ICloudDatabase

class AWSDynamoDBConnector(ICloudDatabase):
    """
    Class which has operations specific to AWS Dynamo DB
    """

    # Declare empty variables
    table = None

    def __init__(self, table_name):
        """
        The constructor takes AWS dynamo db table name and initializes an object
        :param table_name: name of the table for which dynamodb object should be initialized
        """
        try:
            dynamo_db = boto3.resource('dynamodb', region_name='us-east-1')
            self.table = dynamo_db.Table(table_name)
        except Exception as e:
            print(f'Error connecting to dynamo db: {e}')

    def save_to_db(self, items):
        """
        This method will save data to AWS dynamo db and returns the response
        If there is an exception during the save operation, an error is thrown
        :param items: Json object which will be stored to AWS dynamo db
        :return: records_added, records_in_error, total_records: Tuple of records added and records in error
        """
        records_added = 0
        records_in_error = 0
        total_records = 0
        with self.table.batch_writer() as batch:
            for item in items:
                try:
                    batch.put_item(Item=item)
                    records_added = records_added+1
                except Exception as e:
                    print(f'Exception {e} occurred while processing {item}')
                    records_in_error = records_in_error + 1
            total_records = total_records+1

        return records_added, records_in_error, total_records

    def get_from_db(self, key):
        """
        This method will get the data from AWS dynamo db and returns the response
        If there is an exception during the get operation, an error is thrown
        :param key: Json object with key: value pair to retrieve data from AWS dynamo db
        :return: Any: response from aws dynamo db
        """
        try:
            response = self.table.get_item(Key=key)
            item = response['Item']
            return item
        except Exception as e:
            print(f'Error getting item: {e}')
