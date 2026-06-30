import json
import os
from typing import Dict, Any

class SharedMemoryBus:
    def __init__(self, storage_file: str = "memory.json"):
        self.storage_file = storage_file
        self.memory = {
            "business_context_memory": {},
            "leads_memory": [],
            "campaign_memory": {},
            "proposal_memory": {},
            "analytics_memory": {}
        }
        self.load()

    def load(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                try:
                    self.memory = json.load(f)
                except json.JSONDecodeError:
                    pass

    def save(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.memory, f, indent=2)

    def write(self, segment: str, data: Any):
        if segment not in self.memory:
            raise ValueError(f"Unknown memory segment: {segment}")
        self.memory[segment] = data
        self.save()

    def append(self, segment: str, data: Any):
        if segment not in self.memory:
            raise ValueError(f"Unknown memory segment: {segment}")
        if not isinstance(self.memory[segment], list):
            raise ValueError(f"Memory segment {segment} is not a list")
        self.memory[segment].append(data)
        self.save()

    def read(self, segment: str) -> Any:
        return self.memory.get(segment)

# Global singleton for the memory bus
memory_bus = SharedMemoryBus()
