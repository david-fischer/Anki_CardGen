from time import time
from urllib.error import HTTPError

import wget
from kivy.effects.opacityscroll import OpacityScrollEffect
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty, ListProperty, Property
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.imagelist import Tile, SmartTile
from kivymd.utils.fitimage import FitImage


class CallControl:

    def __init__(self, max_call_interval):
        self._max_call_interval = max_call_interval
        self._last_call = time()

    def __call__(self, function):
        def wrapped(*args, **kwargs):
            now = time()
            if now - self._last_call > self._max_call_interval:
                self._last_call = now
                function(*args, **kwargs)

        return wrapped


class CheckTile(Tile):
    source = StringProperty()
    alternative_source = StringProperty("assets/camera.png")
    color = ListProperty([0, 0, 0, 0])
    checked = BooleanProperty(False)
    checked_op = Property(1)
    unchecked_op = Property(0.5)
    opacity = Property(0.5)

    def reload_image(self):
        self.ids.float_layout.remove_widget(self.ids.fit_image)
        self.ids.float_layout.add_widget(FitImage(id="fit_image",
                                                  pos_hint={"center_x": 0.5, "center_y": 0.5},
                                                  source=self.source))


class ThumbnailTile(CheckTile):
    url = StringProperty("")
    has_been_checked = BooleanProperty(False)
    is_loading = BooleanProperty(False)

    def on_press(self):
        super(ThumbnailTile, self).on_press()
        self.has_been_checked = True

    def on_has_been_checked(self, *args):
        self.ids.spinner.active = True
        new_source = self.source.replace("thumb", "img")
        try:
            wget.download(self.url, new_source)
            self.source = new_source
        except HTTPError:
            print(f"Could not find image under {self.url}")
        self.ids.spinner.active = False


class LoadMoreOnOverscroll(OpacityScrollEffect):

    def on_overscroll(self, *args):
        super(LoadMoreOnOverscroll, self).on_overscroll(*args)
        if self.overscroll > 100:
            self.refresh()

    @CallControl(max_call_interval=3)
    def refresh(self):
        # print("refresh")
        app = MDApp.get_running_app()
        app.root.ids.spinner.active = True


class ImgPick(ScrollView):
    effect_cls = LoadMoreOnOverscroll
    source_folder = StringProperty("assets")

    # source_list = ListProperty([])

    # def get_img_list(self):
    #     return [
    #         f
    #         for f in glob.glob(f"{self.source_folder}/*")
    #         if re.match(r'.*(jpg|png)', f)
    #     ]

    def remove_unchecked(self):
        unchecked_children = [child for child in self.ids.grid_layout.children if not child.checked]
        for child in unchecked_children:
            self.ids.grid_layout.remove_widget(child)

    def refresh_view(self):
        word = MDApp.get_running_app().word
        self.remove_unchecked()
        for i, url in enumerate(word.image_urls):
            self.ids.grid_layout.add_widget(SmartTile(
                source=url
                # url=url,
                # source=f"{self.source_folder}/thumb_{i}.jpg"
            ))

    # def on_source_folder(self, *args):
    #     self.source_list = self.get_img_list()
    #     self.remove_unchecked()
    #     for image_source in self.source_list:
    #         self.ids.grid_layout.add_widget(CheckTile(source=image_source))

    def get_checked(self):
        checked_children = [child for child in self.ids.grid_layout.children if child.checked]
        return [checked_tile.source for checked_tile in checked_children]


class ImagePickerMain:
    pass


Builder.load_file("my_kivy/picture_picker.kv")

if __name__ == "__main__":
    class MainApp(MDApp):
        def build(self):
            return Builder.load_string("""
FloatLayout:
    MDSpinner:
        id: spinner
        active:False
        size_hint: 0.5,0.5
        pos_hint:  {"center_x": .5, "center_y": .5}
        
    ImgPick:
        id: image_picker
        source_folder: app.word.folder
    
    MDFloatingActionButton:
        icon: "reload"
        pos_hint: {"center_x": .9, "center_y": .9}
        on_release: image_picker.on_source_folder()

    MDFloatingActionButton:
        icon: "minus"
        pos_hint: {"center_x": .9, "center_y": .1}
        on_release: image_picker.remove_unchecked()
    
    MDFloatingActionButton:
        icon: "check"
        pos_hint: {"center_x": .2, "center_y": .1}
        on_release: print(f"You chose {image_picker.get_checked()}.")
    
    MDTextFieldRound:
        icon_left: "magnify"
        hint_text: "Search Term"
        size_hint: 0.5,None
        height: 30
        pos_hint:  {"center_x": .5, "center_y": .9}

    
""")


    MainApp().run()
