"""Provide :class:`CookBook`."""

import attr


@attr.s(auto_attribs=True)
class CookBook:
    """Save recipes for construction of Classes with default values."""

    recipes: dict = None

    def __attrs_post_init__(self):
        if self.recipes is None:
            self.recipes = {}

    def register(self, recipe_name, info=None, **kwargs):
        """Add recipe to :attr:`recipes`."""

        def wrapper(func):
            self.recipes[recipe_name] = {
                "obj": func,
                "info": info,
                "default_kwargs": kwargs,
            }
            return func

        return wrapper

    def cook(self, name, **kwargs):
        """Generate object from recipe.

        default_kwargs in recipe can be overridden by kwargs.
        """
        if name not in self.recipes:
            raise KeyError(f"Name '{name}' must be one of: {self.recipes.keys()}")
        recipe = self.recipes[name]
        for key, val in recipe["default_kwargs"].items():
            kwargs.setdefault(key, val)
        return recipe["obj"](**kwargs)

    def __contains__(self, item):
        return item in self.recipes

    def get_recipes(self):
        """Return :attr:`recipes`."""
        return self.recipes

    def get_recipe_names(self):
        """Return list of all registered recipes."""
        return list(self.recipes.keys())

    def to_button_dict(self):
        """Return dict in a form as used in :attr:`custom_widgets.CustomSpeedDial.button_dicts`."""
        return {
            val["info"]["icon"]: {
                "text": val["info"]["text"],
                "callback": self.cook(key),
            }
            for key, val in self.recipes.items()
        }
