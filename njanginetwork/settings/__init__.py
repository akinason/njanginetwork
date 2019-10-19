import environment

if environment.env() == environment.DEVELOPMENT:
    from .development import *
else:
    from .production import *


