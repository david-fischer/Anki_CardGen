import lorem
from kivy.animation import Animation
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivymd.uix.behaviors import RectangularRippleBehavior
from kivymd.uix.card import MDCard

Builder.load_file("my_kivy/mycard.kv")


class MyCard(RectangularRippleBehavior, ButtonBehavior, MDCard):
    checked = BooleanProperty(False)
    text_color = ListProperty()
    bg_color = ListProperty()
    text = StringProperty(lorem.paragraph())

    def on_press(self):
        self.checked = not self.checked

    # def on_touch_down(self, touch):
    #     if self.collide_point(*touch.pos):
    #         self.checked = not self.checked

    def on_checked(self, *args):
        anim = Animation(bg_color=self.theme_cls.primary_color if self.checked else self.theme_cls.bg_light,
                         text_color=[1, 1, 1, 1] if self.checked else self.theme_cls.text_color,
                         duration=0.5,
                         t="out_circ")
        anim.start(self)


class MyCardChooser(BoxLayout):
    choose_one = BooleanProperty(False)
    string_list = ListProperty([])

    def get_checked(self):
        return [card.ids.label.text for card in self.children if card.checked]

    def on_string_list(self, *args):
        self.clear_widgets()
        for string in self.string_list:
            self.add_widget(MyCard(text=string))


if __name__ == "__main__":
    class TestApp(MDApp):
        def build(self):
            self.theme_cls.primary_palette = "Red"  # "Purple", "Red"
            self.theme_cls.theme_style = "Dark"  # "Purple", "Red"
            return Builder.load_string("""
#:import lorem lorem
ScrollView:
    do_scroll_x: False
    do_scroll_y: True
    size_hint: 1,1
    MyCardChooser:
        id: my_card_chooser
        string_list: ["test_"+str(i) for i in range(10)]
""")


    TestApp().run()
