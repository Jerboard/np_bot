from asyncio import run
from os import environ

from dotenv import load_dotenv

load_dotenv(dotenv_path='./docker/.env')

environ['DB_HOST'] = 'localhost'
environ['REDIS_HOST'] = 'localhost'

from main import main
run(main())
