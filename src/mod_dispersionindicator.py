
import math
import json
import BigWorld
import ResMgr
from debug_utils import LOG_CURRENT_EXCEPTION
from PlayerEvents import g_playerEvents
from Avatar import PlayerAvatar

from dispersionindicator.constants import MOD_NAME, CONFIG_FILES
from dispersionindicator.indicator import Indicator


def init():
    try:
        BigWorld.logInfo(MOD_NAME, '{} initialize'.format(MOD_NAME), None)
        config = { 'default': {}, 'stats_defs': {}, 'panels': {} }
        for file in CONFIG_FILES:
            if not ResMgr.isFile(file):
                continue
            BigWorld.logInfo(MOD_NAME, 'load config file: {}'.format(file), None)
            section = ResMgr.openSection(file)
            data = json.loads(section.asString)
            config['default'].update(data.get('default', {}))
            config['stats_defs'].update(data.get('stats_defs', {}))
            config['panels'] = data.get('panels', {})
            config['logs'] = data.get('logs', {})
        print json.dumps(config, indent=2)
        indicator = Indicator(config)
        for name, paneldef in config['panels'].items():
            localConfig = { 'style': {} }
            localConfig['style'].update(config['default'])
            localConfig['style'].update(paneldef.get('style', {}))
            localConfig['stats_defs'] = {}
            localConfig['stats_defs'].update(config['stats_defs'])
            localConfig['stats_defs'].update(paneldef.get('stats_defs', {}))
            localConfig['items'] = paneldef['items']
            indicator.addPanel(name, localConfig)
        if len(config.get('logs', {})):
            localConfig = {}
            localConfig['items'] = config['logs'].values()[0]['items']
            localConfig['stats_defs'] = config['stats_defs']
            indicator.addLogger(localConfig)
        g_playerEvents.onAvatarBecomePlayer += indicator.start
        g_playerEvents.onAvatarBecomeNonPlayer += indicator.stop
    except:
        LOG_CURRENT_EXCEPTION()

