from dotenv import load_dotenv
import os

load_dotenv() 

API_URL = os.environ.get("API_URL")
API_TOKEN = os.environ.get("API_TOKEN")
# REDIS
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_NUM_DB = os.environ.get("REDIS_NUM_DB")
REDIS_PORT = os.environ.get("REDIS_PORT")
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_NUM_DB}'