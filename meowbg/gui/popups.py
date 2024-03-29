from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.slider import Slider


class OKDialog(GridLayout):
    def __init__(self, text, **kwargs):
        kwargs.update({"rows": 3})
        GridLayout.__init__(self, **kwargs)
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


class ResignOptions(GridLayout):
    NORMAL, GAMMON, BACKGAMMON = 1, 2, 3

    def __init__(self, **kwargs):
        kwargs.update({'cols': 2})
        GridLayout.__init__(self, **kwargs)
        cb_normal = CheckBox(group='resign', active=True, size_hint=(0.1, 1))
        cb_normal.bind(active=lambda cb, v: self.set_choice(self.NORMAL))
        self.add_widget(cb_normal)
        self.add_widget(Label(text='normal', size_hint=(0.9, 1)))

        cb_gammon = CheckBox(group='resign', size_hint=(0.1, 1))
        cb_gammon.bind(active=lambda cb, v: self.set_choice(self.GAMMON))
        self.add_widget(cb_gammon)
        self.add_widget(Label(text='gammon', size_hint=(0.9, 1)))

        cb_backgammon = CheckBox(group='resign', size_hint=(0.1, 1))
        cb_backgammon.bind(
            active=lambda cb, v: self.set_choice(self.BACKGAMMON))
        self.add_widget(cb_backgammon)
        self.add_widget(Label(text='backgammon', size_hint=(0.9, 1)))

        self.choice = self.NORMAL

    def set_choice(self, val):
        self.choice = val


class ResignDialog(GridLayout):
    def __init__(self, **kwargs):
        kwargs.update({"rows": 3})
        GridLayout.__init__(self, **kwargs)
        self.add_widget(Label(text="Resign how?", size_hint=(1, 3)))
        self.options = ResignOptions(size_hint=(1, 2))
        self.add_widget(self.options)

        self.ok_button = Button(text="OK", size_hint=(1, 1))
        self.add_widget(self.ok_button)

        self.cancel_button = Button(text="Cancel", size_hint=(1, 1))
        self.add_widget(self.cancel_button)


class ChooseMatchLengthDialog(GridLayout):
    DEFAULT_CHOICE = 3

    def __init__(self, **kwargs):
        kwargs.update({"cols": 1})
        GridLayout.__init__(self, **kwargs)
        self.choice = self.DEFAULT_CHOICE
        self.add_widget(
            Label(text="Please pick a match length", size_hint=(1, 1)))

        self.choice_label = Label(text=str(self.choice),
                                  font_size=20,
                                  size_hint=(1, 2))
        self.add_widget(self.choice_label)

        slider = Slider(min=1, max=22, value=self.choice, size_hint=(1, 2))
        slider.bind(value=self.update_val)
        self.add_widget(slider)

        self.ok_button = Button(text="OK", size_hint=(1, 1))
        self.add_widget(self.ok_button)

        self.cancel_button = Button(text="Cancel", size_hint=(1, 1))
        self.add_widget(self.cancel_button)

    def update_val(self, slider, val):
        self.choice = int(val)
        text = str(self.choice)
        if val == 22:
            text = u"\u221E"
        self.choice_label.text = text


class ConnectionDialog(GridLayout):
    def set_server(self, val):
        self.server = val

    def __init__(self, **kwargs):
        kwargs.update({"cols": 2})
        GridLayout.__init__(self, **kwargs)

        self.server = "Tigergammon"

        cb_tiga = CheckBox(group='server', active=True, size_hint=(0.1, 1))
        cb_tiga.bind(active=lambda cb, v: self.set_server("Tigergammon"))
        self.add_widget(cb_tiga)
        self.add_widget(Label(text='TigerGammon', size_hint=(0.9, 1)))

        cb_fibs = CheckBox(group='server', active=False, size_hint=(0.1, 1))
        cb_fibs.bind(active=lambda cb, v: self.set_server("fibs"))
        self.add_widget(cb_fibs)
        self.add_widget(Label(text='FIBS', size_hint=(0.9, 1)))

        self.add_widget(Label(text="User", size_hint=(0.1, 1)))

        self.username = TextInput(size_hint=(0.1, 1))
        self.add_widget(self.username)

        self.add_widget(Label(text="Password", size_hint=(0.1, 1)))
        self.password = TextInput(password=True, size_hint=(0.1, 1))
        self.add_widget(self.password)

        self.ok_button = Button(text="OK", size_hint=(1, 1))
        self.add_widget(self.ok_button)

        self.cancel_button = Button(text="Cancel", size_hint=(1, 1))
        self.add_widget(self.cancel_button)
