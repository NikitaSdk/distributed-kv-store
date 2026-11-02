import hashlib
from bisect import bisect

class ConsistentHashRing:
    def __init__(self, replicas=100):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []

    def _hash(self, key: str):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node):
        for i in range(self.replicas):
            key = self._hash(f"{node}-{i}")
            self.ring[key] = node
            self.sorted_keys.append(key)
        self.sorted_keys.sort()

    def remove_node(self, node):
        for i in range(self.replicas):
            key = self._hash(f"{node}-{i}")
            del self.ring[key]
            self.sorted_keys.remove(key)

    def get_node(self, item_key):
        if not self.ring:
            return None

        hash_val = self._hash(item_key)
        idx = bisect(self.sorted_keys, hash_val) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[idx]]


hash_ring = ConsistentHashRing()
