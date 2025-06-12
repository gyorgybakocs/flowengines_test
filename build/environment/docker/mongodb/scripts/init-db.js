print('--- Initializing MongoDB for Langflow/TIS ---');

db = db.getSiblingDB(process.env.MONGO_INITDB_DATABASE || 'fetest-mongodb');

print('--> Creating application database: ' + db.getName());

// Create collections for common use cases
print('--> Creating documents collection...');
db.createCollection('documents', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["source", "content", "created_at"],
            properties: {
                source: {
                    bsonType: "string",
                    description: "Source of the document (required)"
                },
                content: {
                    bsonType: "string",
                    description: "Document content (required)"
                },
                metadata: {
                    bsonType: "object",
                    description: "Additional metadata (optional)"
                },
                created_at: {
                    bsonType: "date",
                    description: "Creation timestamp (required)"
                }
            }
        }
    }
});

print('--> Creating chat_sessions collection...');
db.createCollection('chat_sessions', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["created_at"],
            properties: {
                user_id: {
                    bsonType: "string",
                    description: "User identifier (optional)"
                },
                metadata: {
                    bsonType: "object",
                    description: "Session metadata (optional)"
                },
                created_at: {
                    bsonType: "date",
                    description: "Creation timestamp (required)"
                }
            }
        }
    }
});

print('--> Creating chat_messages collection...');
db.createCollection('chat_messages', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["session_id", "is_from_user", "content", "created_at"],
            properties: {
                session_id: {
                    bsonType: "objectId",
                    description: "Reference to chat_sessions._id (required)"
                },
                is_from_user: {
                    bsonType: "bool",
                    description: "True if message from user, false if from AI (required)"
                },
                content: {
                    bsonType: "string",
                    description: "Message content (required)"
                },
                created_at: {
                    bsonType: "date",
                    description: "Creation timestamp (required)"
                }
            }
        }
    }
});

print('--> Creating indexes...');

db.documents.createIndex({ "source": 1 });
db.documents.createIndex({ "created_at": -1 });
db.documents.createIndex({ "metadata.type": 1 });

db.chat_sessions.createIndex({ "user_id": 1 });
db.chat_sessions.createIndex({ "created_at": -1 });

db.chat_messages.createIndex({ "session_id": 1 });
db.chat_messages.createIndex({ "created_at": -1 });
db.chat_messages.createIndex({ "session_id": 1, "created_at": 1 });

print('--> Creating application user...');
db.createUser({
    user: "langflow_user",
    pwd: "langflow_password",
    roles: [
        {
            role: "readWrite",
            db: db.getName()
        }
    ]
});

print('--- MongoDB initialization complete ---');
print('Database: ' + db.getName());
print('Collections created: documents, chat_sessions, chat_messages');
print('Application user: langflow_user');
print('Ready for Langflow integration!');
