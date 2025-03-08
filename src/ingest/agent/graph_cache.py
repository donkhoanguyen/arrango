import nx_arangodb as nxadb

class GraphWrapper:
    def __init__(self, graph: nxadb.DiGraph, name: str, schema: dict[str, str], description: str):
        self.graph = graph
        self.name = name
        self.schema = schema
        self.description = description
    
    def __repr__(self):
        return f"NetworkX DiGraph with name '{self.name}', schema: {self.schema}, and overall description: {self.description}"
