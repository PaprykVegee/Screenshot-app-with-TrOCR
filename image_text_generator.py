import sys
import random
from polish_text_generator import TextGenerator
import io
from datasets import load_dataset
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import os
import textwrap

class ImageTextGenerator:
    def __init__(self, model_name, fonts_folder, max_lines=4, max_width=800, random_state=None):
        self.topicks = [
            "Podróż do", "Historia o", "Przyszłość", "Tajemnica", "Rozmowa z", 
            "Spotkanie w", "Opowieść o", "Ciekawostka z", "Nieznane miejsce", "Eksperyment z"
        ]
        self.places = [
            "kosmosie", "górach", "oceanie", "dżungli", "mieście", "przyszłości", 
            "przeszłości", "innej planecie", "zamku", "starożytnym Egipcie"
        ]
        self.heros = [
            "naukowcem", "kosmitą", "robotem", "człowiekiem", "zwierzęciem", "superbohaterem", 
            "duchem", "wampirem", "dzieckiem", "starożytnym bogiem"
        ]
        self.actions = [
            "rozwiązuje zagadkę", "walczy o przetrwanie", "ucieka przed wrogiem", "poszukuje skarbu", 
            "odkrywa nowe technologie", "ratuje świat", "przeżywa niezwykłe przygody", "rozmawia z nieznanym", 
            "buduje coś niesamowitego", "zmienia historię"
        ]
        self.generator = TextGenerator(model_name=model_name)
        self.fonts_folder = fonts_folder
        self.max_lines = max_lines
        self.max_width = max_width

        # Set random state for reproducibility
        self.random_state = random_state
        if self.random_state is not None:
            random.seed(self.random_state)

    def generate_prompt(self):
        topick = random.choice(self.topicks)
        place = random.choice(self.places)
        hero = random.choice(self.heros)
        action = random.choice(self.actions)

        return f"{topick} {place}, gdzie {hero} {action}."

    def generate_texts(self, num_texts=15, max_len=50):
        text_list = []
        for _ in range(num_texts):
            prompt = self.generate_prompt()
            text = self.generator.generate_text(prompt, max_len=max_len)
            text_list.append(text)
        return text_list

    def create_image_from_text(self, text):
        font_file = os.path.join(self.fonts_folder, os.listdir(self.fonts_folder)[0])
        font = ImageFont.truetype(font_file, 40)
        
        temp_image = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(temp_image)

        wrapped_text = textwrap.wrap(text, width=self.max_width // 20)

        if len(wrapped_text) > self.max_lines:
            wrapped_text = wrapped_text[:self.max_lines]

        total_height = 0
        line_height = font.getbbox("Hg")[3] - font.getbbox("Hg")[1]

        for line in wrapped_text:
            total_height += line_height

        image = Image.new("RGB", (self.max_width, total_height + 20), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        y_text = 10
        for line in wrapped_text:
            draw.text((10, y_text), line, font=font, fill=(0, 0, 0))
            y_text += line_height

        return image

    def create_images(self, text_list):
        images = []
        for text in text_list:
            image = self.create_image_from_text(text)
            images.append(image)
        return images

    def load_english_dataset(self):
        df_english = load_dataset("Teklia/IAM-line")
        return df_english['train'].to_pandas()

    def bytes_to_PIL(self, image):
        image = image['bytes']
        return Image.open(io.BytesIO(image))

    def process_english_dataset(self, df_english):
        df_english['image'] = df_english['image'].apply(self.bytes_to_PIL)
        return df_english

    def create_polish_dataframe(self, text_list, image_list):
        return pd.DataFrame({
            "image": image_list,
            "text": text_list
        })

    def combine_datasets(self, df_polish, df_english):
        return pd.concat([df_english, df_polish])

    def generate_data(self):
        # Generate Polish text and images
        text_list = self.generate_texts()
        image_list = self.create_images(text_list)
        df_polish = self.create_polish_dataframe(text_list, image_list)

        # Load and process English dataset
        df_english = self.load_english_dataset()
        df_english = self.process_english_dataset(df_english)

        # Combine both datasets
        combined_df = self.combine_datasets(df_polish, df_english)
        return combined_df
