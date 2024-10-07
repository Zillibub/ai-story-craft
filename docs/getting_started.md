# Installation

1. Fill out .env file
2. Run Docker compose 
3. Make migration with alembic 
4. Start a telegram bot 


## Making migrations 

```
export POSTGRES_USER=<postgres username>
export POSTGRES_PASSWORD=<postgres password>
export POSTGRES_DB=<db name>  
alembic revision --autogenerate -m <revision name> 
alembic upgrade head 
```