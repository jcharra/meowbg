from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label

class OKDialog(GridLayout):
    def __init__(self, **kwargs):
        kwargs.update({"rows": 3})
        GridLayout.__init__(self, **kwargs)
        text = kwargs.get("text", "")
        self.add_widget(Label(text=text, size_hint=(1, 3)))
        self.ok_button = Button(text="OK", size_hint=(1, 1))
        self.add_widget(self.ok_button)

class ResignDialog(GridLayout):
    def __init__(self, **kwargs):
        kwargs.update({"rows": 3})
        GridLayout.__init__(self, **kwargs)
        self.add_widget(Label(text="Resign how?", size_hint=(1, 3)))
        self.ok_button = Button(text="OK", size_hint=(1, 1))
        self.add_widget(self.ok_button)
