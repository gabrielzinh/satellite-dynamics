from orekit.pyhelpers import setup_orekit_curdir, download_orekit_data_curdir;
from org.orekit.utils import Constants, IERSConventions;
from org.orekit.time import AbsoluteDate, TimeScalesFactory;
from org.orekit.frames import FramesFactory;
from org.orekit.orbits import KeplerianOrbit, PositionAngleType, OrbitType;
from org.orekit.bodies import CelestialBodyFactory, OneAxisEllipsoid;
from org.orekit.forces.gravity import HolmesFeatherstoneAttractionModel, ThirdBodyAttraction;
from org.orekit.forces.gravity.potential import GravityFieldFactory;
from org.orekit.forces.radiation import SolarRadiationPressure, IsotropicRadiationSingleCoefficient;
from org.orekit.propagation import SpacecraftState;
from org.orekit.propagation.numerical import NumericalPropagator;
from org.hipparchus.ode.nonstiff import DormandPrince853Integrator;
from math import radians;
import orekit, os, json;
vm = orekit.initVM();
Path = ".\\orekit-data.zip";

if (not os.path.exists(Path)):
    download_orekit_data_curdir(Path);

setup_orekit_curdir(Path);

class Scenario:
    @staticmethod
    def __createorbits__(data_file, entries):
        Data = dict();
        Orbits = list();

        if (data_file.find(".") != -1):
            data_file = data_file.partition(".")[0];

        with open(f"{data_file}.json", "r") as file:
            Data = json.load(file);

        for Entry in entries:
            CurData = Data[Entry];
            a, e = float(CurData["SEMIMAJOR_AXIS"]) * 1000.0, float(CurData["ECCENTRICITY"]);
            i, pa = radians(float(CurData["INCLINATION"])), radians(float(CurData["ARG_OF_PERICENTER"]));
            Raan, Anomaly, Epoch = radians(float(CurData["RA_OF_ASC_NODE"])), radians(float(CurData["MEAN_ANOMALY"])), CurData["EPOCH"];
            AnomalyType, Frame, Date = PositionAngleType.MEAN, FramesFactory.getTEME(), AbsoluteDate(Epoch, TimeScalesFactory.getUTC());
            InitialOrbit = KeplerianOrbit(a, e, i, pa, Raan, Anomaly, AnomalyType, Frame, Date, Constants.EGM96_EARTH_MU);
            Orbits.append(InitialOrbit);

        return Orbits;

    def __addforcemodel__(self, force_model, force_name, position):
        force_name = str.upper(force_name);

        if (force_name not in self.force_models and self.propagator is not None):
            self.force_models.insert(position, force_name);
            self.propagator.addForceModel(force_model);

        return self;

    def __addthirdbodyattraction__(self, celestial_body, force_name, position):
        ForceModel = ThirdBodyAttraction(celestial_body);
        return self.__addforcemodel__(ForceModel, force_name, position);

    def __init__(self, spacecraft_mass = 1.0, spacecraft_cross_section = 1.0, reflection_coef = 1.0):
        self.spacecraft_mass = float(spacecraft_mass);
        self.spacecraft_cross_section = float(spacecraft_cross_section);
        self.reflection_coef = float(reflection_coef);
        self.initial_state = None;
        self.propagator = None;
        self.is_initial_state_set = False;
        self.force_models = list();

    def __str__(self):
        Parameters = f"Spacecraft Mass: {self.spacecraft_mass} kg, Spacecraft Cross Section: {self.spacecraft_cross_section} m², Reflection Coefficient: {self.reflection_coef}\n";
        InitialPos = f"Initial Position: {self.initial_state.getPVCoordinates().getPosition()}";
        InitialVel = f"Initial Velocity: {self.initial_state.getPVCoordinates().getVelocity()}";
        return Parameters + "\n" + InitialPos + "\n" + InitialVel + "\n";

    def BuildInitialState(self, data_file, entry = 0):
        data_file = str(data_file);

        if (data_file.find(".") != -1):
            data_file = data_file.partition(".")[0];

        InitialOrbit = Scenario.__createorbits__(data_file, [entry])[0];
        InitialState = SpacecraftState(InitialOrbit).withMass(self.spacecraft_mass);
        self.initial_state = InitialState;
        self.is_initial_state_set = True;
        return self;

    def BuildBasicPropagator(self, min_step = 0.001, max_step = 10.0, abs_error = 1.0, rel_error = 1.0):
        if (not self.is_initial_state_set):
            return None;

        Integrator = DormandPrince853Integrator(min_step, max_step, abs_error, rel_error);
        Propagator = NumericalPropagator(Integrator);
        Propagator.setOrbitType(OrbitType.KEPLERIAN);
        Propagator.setInitialState(self.initial_state);
        self.propagator = Propagator;
        return self;

    def AddEarthGravity(self):
        EarthFrame, GravityProvider = FramesFactory.getITRF(IERSConventions.IERS_2010, True), GravityFieldFactory.getNormalizedProvider(12, 12);
        ForceModel = HolmesFeatherstoneAttractionModel(EarthFrame, GravityProvider);
        return self.__addforcemodel__(ForceModel, "Earth Gravity", 0);

    def AddSunGravity(self):
        SunModel = CelestialBodyFactory.getSun();
        return self.__addthirdbodyattraction__(SunModel, "Sun Gravity", 1);

    def AddMoonGravity(self):
        MoonModel = CelestialBodyFactory.getMoon();
        return self.__addthirdbodyattraction__(MoonModel, "Moon Gravity", 2);

    def AddSolarRadiationPressure(self):
        SRPModel = IsotropicRadiationSingleCoefficient(self.spacecraft_cross_section, self.reflection_coef);
        EarthModel = OneAxisEllipsoid(Constants.WGS84_EARTH_EQUATORIAL_RADIUS, Constants.WGS84_EARTH_FLATTENING, FramesFactory.getITRF(IERSConventions.IERS_2010, True));
        ForceModel = SolarRadiationPressure(CelestialBodyFactory.getSun(), EarthModel, SRPModel);
        return self.__addforcemodel__(ForceModel, "Solar Radiation Pressure", 3);

    def AddAllForces(self):
        self.AddEarthGravity();
        self.AddSunGravity();
        self.AddMoonGravity();
        self.AddSolarRadiationPressure();

    def RemoveAllForces(self):
        self.propagator.removeForceModels();
        self.force_models = list();
