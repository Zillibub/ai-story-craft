# Installation

1. Fill out .env file
2. Run Docker compose 
3. Make migration with alembic 
4. Start a discord bot 


## Making migrations 

```
export $(grep -v '^#' .env | tr -d '\r' | xargs)
alembic revision --autogenerate -m <revision name> 
alembic upgrade head 
```