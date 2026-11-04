from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
     model_config=SettingsConfigDict(env_file=".env",env_file_encoding="utf-8")
     database_url:str
     secret_key:SecretStr
     algorithm:str="HS256"
     access_token_expire_minute:int=30
     refresh_token_expire_minutes: int = 60 * 24 * 7 
settings=Settings()