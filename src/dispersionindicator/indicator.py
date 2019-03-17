
import BigWorld
import GUI
from gui import g_guiResetters
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider
from gui.shared.utils.TimeInterval import TimeInterval
from gui.battle_control.battle_constants import VEHICLE_VIEW_STATE

from widget import PanelWidget, LabelWidget
from output import OutputFile

MOD_NAME = '${name}'

_UPDATE_INTERVAL = 0.1
CONSTANT = {
    'MS_TO_KMH':    3600.0 / 1000.0
}


class IndicatorPanel(object):
    def __init__(self):
        self.__panels = {}
        self._timeInterval = TimeInterval(_UPDATE_INTERVAL, self, '_update')

    def addPanel(self, name, config, stats):
        panel = _IndicatorSubPanel(config, stats)
        self.__panels[name] = panel

    def addLogger(self, config, stats):
        logger = OutputFile(config, stats)
        self.__panels['__logger__'] = logger

    def start(self):
        BigWorld.logInfo(MOD_NAME, 'panel.start', None)
        for panel in self.__panels.values():
            panel.start()
        g_guiResetters.add(self.onScreenResolutionChanged)
        self.session = dependency.instance(IBattleSessionProvider)
        # VehicleStateController in gui.battle_control.controllers.vehicle_state_ctrl
        ctl = self.session.shared.vehicleState
        ctl.onVehicleStateUpdated += self.onVehicleStateUpdated
        ctl.onVehicleControlling += self.onVehicleControlling

    def stop(self):
        BigWorld.logInfo(MOD_NAME, 'panel.stop', None)
        self._timeInterval.stop()
        g_guiResetters.discard(self.onScreenResolutionChanged)
        ctl = self.session.shared.crosshair
        if ctl:
            ctl.onVehicleStateUpdated -= self.onVehicleStateUpdated
            ctl.onVehicleControlling -= self.onVehicleControlling
        for panel in self.__panels.values():
            panel.stop()

    def _update(self):
        #BigWorld.logInfo(MOD_NAME, '_update', None)
        for panel in self.__panels.values():
            panel.update()

    def onVehicleStateUpdated(self, stateID, stateValue):
        BigWorld.logInfo(MOD_NAME, 'onVehicleStateUpdated: {}, {}'.format(stateID, stateValue), None)
        if stateID == VEHICLE_VIEW_STATE.CRUISE_MODE:
            if not self._timeInterval.isStarted():
                BigWorld.logInfo(MOD_NAME, 'TimeInterval: start', None)
                self._timeInterval.start()

    def onVehicleControlling(self, vehicle):
        BigWorld.logInfo(MOD_NAME, 'onVehicleControlling: {}'.format(vehicle), None)
        if not self._timeInterval.isStarted():
            BigWorld.logInfo(MOD_NAME, 'TimeInterval: start', None)
            self._timeInterval.start()

    def onScreenResolutionChanged(self):
        for panel in self.__panels.values():
            if getattr(panel, 'updatePosition', None) and callable(panel.updatePosition):
                panel.updatePosition()


class _IndicatorSubPanel(object):
    def __init__(self, config, stats):
        self.stats = stats
        style = config['style']
        self.label_font = style['font']
        self.label_colour = tuple(style['colour'] + [ style['alpha'] ])
        self.line_height = style['line_height']
        self.padding_top = style['padding_top']
        self.padding_bottom = style['padding_bottom']
        self.padding_left = style['padding_left']
        self.padding_right = style['padding_right']
        self.panel_offset = style['panel_offset']
        self.panel_horizontalAnchor = str(style['horizontalAnchor'])
        self.panel_verticalAnchor = str(style['verticalAnchor'])
        self.stats_width = style['stats_width']
        self.bgimage = style['bgimage']
        self.statsdefs = config['stats_defs']
        self.panel = self.createWidgetTree(config['items'])
        self.panel.visible = False

    def start(self):
        self.panel.addRoot()
        self.updatePosition()
        self.panel.visible = True
        
    def stop(self):
        self.panel.visible = False
        self.panel.delRoot()

    def update(self, *args):
        try:
            self.panel.update()
        except:
            BigWorld.logError(MOD_NAME, 'fail to update panel state', None)
    
    def enable(self):
        self.panel.visible = True
    
    def toggleVisible(self):
        self.panel.visible = not self.panel.visible

    def updatePosition(self):
        screen = GUI.screenResolution()
        center = ( screen[0] / 2, screen[1] / 2)
        x = center[0] + self.panel_offset[0]
        y = center[1] + self.panel_offset[1]
        self.panel.position = (x, y, 1)

    def createWidgetTree(self, items):
        panel = PanelWidget(self.bgimage)
        y = self.padding_top
        for name in items:
            setting = self.statsdefs[name]
            child = self.createPanelLine(setting)
            panel.addChild(child)
            child.position = (0, y, 1)
            y = y + child.height
        anchorx = max([ c.anchor[0] for c in panel.children ])
        for child in panel.children:
            pos = list(child.position)
            offsetx = anchorx - child.anchor[0]
            newpos = (pos[0] + offsetx + self.padding_left, pos[1], pos[2])
            child.position = newpos
        bx0 = min([ c.boundingBox[0] for c in panel.children])
        bx1 = max([ c.boundingBox[2] for c in panel.children])
        panel.width = bx1 - bx0 + self.padding_left + self.padding_right
        panel.height = y + self.padding_bottom
        panel.horizontalAnchor = self.panel_horizontalAnchor
        panel.verticalAnchor = self.panel_verticalAnchor
        return panel

    def createPanelLine(self, setting):
        name = setting['status']
        factor = setting['factor']
        template = setting['format']
        if isinstance(factor, str) or isinstance(factor, unicode):
            factor = CONSTANT.get(factor, 1.0)
        argList = {
            'title': {
                'text':     setting['title'],
                'align':    'RIGHT',
                'x':        - self.stats_width - 4
            },
            'stat': {
                'text':     template.format(0.0),
                'func':     lambda n=name, f=factor, t=template, s=self.stats: t.format(getattr(s, n, 0.0) * f),
                'align':    'RIGHT',
                'width':    self.stats_width,
                'x':        0
            },
            'unit': {
                'text':     setting['unit'],
                'x':        4
            }
        }
        panel = PanelWidget('')
        for name, kwargs in argList.items():
            label = self.createLabel(**kwargs)
            panel.addChild(label, name)
        bx0 = min([ c.boundingBox[0] for c in panel.children])
        bx1 = max([ c.boundingBox[2] for c in panel.children])
        for child in panel.children:
            pos = list(child.position)
            newpos = (pos[0] - bx0, pos[1], pos[2])
            child.position = newpos
        panel.anchor = [ - bx0, 0 ]
        panel.width = bx1 - bx0
        panel.height = self.line_height
        panel.visible = True
        panel.position = (0, 0, 1)
        return panel

    def createLabel(self, text='', func=None, align='LEFT', width=None, x=0):
        label = LabelWidget()
        label.text = text
        if func is not None:
            label.setCallback(func)
        label.font = self.label_font
        label.colour = self.label_colour
        label.horizontalAnchor = align
        label.position = (x, 0, 1)
        label.visible = True
        label.width = width
        return label
