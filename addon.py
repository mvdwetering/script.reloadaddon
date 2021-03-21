# -*- coding: utf-8 -*-

from typing import Any, Dict, Tuple

import logging
import time
import json

import xbmcaddon
import xbmc
import xbmcgui

# Keep this file to a minimum, as Kodi
# doesn't keep a compiled copy of this
ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))

addon_id_to_reload = ADDON.getSettingString("addonid")
# addon_id_to_reload = "service.xbmc.versioncheck"


def notify(message:str, icon=ADDON.getAddonInfo('icon')):
    xbmcgui.Dialog().notification(ADDON.getAddonInfo('name'), message, icon, 5000)


def do_rpc(method:str, params:Dict) -> Tuple[bool, Any]:
    jsonrpc = {
        "jsonrpc": "2.0",
        "id":1,
        "method": method,
        "params": params
    }
    response = xbmc.executeJSONRPC(json.dumps(jsonrpc))
    return ("result" in response, json.loads(response))


def enable_addon(addon_id:str, enable:bool) -> bool:
    params = {
        "addonid": addon_id,
        "enabled": enable
    }
    result = do_rpc("Addons.SetAddonEnabled", params)
    return result[0]


def is_addon_to_reload_enabled() -> bool:
    result = do_rpc("Addons.GetAddonDetails", {"addonid": addon_id_to_reload, "properties": ["enabled"]})
    return result[1]["result"]["addon"]["enabled"]


def wait_for_enabled_status(desired_status:bool, timeout:int=10):
    status = not desired_status
    start = time.time()
    while status != desired_status:
        time.sleep(0.5)
        status = is_addon_to_reload_enabled()
        if (time.time() - start) > timeout:
            raise(TimeoutError)


# Validate settings
try:
    xbmcaddon.Addon(addon_id_to_reload)
except RuntimeError:
    # Occurs when addon_id_to_reload is invalid
    addon_id_to_reload = ""

if not addon_id_to_reload:
    if xbmcgui.Dialog().yesno(ADDON.getAddonInfo("name"), ADDON.getLocalizedString(32003)):
        ADDON.openSettings()
    exit(0)

# Reload
ok = True
try:
    ok &= enable_addon(addon_id_to_reload, False)
    wait_for_enabled_status(False)
    ok &= enable_addon(addon_id_to_reload, True)
    wait_for_enabled_status(True)
except Exception as e:
    logger.exception(e)
    ok = False

if ok:
    notify(f"{addon_id_to_reload}\nsuccess", xbmcgui.NOTIFICATION_INFO)
else:
    notify(f"{addon_id_to_reload}\nfailed", xbmcgui.NOTIFICATION_WARNING)

