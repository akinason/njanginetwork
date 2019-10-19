import os
project_root = "/home/kinason/projects/njanginetwork"
dirs = os.listdir(project_root)
for app in dirs:
    app_path = os.path.join(project_root, app)
    locale_path = os.path.join(app_path, "locale")
    if os.path.exists(locale_path):  # modify this condition for exclusion of specific folders
        os.chdir(app_path)
        os.system("django-admin.py makemessages -l fr")
