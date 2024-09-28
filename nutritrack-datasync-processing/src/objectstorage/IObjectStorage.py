from abc import ABC, abstractmethod

from src.nosqldatabase.ICloudDatabase import MethodNotImplementedException


class IObjectStorage(ABC):
    """
    Interface to define methods to handle object storage operations
    """

    @abstractmethod
    def stream_gzip_file_content_from_object_storage(self, file_name):
        raise MethodNotImplementedException("This method is not implemented")

    @abstractmethod
    def remove_file_from_object_storage(self, file_name):
        raise MethodNotImplementedException("This method is not implemented")