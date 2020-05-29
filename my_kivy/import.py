def file_manager_open(self):
    if not self.manager:
        self.manager = ModalView(size_hint=(1, 1), auto_dismiss=False)
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager, select_path=self.select_path)
        self.manager.add_widget(self.file_manager)
        self.file_manager.show('/')  # output manager to the screen
    self.manager_open = True
    self.manager.open()


def select_path(self, path):
    '''It will be called when you click on the file name
    or the catalog selection button.

    :type path: str;
    :param path: path to the selected directory or file;
    '''

    self.exit_manager()
    toast(path)


def exit_manager(self, *args):
    '''Called when the user reaches the root of the directory tree.'''

    self.manager.dismiss()
    self.manager_open = False


def events(self, instance, keyboard, keycode, text, modifiers):
    '''Called when buttons are pressed on the mobile device..'''

    if keyboard in (1001, 27):
        if self.manager_open:
            self.file_manager.back()
    return True