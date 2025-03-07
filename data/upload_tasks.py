import csv
import json
from arango import ArangoClient

def connect_to_arangodb(arango_url, db_name, username, password):
    client = ArangoClient(hosts=arango_url)
    db = client.db(
        db_name, username, password
    )
    
    return db

def upload_csv_to_arangodb(csv_file, db, collection_name, team):
    if not db.has_collection(collection_name):
        db.create_collection(collection_name)
    
    collection = db.collection(collection_name)
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        documents = [{"_id": f"{team}_tasks/{row['TaskID']}", **row} for row in reader]
    
    collection.import_bulk(documents)
    print(f"Successfully uploaded {len(documents)} records to {collection_name}.")

def upload_edges_to_arangodb(csv_file, db, edge_collection_name, team):
    if not db.has_collection(edge_collection_name):
        db.create_collection(edge_collection_name, edge=True)
    
    edge_collection = db.collection(edge_collection_name)
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        edges = []
        for row in reader:
            if row["PrecedingTasks"] == "":
                continue
            edges.append({"_from": f'{team}_tasks/{row["TaskID"]}', "_to": f'{team}_tasks/{row["PrecedingTasks"]}'})
    
    edge_collection.import_bulk(edges)
    print(f"Successfully uploaded {len(edges)} edges to {edge_collection_name}.")

# Example usage
if __name__ == "__main__":
    ARANGO_URL = 'https://b61c3b83bfe6.arangodb.cloud:8529'
    DB_NAME = 'DAC_devops_log'
    USERNAME = 'root'
    PASSWORD = 'RHr0KzkRUVlp61IisH8G'
    
    db = connect_to_arangodb(ARANGO_URL, DB_NAME, USERNAME, PASSWORD)
    team = "bi"
    folder = f"tasks/{team}/{team}"
    upload_csv_to_arangodb(f"{folder}_tasks.csv", db, f'{team}_tasks', team)
    upload_edges_to_arangodb(f"{folder}_tasks_dependence.csv", db, f'{team}_tasks_dependence', team)
