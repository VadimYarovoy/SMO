from utils.singleton import Singleton


class Timer(metaclass=Singleton):
  """TODO"""

  current_time: float = 0

  def get_current_time(self) -> float:
    return self.current_time

  def set_current_time(self, time: float) -> None:
    self.current_time = time
