# polish_text_generator.py
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class TextGenerator():
    def __init__(self, model_name):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)

        # Sprawdza, czy dostępne jest GPU
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)

    def generate_text(self, prompt, max_len=100, temperature=1.0, top_k=50, top_p=0.95):
        input_ids = self.tokenizer.encode(prompt, return_tensors='pt').to(self.device)

        # Generowanie tekstu z dodatkowymi parametrami kontroli
        output = self.model.generate(
            input_ids,
            max_length=max_len,
            temperature=temperature,  # Kontroluje losowość generacji
            top_k=top_k,              # Ogranicza wybór do top-k najbardziej prawdopodobnych tokenów
            top_p=top_p,              # Używa nucleus sampling (top-p) dla większej kontroli nad generacją
            do_sample=True,           # Aktywuje sampling, zamiast najbardziej prawdopodobnych predykcji
            num_return_sequences=1     # Ilość sekwencji do wygenerowania
        )

        generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        return generated_text
