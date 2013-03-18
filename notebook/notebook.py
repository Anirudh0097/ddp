import sympy
import os
from getparameters import *
from currenteqs import *
from parsers import *
from config import *
from numericals import *
from scipy.integrate import odeint
import matplotlib.pyplot as plt

# This file is the topmost layer of the project. Only function level calls and data transfer is shown here. 
global linPJac, B, C, D, linPVal, inputm, count, linP
#
# These functions are used in the integration process
# Derivative of the function at any point is given by
# dx/dt = Summation( weight*(Jacobian * ( state ) + B * ( input ) + ( Val @ state - Jacobian * linPoint )))
def dervPWL(y,t):
	#order = len(y)
	weights = normcalc( y )
	#count = len(weights)
	temp = 0
    
	linPVal = []
	linPJac = []
	for i in range( count ):
		sub1={state[k]:abs(float(datapoints[ i ][k])) for k in state}
		input_signals = get_input_signals( t ) 
		#sub1[ state[ 'inp' ] ] = input_signals[ 0 ] 
		for k in range( len( input_list ) ) :
			sub1[ state[ str( input_list[ k ] ) ] ] = input_signals[ k ]
		#sub1[ state[ '0' ] ]= 0.0
		for k in constant_dict.keys():
			sub1[ state[ k ] ] = constant_dict[ k ] 
		linPVal.append( Sym2NumArray( ( Matrix[ i ].linPVal ).evalf( subs = sub1 ) ) )
		linPJac.append( Sym2NumArray( ( Matrix[ i ].linPJac ).evalf( subs = sub1 ) ) )
	inputM = Sym2NumArray(inputm.evalf( subs = sub1 ))
    
	for i in range(count):
		temp = temp +  weights[ i ] * ( linPVal[ i ] + (numpy.dot( linPJac[ i ], y )).reshape( order ,1 ) - (numpy.dot( linPJac[ i ], linP[ i ] )).reshape( order ,1 ) + (numpy.dot( B[ i ], inputM )) )
	return (temp.reshape(1, order))[0]

# Calculates the weighing function depending on the proximity to linearizatoin points
def normcalc( y ) :
	norm = numpy.array([ 10.0**(-20*numpy.linalg.norm( linP[ i ] - y.reshape(order,1) )) for i in range(count) ])
	return norm/norm.sum()


def initialize():
    if os.path.isfile('./config.py'):
        print "Config file in ", os.path.abspath('./config.py')
        print "-----------------------------------------------"
    else:
        print "Config file in PYTHONPATH"
        print "-----------------------------------------------"

initialize()

initialcond = get_initialcond(file_voltage, sim_begin)

state = get_states(file_voltage,sim_begin)

stateorder = get_stateorder(state)

steadystate = get_steadystate(file_voltage,initialcond,stateorder, sim_end,order)

delta = get_linpdiff(initialcond,steadystate,stateorder,order)

print "Simulation begins at ", sim_begin

count,time = get_linPoints(file_voltage,initialcond,delta/denominator,order,stateorder,sim_begin)

datapoints = get_datapoints(file_voltage, count , time)

currents = get_currents(file_current,count,time)

regions = get_region_operation(datapoints,file_netlist,count)

Vth = get_vth()

regexp = get_regexp_eqs(input_list)

inputorder = get_inputorder(state, input_list )

linP = get_num_linP(count,order,datapoints,stateorder)

C, B , D , inputm = init_statematrices(count,order,input_list,output_list,stateorder,state)

Matrix, B, C, D = get_statematrices( B, C, D, inputm, count, order, regions, state, regexp, datapoints, stateorder, inputorder, Vth)

y0 , time_intg = get_parameters_integration( initialcond, intg_end, stateorder )

solnPWL = odeint(dervPWL, y0, time_intg)

#--------------------------------------------------------------------------------------------
# Plotting the output obtained with integration
print "Plotting output " 
time_linp = [ float( i ) - sim_begin for i in time] 
C_ones = [i for i in range( len( stateorder ) ) if str( stateorder[ i ] ) in output_list ]

for k in range(len(C_ones)):
    plt.figure(k)
    calc, = plt.plot(time_intg, numpy.array([ abs(float(solnPWL[i][C_ones[k]])) for i in range(len(time_intg) )] ), '--')
    plt.ylabel(r'$V_{'+str(stateorder[C_ones[k]])+'}$' )
    plt.xlabel(r'$time$')
    x , y  = [], []
    for i in import_text(file_voltage,"\t"):
        if (float( i[ 'time' ] ) < intg_end+sim_begin) and (float( i[ 'time' ]  )> sim_begin) :
            y.append( i[ str( stateorder[ C_ones[ k ] ] ) ] ), x.append( float(i[ 'time' ])-sim_begin )
    plt.ylabel(r'$V_{'+str(stateorder[C_ones[k]])+'}$' )
    plt.xlabel(r'$time$')
    plt.title(str(cirname)+' output')
    spice, = plt.plot(x,y)
    #plt.figsize(10,10)
    plt.figlegend([calc,spice],('Calculated','Spice'),'lower right')
    x_time , y_val = [], []
    for i in range( count ):
        x_time.append(float( time_linp[ i ] ) )
        y_val.append( float(datapoints[ i ] [str(stateorder[ C_ones[ k ] ] )]) )
    plt.plot( x_time,y_val,'ro' )
plt.show()

