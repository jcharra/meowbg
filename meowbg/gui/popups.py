from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox

class OKDialog(GridLayout):
    def __init__(self, **kwargs):
        kwargs.update({"rows": 3})
        GridLayout.__init__(self, **kwargs)
        text = kwargs.get("text", "")
        self.add_widget(Label(text=text, size_hint=(1, 3)))
        self.ok_button = Button(text="OK", size_hint=(1, 1))
        self.add_widget(self.ok_button)

class BetweenGamesDialog(GridLayout):
    def __init__(self, **kwargs):
        kwargs.update({"cols": 1})
        GridLayout.__init__(self, **kwargs)
        self.add_widget(Label(text="Continue match?", size_hint=(1, 4)))
        self.ok_button = Button(text="Join next game", size_hint=(1, 1))
        self.add_widget(self.ok_button)
        self.cancel_button = Button(text="Leave", size_hint=(1, 1))
        self.add_widget(self.cancel_button)

class ResignOptions(BoxLayout):
    def __init__(self, **kwargs):
        kwargs.update({'orientation': 'horizontal'})
        BoxLayout.__init__(self, **kwargs)
        self.add_widget(CheckBox(text='normal', group='resign', active=True))
        self.add_widget(CheckBox(text='gammon', group='resign'))
        self.add_widget(CheckBox(text='backgammon', group='resign'))


class ResignDialog(GridLayout):
    def __init__(self, **kwargs):
        kwargs.update({"rows": 3})
        GridLayout.__init__(self, **kwargs)
        self.add_widget(Label(text="Resign how?", size_hint=(1, 3)))
        self.add_widget(ResignOptions(size_hint=(1, 2)))
        self.ok_button = Button(text="OK", size_hint=(1, 1))
        self.add_widget(self.ok_button)
