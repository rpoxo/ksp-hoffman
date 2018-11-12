import math
import datetime
import logging

# TODO: prettify script
# typehinting
# logging
# kwargs
# format -> %f
# Vec3 for vectors

# TARGET BODY PARAMS
G_TARGET_BODY_ORBIT = 12000000 # m
G_TARGET_BODY_SOI = 2429559 # 2 429 559.1 m
G_TARGET_ORBIT = G_TARGET_BODY_ORBIT - G_TARGET_BODY_SOI # we aiming at SOI enter

# INITIAL BODY PARAMS
G_INITIAL_BODY_RADIUS = 600 * (10 ** 3)

# holding global shit
class Game:
    def __init__(self):
        self.resources = {}

class Resource(object):
    def __init__(self, density):
        self._density = density
    
    @property
    def density(self):
        return self._density

# just use same format as in ksp savefiles
# https://wiki.kerbalspaceprogram.com/wiki/Orbit#Orbits_in_the_save_file
class Orbit:
    def __init__(self, eccentricty, semi_major_axis, inclination, longtitude_AN, longtitude_PE):
        # orbit definition
        self.eccentricty = eccentricty
        self.semi_major_axis = semi_major_axis
        self.inclination = inclination
        self.longtitude_AN = longtitude_AN
        self.longtitude_PE = longtitude_PE
        self.body = None # focal if any

    @property
    def AP(self):
        return self.semi_major_axis * (1 + self.eccentricty) - self.body.radius

    @property
    def PE(self):
        return self.semi_major_axis * (1 - self.eccentricty) - self.body.radius
    
    @property
    def period(self):
        return 2 * math.pi * math.sqrt((self.semi_major_axis ** 3) / (self.body.mu))
    
    @property
    def mean_motion(self):
        return (2 * math.pi) / self.period

    # t time from pe?
    def mean_anomaly(self, t):
        return NotImplementedError

    def eccentric_anomaly(self, t):
        return NotImplementedError
    
    # returning altitude of craft at known time
    def altitude(self, t):
        return NotImplementedError

class Orbitable(object):
    def __init__(self, name, orbit: Orbit):
        self.name = name
        self.orbit = orbit

class Body(Orbitable):
    def __init__(self, name, radius, orbit: Orbit, mu):
        Orbitable.__init__(self, name, orbit)
        self.radius = radius
        self.mu = mu

class Vessel(Orbitable):
    def __init__(self, name, orbit: Orbit):
        Orbitable.__init__(self, name, orbit)
        self.parts = []
    
    @property
    def engines(self):
        return [part for part in self.parts if isinstance(part, Engine)]
    
    @property
    def tanks(self):
        return [part for part in self.parts if isinstance(part, ResourcesTank)]
    
    @property
    def torque(self):
        return sum([part.torque for part in self.parts if isinstance(part, Engine)])
    
    @property
    def isp(self):
        mean_fuel_consumption = sum([engine.torque / engine.isp for engine in self.engines])
        return self.torque / mean_fuel_consumption
    
    @property
    def mass(self):
        return sum([part.mass for part in self.parts])


class Part(object):
    def __init__(self):
        self.mass = 0.0

class ResourcesTank(Part):
    def __init__(self):
        self._resources = {}
        self.drymass = 0.0
    
    @property
    def resources(self):
        return self._resources
    
    @resources.setter
    def resources(self, resource, value):
        self._resources[resource] = value

    @property
    def mass(self):
        fuelmass = sum([resource.density * value for resource, value in self._resources.items()])
        wetmass = self.drymass + sum([resource.density * value for resource, value in self._resources.items()])
        
        logging.debug('drymass: %f', self.drymass)
        logging.debug('fuelmass: %f', fuelmass)
        logging.debug('wetmass: %f', wetmass)

        return wetmass

class Engine(Part):
    def __init__(self):
        self.torque = None
        self.resources = []
    
    @property
    def isp(self):
        isp = self.torque / self.fuel_flow_rate
        logging.debug('engine isp: %f', isp)
        return isp
    
    @property
    def fuel_flow_rate(self):
        # 9.80665 is a gravity constant at ground level of kerbin
        # actually 9.82 for ksp???
        #g0 = 9.80665
        g0 = 9.81
        return sum([resource.density * consumption * g0 for resource, consumption in self.resources.items()])

def create_game_globals():
    game = Game()

    # fuel params
    game.resources['xenon'] = Resource(density = 9.99999974737875 * (10**-5))
    game.resources['electricity'] = Resource(density = 0.0)
    
    return game

def create_sun() -> Body:
    name = "Kerbol"
    radius = 261600000
    mu = 1.1723328 * (10 ** 18) # m^3 / s^2

    return Body(name, radius, None, mu)

def create_kerbin(body: Body) -> Body:
    name = "Kerbin"
    radius = 600000
    #mu = G*M # G is gravity constant, M is Kerbin mass
    mu = 3.5316000 * (10 ** 12) # m^3 / s^2

    # https://wiki.kerbalspaceprogram.com/wiki/Kerbin
    # orbiting around Kerbol, ref point
    eccentricty = 0.0
    semi_major_axis = 13599840256 # 13 599 840 256 m 
    inclination = 0.0
    longtitude_AN = 0.0
    longtitude_PE = 0.0
    orbit = Orbit(eccentricty, semi_major_axis, inclination, longtitude_AN, longtitude_PE)
    orbit.body = body

    return Body(name, radius, orbit, mu)

def create_test_orbit(body: Body) -> Orbit:
    # creating test orbit
    eccentricty = 0.00087202515127280354
    semi_major_axis = 677611.24982132285 # in m
    inclination = 0.86208014936579747
    longtitude_AN = 267.79842337347509
    longtitude_PE = 317.59481361307394

    orbit = Orbit(eccentricty, semi_major_axis, inclination, longtitude_AN, longtitude_PE)
    orbit.body = body
    # NOTE: ksp saves mean_anomaly in file while we computate it from formula

    return orbit

def create_test_vessel(game: Game, orbit: Orbit):
    ship = Vessel(name="smolsat", orbit=orbit)
    
    # adding 1x xenon engine, should be done through config
    engine = Engine()
    engine.mass = 0.25 # in kg
    engine.torque = 2.0 # in kN
    engine.resources = { game.resources['xenon'] : 0.486, game.resources['electricity'] : 8.74 }
    ship.parts.append(engine)

    for _ in range(4):
        fueltank = ResourcesTank()
        fueltank.drymass = 0.013500001281499 # kg
        fueltank.resources[game.resources['xenon']] = 405
        ship.parts.append(fueltank)

    ### ### ### ### DUMMY ### ### ### ###
    # we wont simulate other parts unless required
    dummy = Part()
    # 1.296 kg substracting previously real parts
    dummy.mass = 1.296
    dummy.mass -= sum(engine.mass for engine in ship.engines)
    dummy.mass -= sum(tank.mass for tank in ship.tanks)
    ship.parts.append(dummy)
    logging.debug('ship mass: %f', ship.mass)

    return ship

# last eject angle moment should be exact as PE to have correct dT
#
# Kepler 3rd law
def get_transfer_time(r1, r2, mu):
    logging.debug('\nCalculating transfer time for semi-major axis from r1 to r2 orbit')
    logging.debug('r1: %f', r1)
    logging.debug('r2: %f', r2)
    logging.debug('mu: %f', mu)
    
    Ttransfer = math.pi * math.sqrt(((r1 + r2) ** 3) / (8 * mu))

    logging.info('Transfer time = %s, %f', datetime.timedelta(seconds=Ttransfer), Ttransfer)
    return Ttransfer

# we're getting full time required for raising AP from initial orbit
# which is largest elliptic orbit semi-period + previous elliptic orbits periods + starting orbit time to node
# 
# should it be iterative algorithm? as those orbits arent precomputed
# theoretically this is not required, as we can raise initial orbit inb4 reachin ejection time
# on second through, extended raise time leave us with limited time to do so, therefor need to approximte rise time
def get_full_raise_time(rstart, # initial CIRCULAR orbit, or using PE
                        targetAp, # target orbit AP
                       	burnsDvLimit # burns Dv limit for low twr vessels
                      	):
  	pass

def get_required_dv1(r1, r2, mu, r):
    logging.debug('\nCalculating dV1 m/s required for Hoffman transfer ejection burn')
    logging.debug('r1: %f', r1)
    logging.debug('r2: %f', r2)
    logging.debug('mu: %f', mu)
    logging.debug('r: %f', r)

    dV1 = math.sqrt(mu / (r + r1)) * (math.sqrt((2 * r2) / ((r + r1) + r2)) - 1)

    logging.info('dV1 = %f m/s', dV1)
    return dV1

# Improved accuracy by using Thiolkovsky rocket equation:
# dv = isp * 9.81 * math.log(m0/m1)
# Simplified formula works only for short burns with insignificant mass change
# dV * mass / torque
def get_burn_time(dVrequired, vessel):
    logging.debug('\nCalculating ejection burn time')
    logging.debug('dV: %f', dVrequired)
    logging.debug('Vessel mass: %f', vessel.mass)
    logging.debug('Vessel torque: %f', vessel.torque)
    logging.debug('Vessel Isp: %f', vessel.isp)

    # NOTE: 9.81 is a constant, not related to gravity?
    g0 = 9.81
    mass_initial = vessel.mass
    mass_final = mass_initial * math.exp( - dVrequired / (vessel.isp * g0))
    mass_propellant = mass_initial - mass_final
    mass_flow_rate = vessel.torque / (vessel.isp * g0)
    T_burn = mass_propellant / mass_flow_rate

    logging.info('Burn time = %s, %f', datetime.timedelta(seconds=T_burn), T_burn)
    return T_burn

# returns T0+time before starting first burn
def get_nodes(initial_orbit, dVrequired, T_burn, T_transfer, max_node_angle):
    logging.debug('\nCalculating ejection nodes')
    logging.debug('dV: %f', dVrequired)
    logging.debug('Time burn: %f', T_burn)
    logging.debug('Time transfer: %f', T_transfer)
    logging.debug('Max burn angle diff from prograde: %f', max_node_angle)

    return nodes

# TODO: calc phase angle
# TODO2: take into account inter\introplanetary transfers
def get_phase_angle():
	pass

# TODO: improve base accuracy from hoffman transfer
def get_ejection_engle():
  	pass

def main():
    FORMAT = '%(levelno)s:%(funcName)s:%(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT)

    game = create_game_globals()

    sun = create_sun()
    kerbin = create_kerbin(sun)

    vessel = create_test_vessel(game, create_test_orbit(kerbin))
    logging.info('vessel.orbit.AP: %f', vessel.orbit.AP)
    logging.info('vessel.orbit.PE: %f', vessel.orbit.PE)
    logging.info('vessel.orbit.period: %s', datetime.timedelta(seconds=vessel.orbit.period))

    T_mission = 1989049.0211275599 # TODO: update at launch
    logging.info('vessel.orbit.mean_anomaly: %f', vessel.orbit.mean_anomaly(T_mission))

    T_transfer = get_transfer_time(vessel.orbit.altitude(T_mission), G_TARGET_ORBIT, kerbin.mu)
    dV1 = get_required_dv1(vessel.orbit.altitude(T_mission), G_TARGET_ORBIT, kerbin.mu, kerbin.radius)
    
    # auxiliary for long burns
    T_burn = get_burn_time(dV1, vessel)

    # arbitrary
    max_node_angle = 5.0
    nodes = get_nodes(vessel.orbit, dV1, T_burn, T_transfer, max_node_angle)


if __name__ == "__main__":
    main()


