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
#mu = G*M # G is gravity constant, M is Kerbin mass
G_INITIAL_BODY_MU = 3.5316000 * (10 ** 12) # m^3 / s^2
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

class Orbit:
    def __init__(self, semi_major, semi_minor, eccentricty):
        self.semi_major = semi_major
        self.semi_minor = semi_minor
        self.eccentricty = eccentricty
        # TODO: properties - eccentricty, AN\DN, inclination, etc...
    
    @property
    def altitude(self, T):
        return

class Vessel(object):
    def __init__(self, orbit):
        self.parts = []
        self.orbit = orbit
    
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

    def altitude(self, T):
        if T > self.orbit.period:
            T = T % self.orbit.period
        return self.orbit.altitude(T)


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

def create_test_vessel(game: Game):
    # creating test orbit
    # pe=77040.3, ap=78244.3
    orbit = Orbit(semi_major=677640.178, semi_minor=677639.911, eccentricty=0.00089)
    ship = Vessel(orbit)

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


    return 0.0

# TODO: calc phase angle
# TODO2: take into account inter\introplanetary transfers
def get_phase_angle():
	pass

# TODO: improve base accuracy from hoffman transfer
def get_ejection_engle():
  	pass

def get_gravity(altitude):
    return G_INITIAL_BODY_MU / (G_INITIAL_BODY_RADIUS + altitude)**2

def main():
    FORMAT = '%(levelno)s:%(funcName)s:%(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT)

    game_properties = create_game_globals()
    vessel = create_test_vessel(game_properties)

    T_mission = 0.0
    T_transfer = get_transfer_time(vessel.altitude(T_mission), G_TARGET_ORBIT, G_INITIAL_BODY_MU)
    dV1 = get_required_dv1(vessel.altitude(T_mission), G_TARGET_ORBIT, G_INITIAL_BODY_MU, G_INITIAL_BODY_RADIUS)
    
    # auxiliary for long burns
    T_burn = get_burn_time(dV1, vessel)

    # arbitrary
    max_node_angle = 5.0
    nodes = get_nodes(vessel.orbit, dV1, T_burn, T_transfer, max_node_angle)


if __name__ == "__main__":
    main()


