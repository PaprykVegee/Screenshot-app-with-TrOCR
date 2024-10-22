import tkinter as tk
from PIL import Image, ImageTk, ImageGrab, ImageEnhance, ImageDraw
import io
import win32clipboard as clipboard
import threading
import keyboard
from transformers import VisionEncoderDecoderModel, TrOCRProcessor
import torch 

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
model_path = r"C:\Users\patry\Desktop\Models\TROCR_IAM"
model = VisionEncoderDecoderModel.from_pretrained(model_path)


class ScreenshotApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Ukryj główne okno Tkinter
        self.drawing_mode = False
        self.line_mode = False
        self.draw_start_x = self.draw_start_y = self.draw_end_x = self.draw_end_y = 0
        self.last_cropped_image_tk = None
        self.canvas = None
        self.rect = None
        self.menu_frame = None
        self.normal_screenshot = None
        self.draw_image = None
        self.draw_button = None  # Przyciski do rysowania
        self.line_start_x = self.line_start_y = 0

    def open_fullscreen_window_with_screenshot(self):
        # Utwórz okno tkinter
        fullscreen_window = tk.Toplevel(self.root)
        fullscreen_window.attributes('-fullscreen', True)
        fullscreen_window.overrideredirect(1)

        # Zrób zrzut ekranu (po utworzeniu okna tkinter)
        self.normal_screenshot = ImageGrab.grab()
        self.draw_image = self.normal_screenshot.copy()

        # Przyciemnij zrzut ekranu
        enhancer = ImageEnhance.Brightness(self.normal_screenshot)
        dark_screenshot = enhancer.enhance(0.3)  # Przyciemnienie o 70%

        # Konwersja obrazów na format zgodny z Tkinterem
        dark_screenshot_tk = ImageTk.PhotoImage(dark_screenshot)
        normal_screenshot_tk = ImageTk.PhotoImage(self.normal_screenshot)

        # Utwórz canvas do rysowania
        self.canvas = tk.Canvas(fullscreen_window, width=fullscreen_window.winfo_screenwidth(), height=fullscreen_window.winfo_screenheight())
        self.canvas.pack()

        # Wyświetl przyciemniony obraz na całym ekranie
        self.canvas.create_image(0, 0, anchor=tk.NW, image=dark_screenshot_tk)

        # Dodaj przycisk rysowania
        self.draw_button = tk.Button(fullscreen_window, text="Rysuj", command=self.toggle_drawing_mode, bg="black", fg="white")
        self.draw_button.pack(padx=10, pady=10, side=tk.LEFT)

        # Dodaj przycisk rysowania linii
        self.line_button = tk.Button(fullscreen_window, text="Rysuj linię", command=self.toggle_line_mode, bg="black", fg="white")
        self.line_button.pack(padx=10, pady=10, side=tk.LEFT)

        # Zmienna na prostokąt
        self.rect = None
        self.menu_frame = None  # Referencja do menu, które pojawi się po zaznaczeniu

        # Obsługa rysowania prostokąta
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

        # Obsługa skrótów klawiszowych
        fullscreen_window.bind('<Escape>', lambda e: fullscreen_window.destroy())

        # Uruchom główną pętlę tkinter
        fullscreen_window.mainloop()

    def on_activate(self):
        # Uruchom funkcję odpowiedzialną za tworzenie okna i zrzut ekranu
        threading.Thread(target=lambda: self.root.after(0, self.open_fullscreen_window_with_screenshot), daemon=True).start()

    def toggle_drawing_mode(self):
        self.drawing_mode = not self.drawing_mode
        if self.drawing_mode:
            self.draw_button.config(bg="green")  # Zmien kolor na zielony
            self.canvas.bind("<ButtonPress-1>", self.start_drawing)
            self.canvas.bind("<B1-Motion>", self.draw_line)
            self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        else:
            self.draw_button.config(bg="black")  # Zmien kolor na czarny
            self.canvas.bind("<ButtonPress-1>", self.on_button_press)
            self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def toggle_line_mode(self):
        self.line_mode = not self.line_mode
        if self.line_mode:
            self.line_button.config(bg="green")  # Zmien kolor na zielony
            self.canvas.bind("<ButtonPress-1>", self.start_line_drawing)
            self.canvas.bind("<B1-Motion>", self.draw_line_in_progress)
            self.canvas.bind("<ButtonRelease-1>", self.stop_line_drawing)
        else:
            self.line_button.config(bg="black")  # Zmien kolor na czarny
            self.canvas.bind("<ButtonPress-1>", self.on_button_press)
            self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def start_drawing(self, event):
        if self.drawing_mode:
            self.draw_start_x = event.x
            self.draw_start_y = event.y

    def draw_line(self, event):
        if self.drawing_mode:
            end_x, end_y = event.x, event.y
            self.canvas.create_line(self.draw_start_x, self.draw_start_y, end_x, end_y, fill="red", width=2)
            draw = ImageDraw.Draw(self.draw_image)
            draw.line([(self.draw_start_x, self.draw_start_y), (end_x, end_y)], fill="red", width=2)
            self.draw_start_x, self.draw_start_y = end_x, end_y

    def stop_drawing(self, event):
        if self.drawing_mode:
            end_x, end_y = event.x, event.y
            self.canvas.create_line(self.draw_start_x, self.draw_start_y, end_x, end_y, fill="red", width=2)
            draw = ImageDraw.Draw(self.draw_image)
            draw.line([(self.draw_start_x, self.draw_start_y), (end_x, end_y)], fill="red", width=2)
            self.drawing_mode = False
            self.draw_button.config(bg="black")  # Przywróć kolor przycisku na czarny

    def start_line_drawing(self, event):
        if self.line_mode:
            self.line_start_x = event.x
            self.line_start_y = event.y

    def draw_line_in_progress(self, event):
        if self.line_mode:
            end_x, end_y = event.x, event.y
            self.canvas.delete('line_id')
            self.canvas.create_line(self.line_start_x, self.line_start_y, end_x, end_y, fill="red", width=2, tags='line_id')

    def stop_line_drawing(self, event):
        if self.line_mode:
            end_x, end_y = event.x, event.y
            self.canvas.create_line(self.line_start_x, self.line_start_y, end_x, end_y, fill="red", width=2)
            draw = ImageDraw.Draw(self.draw_image)
            draw.line([(self.line_start_x, self.line_start_y), (end_x, end_y)], fill="red", width=2)
            self.line_mode = False
            self.line_button.config(bg="black")  # Przywróć kolor przycisku na czarny

    def on_button_press(self, event):
        if not (self.drawing_mode or self.line_mode):
            self.draw_start_x = event.x
            self.draw_start_y = event.y
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = None
            if self.menu_frame:
                self.menu_frame.destroy()

    def on_mouse_drag(self, event):
        if not (self.drawing_mode or self.line_mode):
            end_x, end_y = event.x, event.y
            if self.rect:
                self.canvas.delete(self.rect)
            self.rect = self.canvas.create_rectangle(self.draw_start_x, self.draw_start_y, end_x, end_y, outline="red", width=2)

            x1, y1 = min(self.draw_start_x, end_x), min(self.draw_start_y, end_y)
            x2, y2 = max(self.draw_start_x, end_x), max(self.draw_start_y, end_y)

            cropped_image = self.normal_screenshot.crop((x1, y1, x2, y2))
            cropped_image_tk = ImageTk.PhotoImage(cropped_image)

            if self.last_cropped_image_tk:
                self.canvas.delete('cropped_image_id')

            self.canvas.create_image(x1, y1, anchor=tk.NW, image=cropped_image_tk, tags='cropped_image_id')
            self.last_cropped_image_tk = cropped_image_tk

    def on_button_release(self, event):
        if not (self.drawing_mode or self.line_mode):
            end_x, end_y = event.x, event.y
            print(f"Start: ({self.draw_start_x}, {self.draw_start_y}), End: ({end_x}, {end_y})")
            self.show_action_menu(self.draw_start_x, self.draw_start_y, end_x, end_y, self.canvas.master)

    def copy_to_clipboard(self, image):
        output = io.BytesIO()
        image.convert("RGB").save(output, format="BMP")
        data = output.getvalue()[14:]

        clipboard.OpenClipboard()
        clipboard.EmptyClipboard()
        clipboard.SetClipboardData(clipboard.CF_DIB, data)
        clipboard.CloseClipboard()

    def crop_and_copy_to_clipboard(self, x1, y1, x2, y2):
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        
        screen_shot = ImageGrab.grab()
        cropped_image = screen_shot.crop((x1, y1, x2, y2))
        self.copy_to_clipboard(cropped_image)
        print("Zaznaczony fragment został skopiowany do schowka!")

    def take_text(self, x1, y1, x2, y2):
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        screen_shot = ImageGrab.grab()
        cropped_image = screen_shot.crop((x1, y1, x2, y2)).convert("RGB")

        pixels_value = procesor(images=cropped_image, return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        print(generated_text)
        


    def show_action_menu(self, x1, y1, x2, y2, fullscreen_window):
        if self.menu_frame:
            self.menu_frame.destroy()

        menu_x = x2
        menu_y = y1

        self.menu_frame = tk.Frame(fullscreen_window, bg="white", bd=2)
        self.menu_frame.place(x=menu_x, y=menu_y)

        copy_button = tk.Button(self.menu_frame, text="Kopiuj do schowka", command=lambda: self.crop_and_copy_to_clipboard(x1, y1, x2, y2))
        copy_button.pack(fill=tk.BOTH)

        draw_button = tk.Button(self.menu_frame, text="Rysuj", command=lambda: self.enable_drawing(x1, y1, x2, y2))
        draw_button.pack(fill=tk.BOTH)

        line_button = tk.Button(self.menu_frame, text="Rysuj linię", command=lambda: self.enable_line_drawing(x1, y1, x2, y2))
        line_button.pack(fill=tk.BOTH)

        cancel_button = tk.Button(self.menu_frame, text="Anuluj", command=self.menu_frame.destroy)
        cancel_button.pack(fill=tk.BOTH)

        text_analise_button = tk.Button(self.manu_frame, text="czytaj tekst", command=lambda: self.take_text(x1, y1, x2, y2))
        text_analise_button.pack(fill=tk.BOTH)

    def enable_drawing(self, x1, y1, x2, y2):
        self.drawing_mode = True
        self.draw_start_x = x1
        self.draw_start_y = y1
        self.draw_end_x = x2
        self.draw_end_y = y2

        self.canvas.bind("<ButtonPress-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw_line)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)

    def enable_line_drawing(self, x1, y1, x2, y2):
        self.line_mode = True
        self.line_start_x = x1
        self.line_start_y = y1

        self.canvas.bind("<ButtonPress-1>", self.start_line_drawing)
        self.canvas.bind("<B1-Motion>", self.draw_line_in_progress)
        self.canvas.bind("<ButtonRelease-1>", self.stop_line_drawing)

    def run(self):
        # Nasłuchuj kombinacji klawiszy
        keyboard.add_hotkey('alt+shift', self.on_activate)
        self.root.mainloop()

if __name__ == "__main__":
    app = ScreenshotApp()
    print('ready1')
    app.run()
    print('ready2')
