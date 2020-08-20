#-------------------------------------------------------------------------
# 
# The MIT License (MIT)
#
# Copyright (c) 2020 Liam Kennedy : 8/20/2020
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#-------------------------------------------------------------------------

import math
import ephem
from datetime import datetime
from datetime import timedelta

def VisualMagnitude( iss, obs, sun ):
    # Note:  Make sure obs.date is set as needed AND 
    # iss.compute(obs) and sun.compute(obs) is done before calling this function
    
    AU = 149597871 # Astronimical Unit (km)
    STANDARD_MAG = -1.3 # intrinsic brightness of ISS at 1000km.  
                        # Cannot remember source for this - some suggest it should be lower now (making ISS brighter)
                        # I still find this lines up with how I think it is visually
    STATUS_GOOD = True
    STATUS_BAD = False
    
    if iss.eclipsed :
       return (None, STATUS_BAD) #no valid mag data as the ISS is eclipsed (in the earths shadow)
          
    # Note - no idea why I do this here... it's never used
    # Leaving it here just in case someone realized why I even put this here :-) 
    # Probably just my early "scribblings" trying to figure stuff out
    sun_az_deg = math.degrees(sun.az)
    iss_az_deg = math.degrees(iss.az)
    phase_angle = abs(180-abs(sun_az_deg-iss_az_deg)) 
                                                      
                                                      
    # SSA Triangle.  We have side a and b and angle C.  Need to solve to find side c
    a = sun.earth_distance * AU - ephem.earth_radius #distance sun from observer (Km)
    b = iss.range / 1000 # distance to ISS from observer (Km) 
    angle_c = ephem.separation( (iss.az, iss.alt), ( sun.az, sun.alt) )
    c = math.sqrt( math.pow(a,2) + math.pow(b,2) - 2*a*b*math.cos( angle_c) )
    
    # now we find the "missing" angles (of which angle A is the one we need)    
    angle_a = math.acos((math.pow(b,2) + math.pow( c,2) - math.pow(a,2)) / (2 * b * c)) # I think angle_a is the phase angle
    angle_b = math.pi - angle_a - angle_c #note: this is basically ZERO - not a big surprise really.  
    phase_angle = angle_a # This is the angle we need.  BINGO!!
    
    # This is the MAGIC equation (Author: Matson, Robert)
    mag = STANDARD_MAG - 15 + 5*math.log10(iss.range/1000) - 2.5*math.log10(math.sin(phase_angle)+((math.pi-phase_angle)*math.cos(phase_angle)))
    return (mag, STATUS_GOOD)
    
if __name__ == '__main__':  

   #code here from http://hoegners.de/Maxi/geo/ (YES.. I just googled it)
   direction_names = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
   directions_num = len(direction_names)
   directions_step = 360./directions_num
   
   def direction_name(angle):
       index = int(round( angle /directions_step ))
       index %= directions_num
       return direction_names[index]
   #end of code lifted from geo.py

   # IMPORTANT!!! This example code will display the Magnitude of the ISS for the NEXT PASS (not necessarily a visible one)
   
   SKIP_SECONDS = 10

   # TLE from here:  http://www.celestrak.com/NORAD/elements/stations.txt
   # NOTE:  MAKE SURE TO BE A GOOD USER OF CELESTRAK and ONLY dowload the TLE when you need to update it
   # Usually once a day is more than enough accuracy
     
   iss_tle = ( "ISS (ZARYA)", \
               "1 25544U 98067A   20233.73843000 -.00002996  00000-0 -45975-4 0  9997", \
               "2 25544  51.6453  29.0063 0001485  60.4588  71.0712 15.49170160242027" )
               
   iss = ephem.readtle(iss_tle[0], iss_tle[1], iss_tle[2] )
   
   obs = ephem.Observer()
   
   # Set observer location - for this demo - this is Johnson Space Center in Houston,TX
   obs.lat = "29.5593" 
   obs.lon = "-95.0900"  
       
   obs.date = datetime.utcnow()
   print "start time:", ephem.localtime(obs.date)
   sun = ephem.Sun(obs)
   
   # IMPORTANT:  Did you know the results from obs.next_pass(iss) get REALLY REALLY WEIRD if you run that DURING a pass????
   tr, azr, tt, altt, ts, azs = obs.next_pass(iss)
   if tr > ts :
      # ok so this odd thing happens when there is pass already in progress at the start time chosen
      # Yes - really.  The Time of Rise is AFTER the time Set. 
      # It "sort of" makes sense if you think about it.  
      # so roll back the clock by 60 minutes 
      # This SHOULD fix it.   
      obs.date = datetime.utcnow()+timedelta(minutes=-60)
      tr, azr, tt, altt, ts, azs = obs.next_pass(iss)
   
   obs.date = tr
      
   print "Next pass for: ", math.degrees(obs.lat),math.degrees(obs.lon)
   print "    Rise time :", ephem.localtime(tr).strftime('%Y/%m/%d %H:%M:%S')
   print "           Az : {:6.2f}".format(math.degrees(azr))
   print " Transit Time :",ephem.localtime(tt).strftime('%Y/%m/%d %H:%M:%S')
   print "          Alt : {:6.2f}".format(math.degrees(altt))
   print "     Set Time :", ephem.localtime(ts).strftime('%Y/%m/%d %H:%M:%S')
   print "           Az : {:6.2f}".format(math.degrees(azs))
   
   print "-----------------------------------------------------------------------------"
   print "| TIME                |   Alt  |     Az      | Range(km) |  Mag   | Sun Alt |"
   #| 2020/08/20 15:27:33 |  -0.00 | 250.37 WSW  |   2414 |   3.49 |  31.04 |

   while obs.date < ts :
   
         iss.compute(obs)
         sun.compute(obs)
         
         mag, magOK = VisualMagnitude( iss, obs, sun )
         
         #Time                   |  Alt     AZ 
         # 2020/08/20 15:27:33     0.00 250.37 WSW    2414   3.49  31.04
         #mag=None 
         print "| "+ephem.localtime(obs.date).strftime('%Y/%m/%d %H:%M:%S'), 
         print "| {:6.2f} | {:6.2f} {:4} | {:6.0f}    | {:6.2f} | {:6.2f}  | {:10}".format( math.degrees(iss.alt), 
                                                                            math.degrees(iss.az), 
                                                                            direction_name(math.degrees(iss.az)), 
                                                                            iss.range/1000, 
                                                                            999 if mag is None else mag, 
                                                                            math.degrees(sun.alt) ,  
                                                                            "eclipsed" if iss.eclipsed else "" )           
         obs.date = ephem.Date( obs.date + ephem.second * SKIP_SECONDS )
          
   print "-----------------------------------------------------------------------------"
   
   
   
   