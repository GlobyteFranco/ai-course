# Asegurarse de probar esto
from transformers import pipeline

generator = pipeline(
    "text-generation", 
    model="gpt2"
)

print(generator("Artificial Intelligence is", max_length=20))