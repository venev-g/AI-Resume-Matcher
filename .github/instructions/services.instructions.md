---
applyTo: "backend/services/**/*.py"
---

# Database & External Services Instructions

## Service Layer Architecture
Services handle all external integrations (Pinecone, MongoDB, LLM APIs).

## Pinecone Vector Database Service

### Connection Pattern
```python
from pinecone import Pinecone, ServerlessSpec
import os

class PineconeService:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        self._initialize_index()
    
    def _initialize_index(self):
        # Check if index exists before creating
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=768,  # Gemini embedding dimension
                metric='cosine',
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )
        self.index = self.pc.Index(self.index_name)
```

### Operations
- **Upsert**: Use batch upserts (100 vectors at a time) for performance
- **Query**: Include metadata for filtering
- **Delete**: Clean up old embeddings when resumes are updated
- **Metadata**: Store resume_id, candidate_name, upload_date

### Best Practices
- Always **check index existence** before operations
- Use **namespace** for multi-tenant scenarios (optional)
- Implement **retry logic** for network errors
- Monitor **usage metrics** (free tier: 100k vectors)

## MongoDB Atlas Service

### Connection Pattern
```python
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
import os

class MongoDBService:
    def __init__(self):
        # Use async client for non-blocking I/O
        self.client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
        self.db = self.client[os.getenv("MONGODB_DATABASE")]
        self.matches_collection = self.db["match_results"]
        self.evaluations_collection = self.db["evaluations"]
```

### Operations
- **Insert**: Use insert_one() for single docs, insert_many() for bulk
- **Update**: Use update_one() with upsert=True for idempotency
- **Query**: Use find() with projection for large docs
- **Aggregation**: Use pipeline for complex analytics

### Indexing
```python
# Create indexes on startup
await self.matches_collection.create_index("timestamp")
await self.matches_collection.create_index("jd_text")
await self.matches_collection.create_index([("jd_text", "text")])
```

### Best Practices
- Use **async operations** (motor) in FastAPI
- Implement **connection pooling** (automatic with motor)
- Add **TTL indexes** for temporary data
- Handle **connection errors** gracefully
- Close connections on **app shutdown**

## Error Handling Pattern
```python
from pymongo.errors import ConnectionFailure, OperationFailure

async def store_match_result(self, result: Dict):
    try:
        inserted = await self.matches_collection.insert_one(result)
        return str(inserted.inserted_id)
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise ServiceUnavailableError("Database temporarily unavailable")
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed: {e}")
        raise DatabaseError("Failed to store results")
```

## Environment Variables
Required for all services:
- PINECONE_API_KEY
- PINECONE_ENVIRONMENT
- PINECONE_INDEX_NAME
- MONGODB_URI
- MONGODB_DATABASE

Load and validate on startup.