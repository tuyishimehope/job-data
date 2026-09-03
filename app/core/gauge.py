class Gauge:
    def __init__(self) -> None:
        self.value = 0

    def increment(self, amount: int = 1) -> None:
        self.value += amount

    def decrement(self, amount: int = 1) -> None:
        self.value -= amount

    def get(self) -> int:
        return self.value