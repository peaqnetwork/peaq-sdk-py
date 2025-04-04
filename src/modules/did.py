from src.modules.base import Base
from src.types.common import ChainType, SDKMetadata


class Did(Base):
    def __init__(self, api, metadata) -> None:
        super().__init__()
        self._api = api
        self.__metadata: SDKMetadata = metadata
    def create():
        pass
    def read():
        pass
    def update():
        pass
    def remove():
        pass