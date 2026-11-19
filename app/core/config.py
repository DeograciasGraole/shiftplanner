from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
     model_config=SettingsConfigDict(env_file=".env",env_file_encoding="utf-8")
     database_url:str
     secret_key:SecretStr
     resend_api_key: SecretStr
     resend_from_email: str

     infobip_api_key: SecretStr
     infobip_base_url: str
     infobip_whatsapp_sender: str

     algorithm:str="HS256"
     access_token_expires_minute:int=30
     refresh_token_expires_days: int = 7
     # refresh_token_expire_: int = 60 * 24 * 7 
settings=Settings()