"""Seed ChromaDB with question bank (50+ questions across roles/difficulties)."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb
from ml.embeddings.embed_utils import generate_embeddings_batch

QUESTIONS = [
    {"id": "q-001", "text": "What is the virtual DOM and how does React use it?", "topic": "React", "difficulty": "easy", "category": "fundamentals", "keywords": "virtual DOM,reconciliation,diffing"},
    {"id": "q-002", "text": "Explain React hooks and when to use useState vs useReducer.", "topic": "React", "difficulty": "medium", "category": "fundamentals", "keywords": "hooks,useState,useReducer,state management"},
    {"id": "q-003", "text": "How does React Fiber improve rendering performance?", "topic": "React", "difficulty": "hard", "category": "architecture", "keywords": "fiber,concurrent rendering,scheduling,priority"},
    {"id": "q-004", "text": "What is the event loop in JavaScript?", "topic": "JavaScript", "difficulty": "easy", "category": "fundamentals", "keywords": "event loop,call stack,callback queue,microtask"},
    {"id": "q-005", "text": "Explain closures and their practical use cases.", "topic": "JavaScript", "difficulty": "medium", "category": "fundamentals", "keywords": "closure,scope,lexical environment"},
    {"id": "q-006", "text": "How does prototypal inheritance work in JavaScript?", "topic": "JavaScript", "difficulty": "medium", "category": "fundamentals", "keywords": "prototype,inheritance,__proto__,Object.create"},
    {"id": "q-007", "text": "What are generators and how do they differ from async/await?", "topic": "JavaScript", "difficulty": "hard", "category": "fundamentals", "keywords": "generator,yield,iterator,async"},
    {"id": "q-008", "text": "Explain TypeScript generics with an example.", "topic": "TypeScript", "difficulty": "medium", "category": "fundamentals", "keywords": "generics,type parameter,constraint"},
    {"id": "q-009", "text": "What is Node.js and how does it handle concurrent requests?", "topic": "Node.js", "difficulty": "easy", "category": "fundamentals", "keywords": "event loop,non-blocking,single thread"},
    {"id": "q-010", "text": "Explain the middleware pattern in Express.js.", "topic": "Node.js", "difficulty": "medium", "category": "architecture", "keywords": "middleware,request,response,next"},
    {"id": "q-011", "text": "How would you handle memory leaks in a Node.js application?", "topic": "Node.js", "difficulty": "hard", "category": "architecture", "keywords": "memory leak,heap,garbage collection,profiling"},
    {"id": "q-012", "text": "What is SQL injection and how do you prevent it?", "topic": "SQL", "difficulty": "easy", "category": "fundamentals", "keywords": "SQL injection,parameterized queries,prepared statements"},
    {"id": "q-013", "text": "Explain database normalization and its forms.", "topic": "SQL", "difficulty": "medium", "category": "fundamentals", "keywords": "normalization,1NF,2NF,3NF,BCNF"},
    {"id": "q-014", "text": "How do database indexes work and when would you use them?", "topic": "SQL", "difficulty": "medium", "category": "architecture", "keywords": "index,B-tree,query optimization,cardinality"},
    {"id": "q-015", "text": "What is Docker and why is containerization important?", "topic": "Docker", "difficulty": "easy", "category": "fundamentals", "keywords": "container,image,isolation,portability"},
    {"id": "q-016", "text": "Explain Docker Compose and multi-container applications.", "topic": "Docker", "difficulty": "medium", "category": "architecture", "keywords": "compose,services,networking,volumes"},
    {"id": "q-017", "text": "What is Kubernetes and how does it orchestrate containers?", "topic": "Kubernetes", "difficulty": "medium", "category": "fundamentals", "keywords": "pods,services,deployment,orchestration"},
    {"id": "q-018", "text": "Explain Python decorators with a practical example.", "topic": "Python", "difficulty": "medium", "category": "fundamentals", "keywords": "decorator,wrapper,function,syntax"},
    {"id": "q-019", "text": "What are Python generators and when would you use them?", "topic": "Python", "difficulty": "medium", "category": "fundamentals", "keywords": "generator,yield,lazy evaluation,memory"},
    {"id": "q-020", "text": "Explain the GIL in Python and its implications.", "topic": "Python", "difficulty": "hard", "category": "architecture", "keywords": "GIL,threading,multiprocessing,concurrency"},
    {"id": "q-021", "text": "What is REST and what makes an API RESTful?", "topic": "REST", "difficulty": "easy", "category": "fundamentals", "keywords": "REST,stateless,resources,HTTP methods"},
    {"id": "q-022", "text": "Compare REST vs GraphQL and their trade-offs.", "topic": "API Design", "difficulty": "medium", "category": "architecture", "keywords": "REST,GraphQL,over-fetching,schema"},
    {"id": "q-023", "text": "What is CSS Flexbox and when would you use it?", "topic": "CSS", "difficulty": "easy", "category": "fundamentals", "keywords": "flexbox,flex-direction,justify-content,align-items"},
    {"id": "q-024", "text": "Explain CSS Grid and how it differs from Flexbox.", "topic": "CSS", "difficulty": "medium", "category": "fundamentals", "keywords": "grid,template,areas,responsive"},
    {"id": "q-025", "text": "What is Git branching and what strategies do teams use?", "topic": "Git", "difficulty": "easy", "category": "fundamentals", "keywords": "branch,merge,rebase,git flow"},
    {"id": "q-026", "text": "What is CI/CD and why is it important?", "topic": "DevOps", "difficulty": "easy", "category": "fundamentals", "keywords": "continuous integration,continuous deployment,pipeline,automation"},
    {"id": "q-027", "text": "Explain microservices architecture and its trade-offs.", "topic": "System Design", "difficulty": "medium", "category": "architecture", "keywords": "microservices,monolith,service discovery,API gateway"},
    {"id": "q-028", "text": "How would you design a URL shortener?", "topic": "System Design", "difficulty": "medium", "category": "scenario", "keywords": "hashing,database,redirect,scaling"},
    {"id": "q-029", "text": "Design a real-time chat application.", "topic": "System Design", "difficulty": "hard", "category": "scenario", "keywords": "WebSocket,message queue,scaling,persistence"},
    {"id": "q-030", "text": "What is machine learning and how does supervised learning work?", "topic": "Machine Learning", "difficulty": "easy", "category": "fundamentals", "keywords": "supervised,training,features,labels"},
    {"id": "q-031", "text": "Explain overfitting and how to prevent it.", "topic": "Machine Learning", "difficulty": "medium", "category": "fundamentals", "keywords": "overfitting,regularization,cross-validation,dropout"},
    {"id": "q-032", "text": "What are transformers and how do they work?", "topic": "Deep Learning", "difficulty": "hard", "category": "architecture", "keywords": "attention,self-attention,encoder,decoder"},
    {"id": "q-033", "text": "Explain Redux state management pattern.", "topic": "React", "difficulty": "medium", "category": "architecture", "keywords": "store,reducer,action,dispatch"},
    {"id": "q-034", "text": "What is server-side rendering and its benefits?", "topic": "Next.js", "difficulty": "medium", "category": "fundamentals", "keywords": "SSR,hydration,SEO,performance"},
    {"id": "q-035", "text": "Explain AWS EC2 and when to use it.", "topic": "AWS", "difficulty": "easy", "category": "fundamentals", "keywords": "EC2,instance,AMI,scaling"},
    {"id": "q-036", "text": "What is AWS Lambda and serverless architecture?", "topic": "AWS", "difficulty": "medium", "category": "architecture", "keywords": "Lambda,serverless,function,cold start"},
    {"id": "q-037", "text": "Explain authentication vs authorization.", "topic": "Security", "difficulty": "easy", "category": "fundamentals", "keywords": "authentication,authorization,OAuth,JWT"},
    {"id": "q-038", "text": "What is JWT and how does it work?", "topic": "Security", "difficulty": "medium", "category": "fundamentals", "keywords": "JWT,token,claims,signature"},
    {"id": "q-039", "text": "Tell me about a time you resolved a conflict in your team.", "topic": "behavioral", "difficulty": "medium", "category": "behavioral", "keywords": "conflict,resolution,communication,compromise"},
    {"id": "q-040", "text": "Describe a project where you had to learn something new quickly.", "topic": "behavioral", "difficulty": "medium", "category": "behavioral", "keywords": "learning,adaptation,challenge,outcome"},
    {"id": "q-041", "text": "How do you prioritize tasks when you have multiple deadlines?", "topic": "behavioral", "difficulty": "medium", "category": "behavioral", "keywords": "prioritization,time management,communication,delegation"},
    {"id": "q-042", "text": "Tell me about a time you failed and what you learned.", "topic": "behavioral", "difficulty": "medium", "category": "behavioral", "keywords": "failure,lesson,growth,resilience"},
    {"id": "q-043", "text": "How do you approach code reviews?", "topic": "behavioral", "difficulty": "medium", "category": "behavioral", "keywords": "code review,feedback,quality,collaboration"},
    {"id": "q-044", "text": "Explain caching strategies and when to use them.", "topic": "System Design", "difficulty": "medium", "category": "architecture", "keywords": "cache,TTL,invalidation,CDN,Redis"},
    {"id": "q-045", "text": "What is load balancing and how does it work?", "topic": "System Design", "difficulty": "medium", "category": "architecture", "keywords": "load balancer,round robin,health check,scaling"},
    {"id": "q-046", "text": "Explain the CAP theorem.", "topic": "System Design", "difficulty": "hard", "category": "architecture", "keywords": "consistency,availability,partition tolerance,trade-offs"},
    {"id": "q-047", "text": "What is MongoDB and when would you choose it over SQL?", "topic": "MongoDB", "difficulty": "easy", "category": "fundamentals", "keywords": "NoSQL,document,schema-less,scalability"},
    {"id": "q-048", "text": "Explain Redis data structures and use cases.", "topic": "Redis", "difficulty": "medium", "category": "fundamentals", "keywords": "strings,lists,sets,hashes,pub/sub"},
    {"id": "q-049", "text": "What is Terraform and infrastructure as code?", "topic": "DevOps", "difficulty": "medium", "category": "fundamentals", "keywords": "IaC,Terraform,state,providers,modules"},
    {"id": "q-050", "text": "How does HTTPS work and what is TLS?", "topic": "Security", "difficulty": "medium", "category": "fundamentals", "keywords": "TLS,certificate,handshake,encryption"},
]


def get_chroma_client():
    """Get ChromaDB client — local persistent (no server needed)."""
    chroma_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_data")
    os.makedirs(chroma_dir, exist_ok=True)
    return chromadb.PersistentClient(path=chroma_dir)


def seed_questions():
    print(f"Seeding {len(QUESTIONS)} questions...")
    client = get_chroma_client()
    collection = client.get_or_create_collection(name="questions")

    documents = [q["text"] for q in QUESTIONS]
    ids = [q["id"] for q in QUESTIONS]
    metadatas = [{"topic": q["topic"], "difficulty": q["difficulty"], "category": q["category"], "keywords": q["keywords"]} for q in QUESTIONS]

    print("Generating embeddings...")
    embeddings = generate_embeddings_batch(documents)

    print("Upserting to ChromaDB...")
    for i in range(0, len(ids), 50):
        kwargs = {"ids": ids[i:i+50], "documents": documents[i:i+50], "metadatas": metadatas[i:i+50]}
        batch_emb = embeddings[i:i+50] if embeddings and embeddings[0] else None
        if batch_emb and all(e for e in batch_emb):
            kwargs["embeddings"] = batch_emb
        collection.upsert(**kwargs)

    print(f"✅ Seeded {len(ids)} questions into ChromaDB.")


if __name__ == "__main__":
    seed_questions()
