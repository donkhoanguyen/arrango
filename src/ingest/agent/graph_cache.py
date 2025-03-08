import nx_arangodb as nxadb
from arango.database import StandardDatabase

class GraphWrapper:
    def __init__(self, db: StandardDatabase, graph: nxadb.DiGraph, name: str, schema: dict[str, str], description: str):
        self.db = db
        self.graph = graph
        self.name = name
        self.schema = schema
        self.description = description
    
    def __repr__(self):
        return f"NetworkX DiGraph with name '{self.name}', schema: {self.schema}, and overall description: {self.description}"

    def load_graph(self):
        if self.graph is not None:
            print(f"Graph with name {self.graph} is already loaded!")
            return
        
        self.graph = nxadb.DiGraph(name=self.name, db=self.db)
