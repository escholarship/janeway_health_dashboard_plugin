from utils import models
from utils.logger import get_logger

from utils.install import update_settings


logger = get_logger(__name__)

PLUGIN_NAME = "Health Dashboard Plugin"
DISPLAY_NAME = "Health Dashboard"
DESCRIPTION = "Display health metrics for journals"
AUTHOR = "California Digital Library"
VERSION = "1.0"
SHORT_NAME = "health_dashboard"
MANAGER_URL = "dashboard"

def install():
    plugin, created = models.Plugin.objects.get_or_create(
        name=SHORT_NAME,
        defaults={
            "enabled": True,
            "version": VERSION,
            "display_name": DISPLAY_NAME,
        }
    )

    if created:
        print(f'Plugin {PLUGIN_NAME} installed.')
    elif plugin.version != VERSION:
        print(f'Plugin updated: {VERSION} -> {plugin.version}')
        plugin.version = VERSION
        plugin.display_name = DISPLAY_NAME
        plugin.save()
    else:
        print(f'Plugin {PLUGIN_NAME} is already installed.')

    update_settings(
        file_path='plugins/health_dashboard/install/settings.json',
    )


# def register_for_events():
#     pass

def hook_registry():
    pass