clearscreen.

function hoffman1 {
    clean_nodes().

    SET targetBody TO BODY("Mun").
    SET targetAlt to targetBody:ALTITUDE - targetBody:SOIRADIUS.
    // SET myAlt TO ship:body:altitudeOf(positionAt(ship, time:seconds + time)). // for future alt
    SET myAlt TO ship:ALTITUDE. // using current alt as orbit radius
    SET mySpeed TO ship:VELOCITY:ORBIT:MAG.
    SET myBody to BODY("Kerbin").

    PRINT "Current alt: " + myAlt + "m".
    PRINT "Target orbit: " + targetAlt + "m".
    PRINT "Current speed: " + mySpeed + "m/s".

    PRINT myBody:NAME + " radius: " + myBody:RADIUS.
    SET dV1 to hoffman1_get_dv1(myAlt, targetAlt, myBody:MU, myBody:RADIUS).
    PRINT "dV1: " + dV1 + "m/s".
    PRINT "Ejection speed: " + (mySpeed + dV1) + "m/s".

    SET transferTime to hoffman1_get_transfer_time(myAlt, targetAlt, myBody:MU, myBody:RADIUS).
    PRINT "Transfer time: " + transferTime. 

    // TODO: REDO ALL
    // delaytime_degrees = t_hoffmann/Tmun*360 #in deg
    //SET targetTransferOrbitAngle to transferTime/targetBody:ORBIT:PERIOD * 360.
    //PRINT "Target transfer angle : " + targetTransferOrbitAngle.
    //SET currentPhaseAngle to get_phase_angle(SHIP:ORBIT, targetBody:ORBIT).
    //PRINT "Current phase angle: " + currentPhaseAngle.
    //SET ejectionAngle to get_ejection_angle(myAlt, dV1, myBody:MU).
    //PRINT "Ejection angle: " + ejectionAngle.
    //SET timeToEject to get_ejection_time(ship:ORBIT:PERIOD, ejectionAngle, currentPhaseAngle).
    //PRINT "Ejection time: " +  timeToEject.

    // debugging
    SET timeToEject to 600.
    add_node (TIME:SECONDS + timeToEject, 0, 0, dV1).

    // INJECTION
    SET dV2 to hoffman1_get_dv2(myAlt, targetAlt, myBody:MU, myBody:RADIUS).
    PRINT "dV2: " + dV2 + "m/s".
    SET timeToInject to TIME:SECONDS + timeToEject + transferTime.
    add_node (timeToInject, 0, 0, -dV2).

}

// dV = math.sqrt(mu / (r + r1)) * (math.sqrt((2 * r2) / ((r + r1) + r2)) - 1)
function hoffman1_get_dv1 {
    parameter altitude. // initial altitude
    parameter r2. // target
    parameter mu. // body mu
    parameter r. // body radius

    SET r1 to altitude + r.
    SET dV to SQRT(mu / r1) * (SQRT((2 * r2) / (r1 + r2)) - 1).
    return dV.
}

// dV = math.sqrt(mu / r2) * (1 - math.sqrt((2 * (r + r1)) / ((r + r1) + r2)))
function hoffman1_get_dv2 {
    parameter altitude. // initial altitude
    parameter r2. // target
    parameter mu. // body mu
    parameter r. // body radius

    SET r1 to altitude + r.
    SET dV to SQRT(mu / r2) * (SQRT((2 * r1) / (r1 + r2)) - 1).
    return dV.
}

// transfer time
// t_hoffmann = math.pi*((R1+R2)**3/(8*mu))**(0.5) #in s #in s
function hoffman1_get_transfer_time {
    parameter altitude. // initial altitude
    parameter r2. // target orbit
    parameter mu. // body mu
    parameter r. // body radius

    SET r1 to altitude + r.
    return constant:PI * SQRT(((r1 + r2) ^ 3) / (8 * mu)).
}

function get_phase_angle {
    parameter myOrbit.
    parameter targetOrbit.

    //PRINT "myOrbit:LONGITUDEOFASCENDINGNODE: " + myOrbit:LONGITUDEOFASCENDINGNODE.
    //PRINT "myOrbit:ARGUMENTOFPERIAPSIS: " + myOrbit:ARGUMENTOFPERIAPSIS.
    //PRINT "myOrbit:TRUEANOMALY: " + myOrbit:TRUEANOMALY.
    SET Angle1 TO myOrbit:LONGITUDEOFASCENDINGNODE+myOrbit:ARGUMENTOFPERIAPSIS+myOrbit:TRUEANOMALY. //the ships angle to universal reference direction.
    //PRINT "Angle1: " + Angle1.
    
    //PRINT "targetOrbit:LONGITUDEOFASCENDINGNODE: " + targetOrbit:LONGITUDEOFASCENDINGNODE.
    //PRINT "targetOrbit:ARGUMENTOFPERIAPSIS: " + targetOrbit:ARGUMENTOFPERIAPSIS.
    //PRINT "targetOrbit:TRUEANOMALY: " + targetOrbit:TRUEANOMALY.
    SET Angle2 to targetOrbit:LONGITUDEOFASCENDINGNODE+targetOrbit:ARGUMENTOFPERIAPSIS+targetOrbit:TRUEANOMALY. //target angle
    //PRINT "Angle2: " + Angle2.

    SET Angle3 to Angle2 - Angle1.
    //PRINT "Angle3: " + Angle3.

    SET Angle4 to Angle3 - 360 * floor(Angle3/360).
    //PRINT "Angle4: " + Angle4.

    return Angle4.
}

function get_ejection_angle {
    parameter parkR.
    parameter ejectV.
    parameter origingMU.

    SET Angle1 TO (ejectV ^ 2 / 2) - (origingMU / parkR).

    SET H to parkR * ejectV.

    SET Angle2 TO SQRT( 1 + ( ( 2 * Angle1 * ( H ^ 2 ) ) / ( origingMU ^ 2 ) ) ).

    SET Angle3 TO (COS( 1 / Angle2 ) ^ (-1)) * constant:RadToDeg.

    SET EjectAngle TO ( 180 - Angle3 ).

    RETURN EjectAngle.
}

function get_ejection_time {
    parameter myPeriod.
    parameter ejectAngle.
    parameter currentPhaseAngle.

    if (ejectAngle > currentPhaseAngle) {
        SET currentPhaseAngle to currentPhaseAngle + 360.
    }
    SET ejectDelay to (myPeriod * (currentPhaseAngle - ejectAngle) / 360 ).
    
    RETURN ejectDelay.
}

function clean_nodes {
    if HASNODE {
        print "Removing nodes...".
        FOR Node in ALLNODES {
            REMOVE NEXTNODE.
        }
    }
}

function add_node {
    parameter utime.
    parameter dVradial.
    parameter dVnormal.
    parameter dVprograde.

    //NODE(utime, radial, normal, prograde)
    SET myNode to NODE( utime, dVradial, dVnormal, dVprograde ).
    //PRINT myNode:PROGRADE + "m/s to prograde".
    ADD myNode.
}

function debug {
    until FALSE {
        clearscreen.
        
        SET myShip to SHIP.
        SET targetBody TO BODY("Mun").

        print get_phase_angle(myShip, targetBody).
    }
}


//debug().
hoffman1().