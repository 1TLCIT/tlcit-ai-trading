from neo4j import GraphDatabase, basic_auth
from sentence_transformers import SentenceTransformer
import glob
import logging

logging.basicConfig(
    filename='neo4j_ingest.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

URI = "bolt://neo4j:7687"
USER = "neo4j"
PASSWORD = "yourpassword"

driver = GraphDatabase.driver(URI, auth=basic_auth(USER, PASSWORD))
model = SentenceTransformer('all-MiniLM-L6-v2')

BATCH_SIZE = 50

def ingest_batch(tx, batch):
    query = '''
    UNWIND $batch AS record
    MERGE (c:Case {id: record.id})
    SET c.text = record.text,
        c.embedding = record.embedding
    '''
    tx.run(query, batch=batch)

def ingest_all_judgments(folder_path='judgments'):
    files = glob.glob(f"{folder_path}/*.txt")
    batch = []

    for file in files:
        case_id = file.rsplit('/', 1)[-1].replace('.txt', '')
        try:
            with open(file, 'r') as f:
                text = f.read()
            emb = model.encode(text).tolist()
            batch.append({'id': case_id, 'text': text, 'embedding': emb})

            if len(batch) >= BATCH_SIZE:
                with driver.session() as session:
                    session.write_transaction(ingest_batch, batch)
                logging.info(f"Ingested batch of {len(batch)} cases")
                batch.clear()

        except Exception as e:
            logging.error(f"Error processing {file}: {e}")

    if batch:
        with driver.session() as session:
            session.write_transaction(ingest_batch, batch)
        logging.info(f"Ingested final batch of {len(batch)} cases")

if __name__ == "__main__":
    logging.info("Starting Neo4j ingestion")
    ingest_all_judgments()
    logging.info("Completed Neo4j ingestion")
