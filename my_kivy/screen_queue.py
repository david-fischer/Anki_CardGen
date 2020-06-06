from kivymd.app import MDApp

options_dict = {
    "script-text-outline": "Import from Kindle",
    "note-text": "Import from Text File"
}

def import_from(button):
    button.parent.close_stack()
    text = options_dict[button.icon]
    if text == "Import from Kindle":
        print("Importing from kindle-html-file...")
    elif text == "Import from Text File":
        print("Importing from text-file...")

def click_on_queue_item(item):
    print(item.text)
    MDApp.get_running_app().queue_words.remove(item.text)
    MDApp.get_running_app().done_words.append(item.text)

def click_on_done_item(item):
    print(item.text)

def click_on_error_item(item):
    print(item.text)

