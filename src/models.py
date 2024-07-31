from typing import List, Dict, Tuple, Union, Literal, Optional, Sequence, AnyStr
from enum import Enum
from functools import partial
import ollama

class ModelFamilies(Enum):
    MIXTRAL = "mixtral"
    GEMMA_2 = "gemma2"
    LLAMA_3_1 = "llama3.1"
    MISTRAL_NEMO = "mistral-nemo"
    MISTRAL_LARGE = "mistral-large"

model_family_dict: Dict[ModelFamilies, Tuple[List[str], str]] = {
    ModelFamilies.MIXTRAL: (["latest", "8x7b", "8x22b"], "https://mistral.ai/news/mixtral-of-experts/"),
    ModelFamilies.GEMMA_2: (["latest", "9b", "27b"], "https://blog.google/technology/developers/google-gemma-2/"),
    ModelFamilies.LLAMA_3_1: (["latest", "8b", "70b", "405b"], "https://ai.meta.com/blog/meta-llama-3-1/"),
    ModelFamilies.MISTRAL_NEMO: (["latest", "12b"], "https://mistral.ai/news/mistral-nemo/"),
    ModelFamilies.MISTRAL_LARGE: (["latest", "123b"], "https://mistral.ai/news/mistral-large-2407/")
}

class BaseModel:
    def __init__(self, family_name: str, size: str) -> None:
        self.family_name = family_name
        self.size = size
        self.name = f"{self.family_name}:{self.size}"
    def __repr__(self) -> str:
        return f"{self.name}"
    def __str__(self) -> str:
        return f"{self.name}"

class ModelFamily:
    def __init__(self, family: ModelFamilies) -> None:
        self.name = family.value
        self.dict = model_family_dict[family]
        self.sizes = self.dict[0]
        self.info = self.dict[1]
        self.models = [BaseModel(self.name, size) for size in self.sizes]
    def __repr__(self) -> str:
        return f"{self.name}"
    def __str__(self) -> str:
        return f"The {self.name} family of models is available in the following sizes: {', '.join(self.sizes)} to learn more visit {self.info}"


# List of ModelFamily instances
model_families_list = [ModelFamily(family) for family in ModelFamilies]

# Dictionary of BaseModel instances
base_models_dict = {family.name: family.models for family in model_families_list}

class Paramater:
    def __init__(self, name: str, value: Union[str, int, float], short_name: str = None) -> None:
        self.name = name
        self.value = value
        self.short_name = short_name if short_name else name
    def __repr__(self) -> str:
        return f"PARAMETER {self.name} {self.value}"
    def __str__(self) -> str:
        return f"PARAMETER {self.name} {self.value}"

class System:
    def __init__(self, id: int, name: str, message: str) -> None:
        self.id = id
        self.name = name
        self.message = message
    def __repr__(self) -> str:
        return f'SYSTEM """{self.message}"""'
    def __str__(self) -> str:
        return f'SYSTEM """{self.message}"""'

class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    EMPTY = "empty"

class Message:
    def __init__(self, id: int, role: Role, message: str, name: str = None) -> None:
        self.id = id
        self.name = name
        self.message = message
        self.role = role
    def __repr__(self) -> str:
        return f'MESSAGE {self.role} {self.message}'
    def __str__(self) -> str:
        return f'MESSAGE {self.message}'

class Model(BaseModel):
    def __init__(
        self,
        base_model:BaseModel,
        paramaters: List[Paramater] = None, 
        ) -> None:
        # model
        super().__init__(base_model.family_name, base_model.size)
        self.paramaters = paramaters
        
    def __repr__(self) -> str:
        ret = f'{self.base_model}'
        if self.paramaters:
            ret += f'_P({",".join([f"{param.short_name}={param.value}" for param in self.paramaters])})'
        if self.system:
            ret += f'_S({self.system.id})'
        if self.format != '' and self.format:
            ret += f'_F({self.format})'
        return ret
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def options(self):
        options = dict()
        for param in self.paramaters:
            options[param.name] = param.value
        return options