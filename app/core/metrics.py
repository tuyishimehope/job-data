class Counter:
    def __init__(self) -> None:
        self.values: dict[tuple, int] = {}

    def increment(
        self,
        labels: tuple,
        amount: int = 1,
    ) -> None:
        self.values[labels] = (
            self.values.get(labels, 0) + amount
        )

    def get(self) -> dict[tuple, int]:
        return self.values