# Navigate this file at PythonAPI\carla\agents\navigation

import random
import sys
import glob
import os


# from carla.agents.navigation.global_route_planner_dao import GlobalRoutePlannerDAO


try:
    sys.path.append(glob.glob('../../dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
sys.path.insert(1, '../..')

import carla
from agents.navigation.global_route_planner_dao import GlobalRoutePlannerDAO

from global_route_planner import  GlobalRoutePlanner
# from global_route_planner_dao import GlobalRoutePlannerDAO 

import math
import controller

def spawn_vehicle(spawnPoint=carla.Transform(carla.Location(x=-6.446170, y=-79.055023, z=0.275307 ),carla.Rotation(pitch=0.0, yaw=0.0, roll=0.000000))):
    
    """
    
    This function spawn vehicles in the given spawn points. If no spawn 
    point is provided it spawns vehicle in this 
    position x=27.607,y=3.68402,z=0.02
    """
    
    spawnPoint=spawnPoint
    world = client.get_world()
    blueprint_library = world.get_blueprint_library()
    bp = blueprint_library.filter('vehicle.*')[7]
    vehicle = world.spawn_actor(bp, spawnPoint)
    return vehicle
    

    
def drive_through_plan(planned_route,vehicle,speed,PID):
    """
    This function drives throught the planned_route with the speed passed in the argument
    """ 

    i=0
    target=planned_route[0]
    while True: 
        vehicle_loc= vehicle.get_location() 
        distance_v =find_dist_veh(vehicle_loc,target) 
        control = PID.run_step(speed,target)
        vehicle.apply_control(control)
        
        if i==(len(planned_route)-1): # if the vehicle is at the last waypoint
            print("last waypoint reached")
            break 
        
        if (distance_v<3.5): # update new target when the vehicle is close to the current target
            control = PID.run_step(speed,target)
            vehicle.apply_control(control)
            i=i+1
            target=planned_route[i]

    control = PID.run_step(0,planned_route[len(planned_route)-1])
    vehicle.apply_control(control)
                

def find_dist(start ,end ):
    dist = math.sqrt( (start.transform.location.x - end.transform.location.x)**2 + (start.transform.location.y - end.transform.location.y)**2 )
    return dist

def find_dist_veh(vehicle_loc,target):
    dist = math.sqrt( (target.transform.location.x - vehicle_loc.x)**2 + (target.transform.location.y - vehicle_loc.y)**2 )
    return dist

def setup_PID(vehicle):

    """
    This function creates a PID controller for the vehicle passed to it 
    """
    args_lateral_dict = {
            'K_P': 1.95,
            'K_D': 0.2,
            'K_I': 0.07

            ,'dt': 1.0 / 10.0
            }

    args_long_dict = {
            'K_P': 1,
            'K_D': 0.0,
            'K_I': 0.75
            ,'dt': 1.0 / 10.0
            }

    PID=controller.VehiclePIDController(vehicle,args_lateral=args_lateral_dict,args_longitudinal=args_long_dict)
    
    return PID

client = carla.Client("localhost", 2000)
client.set_timeout(10)
# world = client.load_world('Town03')
# client.start_recorder("./recording01.log")
world = client.get_world()
world.unload_map_layer(carla.MapLayer.All)
# transform = random.choice(world.get_map().get_spawn_points())

amap = world.get_map()
sampling_resolution = 2
dao = GlobalRoutePlannerDAO(amap, sampling_resolution)
grp = GlobalRoutePlanner(dao)
grp.setup()
spawn_points = world.get_map().get_spawn_points()
a = carla.Location(spawn_points[0].location)
b = carla.Location(spawn_points[-1].location)
w1 = grp.trace_route(a, b) 

world.debug.draw_point(a,color=carla.Color(r=255, g=0, b=0),size=1.6 ,life_time=120.0)
world.debug.draw_point(b,color=carla.Color(r=255, g=0, b=0),size=1.6 ,life_time=120.0)

wps=[]

# for i in range(len(w1)):
#     wps.append(w1[i][0])
#     world.debug.draw_point(w1[i][0].transform.location,color=carla.Color(r=255, g=0, b=0),size=0.4 ,life_time=120.0)
w_cur = amap.get_waypoint(a)
for i in range(100):
    w_next = random.choice(list(w_cur.next(1)))
    wps.append(w_next)
    w_cur = w_next
    world.debug.draw_point(w_next.transform.location,color=carla.Color(r=255, g=0, b=0),size=0.4 ,life_time=120.0)

client.start_recorder("./recording02.log")
vehicle=spawn_vehicle(carla.Transform(carla.Location(spawn_points[0].location)))
PID=setup_PID(vehicle)

speed=30
drive_through_plan(wps,vehicle,speed,PID)
print("stop record")
vehicle.destroy()
# client.stop_recorder()
