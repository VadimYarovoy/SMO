from utils.singleton import Singleton
class Marker(metaclass=Singleton):

    id: int = 0

    def get_id(self) -> int:
        i = self.id
        self.id += 1
        return i
