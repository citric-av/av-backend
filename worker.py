import redis
from rq import Worker, Queue, Connection
import os

# Queues we want our workers to listen to
listen = ['default']

# URL for our Redis server
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Create a connection to Redis
conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
