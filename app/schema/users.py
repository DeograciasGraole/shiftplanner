from pydantic import BaseModel, EmailStr,ConfigDict,Field
class UserBase(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    email:EmailStr
   