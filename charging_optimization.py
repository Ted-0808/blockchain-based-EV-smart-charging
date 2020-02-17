# -*- coding: utf-8 -*-
"""
Created on Fri Feb 14 17:08:14 2020

@author: zeguang.li
"""

## connection to CP database
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['cpDB']
collection = db.test1

#grid power limit 
powerLimit = 55
_cpGroup = 'G1'
#which charging plaza to optimize
timestep = 15 # in minutes

# update the power of CP for the next time step
def database_update(_cpid, changes):
    query = {"evse_id":_cpid}
    collection.update_one(query,changes)

## this optimization should be triggered every 15 minutes
def optimization(_cpGroup, powerLimit):
    # get updated status from cpDB
    charging_pool =[]
    chargingPoolNext =[]
    totalPowerDemand =0
    flex_supply =0
    dbcopy =[]
    
    for i in collection.find({'cp_group':_cpGroup,'status':'O'},{'_id':0,'evse_id':1, 'powerValue':1,'chargingInfo.user_id':1, 'chargingInfo.E':1,'chargingInfo.T':1}):
        dbcopy.append(i)
        print(i)
    
    for i in dbcopy:
        charging_pool.append({"evse_id":i['evse_id'],"CPpower":i['powerValue'],"userID":i['chargingInfo']['user_id'],"E":i['chargingInfo']['E'],"T":i['chargingInfo']['T']})
        print(charging_pool)
    
    for i in charging_pool:
        i['F_t'] = (i['T'] - i['E']/i['CPpower']*60)
        if (i['F_t']>= timestep):
            i['F_p'] = i['CPpower']
        else:
            i['F_p'] = (i['F_t'] * i['CPpower']/timestep)
        
        totalPowerDemand += i['CPpower']
        flex_supply += i['F_p']
        i['flex_rec']= 0
    
    # allocate the charging power again and send back to cpDB
    if totalPowerDemand <= powerLimit:
        #no grid congestion, update the db with full power supply for each CP
        for i in charging_pool:
            newPowerLevel = {"$set":{"updatedPower":i['CPpower']}}
            database_update(i['evse_id'], newPowerLevel) 
            
            i['T'] -= timestep
            i['E'] -= i['CPpower']*(timestep/60)
            chargingPoolNext.append(i)
            
        print('all updated1')
    else :
    
        flex_demand = totalPowerDemand - powerLimit
        #update db with reduced power proportional to each CP 
        for i in charging_pool:
            _updatedPower = (i['CPpower'] - flex_demand/flex_supply *i['F_p'])
            newPowerLevel = {"$set":{"updatedPower":_updatedPower}}
            database_update(i['evse_id'], newPowerLevel)
            
            i['T'] -= timestep
            i['E'] -= _updatedPower*(timestep/60)
            chargingPoolNext.append(i)
        print('all updated2')
    collection.save({'_id':'est_next','charging_profile':chargingPoolNext})
    return chargingPoolNext


#also give out a expected chargingpool result after next time step so that, new charigng tickets in the next time step can be evaluated based on that.
# 'CPpower' should be included!!!