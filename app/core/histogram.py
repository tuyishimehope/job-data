class Histogram:
    def __init__(self, buckets: list[float]) -> None:
        self.buckets = sorted(buckets)
        self.counts = {
            bucket: 0
            for bucket in self.buckets
        }

        self.count = 0
        self.sum = 0.0

    def observe(self, value: float) -> None:
        self.count += 1
        self.sum += value

        for bucket in self.buckets:
            if value <= bucket:
                self.counts[bucket] += 1

    def get(self) -> dict:
        return {
            "count": self.count,
            "sum": self.sum,
            "buckets": self.counts,
        }