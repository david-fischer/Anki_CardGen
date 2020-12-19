"""File to place unused functions for future use."""


def route_call_to_member(cls, member, method):
    """Map cls.method to cls.member.method instead."""
    setattr(
        cls,
        method,
        lambda x, *args, **kwargs: getattr(
            getattr(x, member),
            method,
        )(*args, **kwargs),
    )


def route_calls_to_member(member, calls):
    """
    Apply :func:`route_call_to_member` to class using a decorator.

    Usage:
        @route_calls_to_member("some_list", "len", "__getitem__", "__contains__", "__iter__" )
        class SomeClass:
            some_list = []
    """

    def decorator_func(cls):
        for call in calls:
            route_call_to_member(cls, member, call)
        return cls

    return decorator_func


#
# @attr.s(auto_attribs=True)
# class OpenDialogMixin:
#     content_cls_name: str = "CustomContentBase"
#     dialog_cls_name: str = "CustomDialog"
#     dialog_title: str = "Default Title"
#     _dialog: MDDialog = None
#
#     def _init_dialog(self):
#         content_cls = Factory.get(self.content_cls_name)
#         dialog_cls = Factory.get(self.dialog_cls_name)
#         print(self.dialog_cls_name, self.content_cls_name)
#         print(dialog_cls, content_cls)
#         self._dialog = dialog_cls(
#             title=self.dialog_title,
#             content_cls=content_cls(),
#             callback=self.dialog_callback,
#         )
#
#     def dialog_callback(self, button, result):
#         """Callback for dialog."""
#
#     def show_dialog(self, raw_dialog_data):
#         if self._dialog is None:
#             self._init_dialog()
#         self._dialog.content_cls.data = self.process_dialog_data(raw_dialog_data)
#         self._dialog.open()
#
#     def process_dialog_data(self, raw_dialog_data):
#         return raw_dialog_data
