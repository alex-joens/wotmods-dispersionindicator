


CONSTANT = {
    'MS_TO_KMH':    3600.0 / 1000.0
}


def init():
    global g_status
    global g_panel
    g_status = Status()
    g_panel = IndicatorPanel()

def shotResultIndicatorPlugin_start(orig, self, *args, **kwargs):
    result = orig(self, *args, **kwargs)
    g_panel.start()
    return result

def shotResultIndicatorPlugin_stop(orig, self, *args, **kwargs):
    g_panel.stop()
    result = orig(self, *args, **kwargs)
    return result

def shotResultIndicatorPlugin_onGunMarkerStateChanged(orig, self, *args, **kwargs):
    result = orig(self, *args, **kwargs)
    g_panel.onUpdate()
    return result


class IndicatorPanel(Panel):
    def __init__(self):
        configlist = self.__genSettings()
        super(IndicatorPanel, self).__init__(configlist)

    def __genSettings(self):
        class Config: pass
        configList = []
        for setting in g_config['panelItems']:
            name = settings['status']
            factor = settings['factor']
            template = settings['format']
            if isinstance(factor, str):
                factor = CONSTANT.get(factor, 1.0)
            config = Config()
            config.title = settings['title']
            config.func = lambda: template.format(getattr(g_status, name) * factor)
            config.unit = settings['unit']
            configList.append(config)


def playerAvatar_getOwnVehicleShotDispersionAngle(orig, self, turretRotationSpeed, withShot = 0):
    result = orig(self, turretRotationSpeed, withShot)
    avatar = self
    g_status.dAngleAiming = result[0]
    g_status.dAngleIdeal = result[1]
    g_status.turretRotationSpeed = turretRotationSpeed
    g_status.withShot = withShot
    g_status._getOwnVehicleShotDispersionAngle(avatar)
    return result


class Status(object):
    def _getOwnVehicleShotDispersionAngle(self, avatar):
        self.currTime = BigWorld.time()
        vDescr = avatar._PlayerAvatar__getDetailedVehicleDescriptor()
        self.additiveFactor = self._PlayerAvatar__getAdditiveShotDispersionFactor(vDescr)
        self.shotDispersionAngle = vDescr.gun.shotDispersionAngle
        if self.withShot == 0:
            self.shotFactor = 0.0
        elif self.withShot == 1:
            self.shotFactor = vDescr.gun.shotDispersionFactors['afterShot']
        else:
            self.shotFactor = vDescr.gun.shotDispersionFactors['afterShotInBurst']
        self._update_aimingInfo(avatar)
        self._update_vehicleSpeeds(avatar)
        self._update_vehicleEngineState(avatar)

    def _update_aimingInfo(self, avatar):
        aimingInfo = avatar._PlayerAvatar__aimingInfo
        self.aimingStartTime = aimingInfo[0]
        self.aimingStartFactor = aimingInfo[1]
        self.multFactor = aiminginfo[2]
        self.factorsTurretRotation = aimingInfo[3]
        self.factorsMovement = aiminginfo[4]
        self.factorsRotation = aiminginfo[5]
        self.aimingTime = aimingInfo[6]

    def _update_vehicleSpeeds(self, avatar):
        vehicleSpeed, vehicleRspeed = avatar.getOwnVehicleSpeeds(True)
        self.vehicleSpeed = vehicleSpeed
        self.vehicleRSpeed = vehicleRSpeed

    def _update_vehicleEngineState(self, avatar):
        detailedEngineState = avatar.vehicle.appearance._CompoundAppearance__detailedEngineState
        self.engineRPM = detailedEngineState.rpm
        self.engineRelativeRPM = detailedEngineState.relativeRPM

    @property
    def aimingFactor(self):
        return self.dAngleAiming / self.shotDispersionAngle

    @property
    def aimingTimeConverging(self):
        return self.aimingStartTime + self.aimingTime * math.log(self.aimingStartFactor) - self.currTime

    @property
    def scoreDispersion(self):
        return (mah.log(self.aimingFactor) / math.log(4.0)) ** 2 * 100.0
