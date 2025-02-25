import qrcode
import numpy as np
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.uix.camera import Camera as KivyCamera
from PIL import Image as PILImage
import cv2


class MainScreen(Screen):
    """Main Screen with navigation buttons."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        layout.add_widget(Label(text="QR Code App", font_size=30, size_hint=(1, 0.2)))

        button_layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.5, None), height=240)

        btn_generate = Button(text="Generate QR Code", size_hint=(2, 1), height=50)
        btn_generate.bind(on_press=self.go_to_generate)
        button_layout.add_widget(btn_generate)

        btn_scan = Button(text="Scan QR Code", size_hint=(2, 1), height=50)
        btn_scan.bind(on_press=self.go_to_scan)
        button_layout.add_widget(btn_scan)

        layout.add_widget(button_layout)
        self.add_widget(layout)

    def go_to_generate(self, instance):
        self.manager.current = 'generate_qr'

    def go_to_scan(self, instance):
        self.manager.current = 'scan_qr'


class GenerateQRScreen(Screen):
    """Screen for generating QR Codes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=20)

        self.name_input = TextInput(hint_text="Enter Name", size_hint=(1.0, 0.1), height=50, multiline=False)
        layout.add_widget(self.name_input)

        self.qr_image = Image(size_hint=(1.0, 1.0), size=(200, 200))
        layout.add_widget(self.qr_image)

        btn_generate = Button(text="Generate QR Code", size_hint=(1, 0.1), height=50)
        btn_generate.bind(on_press=self.generate_qr)
        layout.add_widget(btn_generate)

        btn_back = Button(text="Back to Home", size_hint=(1, 0.1), height=50)
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def generate_qr(self, instance):
        name = self.name_input.text.strip()
        if not name:
            self.name_input.hint_text = "Please enter a name!"
            return

        qr = qrcode.make(name)
        qr.save("qr_code.png")

        pil_image = PILImage.open("qr_code.png").convert("RGBA")
        texture = Texture.create(size=pil_image.size, colorfmt='rgba')
        texture.blit_buffer(pil_image.tobytes(), colorfmt='rgba', bufferfmt='ubyte')

        self.qr_image.texture = texture

    def go_back(self, instance):
        self.manager.current = 'main'


class ScanQRScreen(Screen):
    """Screen for scanning QR Codes using Kivy Camera."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        self.result_label = Label(text="Scan Result: ", font_size=20, size_hint=(1, 0.2))
        layout.add_widget(self.result_label)

        # Use Kivy Camera for Android
        self.camera = KivyCamera(play=False, resolution=(640, 480), size_hint=(1,0.6))
        layout.add_widget(self.camera)

        btn_scan = Button(text="Start Scanning", size_hint=(1, 0.1), height=50)
        btn_scan.bind(on_press=self.start_scanning)
        layout.add_widget(btn_scan)

        btn_back = Button(text="Back to Home", size_hint=(1, 0.1), height=50)
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)

        self.add_widget(layout)

    def start_scanning(self, instance):
        """Start scanning QR codes."""
        self.camera.play = True
        Clock.schedule_interval(self.detect_qr_android, 1.0 / 30.0)  # 30 FPS

    def detect_qr_android(self, dt):
        """Detect QR codes from the camera frame and correct orientation."""
        if self.camera.texture:
            # Convert texture to OpenCV format
            texture = self.camera.texture
            size = texture.size
            pixels = texture.pixels

        # Convert texture to OpenCV image
        opencv_image = np.frombuffer(pixels, dtype=np.uint8).reshape(size[1], size[0], 4)

        # Convert from RGBA to BGR (since OpenCV uses BGR format)
        opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_RGBA2BGR)

        # Rotate the image correctly
        opencv_image = cv2.rotate(opencv_image, cv2.ROTATE_90_CLOCKWISE)  # Adjust as needed

        # QR code detection
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(opencv_image)

        if data:
            self.result_label.text = f"Scan Result: {data}"
            self.camera.play = False
            Clock.unschedule(self.detect_qr_android)


    def go_back(self, instance):
        """Stop the camera and go back to the main screen."""
        self.camera.play = False
        Clock.unschedule(self.detect_qr_android)
        self.manager.current = 'main'


class QRApp(App):
    """Main Application."""

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(GenerateQRScreen(name='generate_qr'))
        sm.add_widget(ScanQRScreen(name='scan_qr'))
        return sm


if __name__ == "__main__":
    QRApp().run()