
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['cpDB']
collection = db.test1

timestep = 15 # in minutes

powerLimit = 44
flex_level = 11 # if the flex power of a charging event is greater than 11 kW, it is catigorized to high flex group, otherwise, low flex group

def database_update(_cpid, changes):
    query = {"evse_id":_cpid}
    collection.update_one(query,changes)
    
    
def optimization(powerLimit): #in real situation, _cpGroup shoud be included
    # get updated status from cpDB
    charging_pool =[] # to extract date of charging event from the database
    chargingPoolNext = [] #for new charging events simulation, based on the result of next step optimization 
    totalPowerDemand =0
    flex_supply_G1 =0
    flex_supply_G2 =0
    dbcopy =[]
    num_G2 = 0 #num of events in low flex group
    global timestep
    
    
    #use pymongo to change status of all finished events, think about how to record flexibility?! the values will be deleted once the EV is driven away 

    collection.update_many({'cp_group':'G1','status':'L'},{"$set":{'status': 'Finished','updatedPower': 0}})
    
    #for the last timestep events, change status, update new power
    for i in collection.find({'cp_group':'G1','status':'O','chargingInfo.T':timestep}):
        
        _updatedPower = round(min(i['powerValue'],(4* i['chargingInfo']['E'])),1)
        newPowerLevel = {"$set":{"updatedPower":_updatedPower, 'status':'L'}}
        database_update(i['evse_id'], newPowerLevel) 
        powerLimit -= _updatedPower
        #these events will not be presented in the 'chargingPoolNext' for new charging request simulation, because their charging process will be finished in the upcoming timestep
    
    #all other charging processes will be evaluated
    for i in collection.find({'cp_group':'G1','status':'O'},{'_id':0,'evse_id':1, 'powerValue':1,'chargingInfo.user_id':1, 'chargingInfo.E':1,'chargingInfo.T':1}):
        dbcopy.append(i)
        print(i)
    
    for i in dbcopy:
        charging_pool.append({"evse_id":i['evse_id'],"CPpower":i['powerValue'],"userID":i['chargingInfo']['user_id'],"E":i['chargingInfo']['E'],"T":i['chargingInfo']['T']})
        print(charging_pool)
    
    for i in charging_pool:
        
        totalPowerDemand += i['CPpower'] ## this is ideal case, in reality, some EV can not charge with full CP power!!!
        i['F_t'] = max(round((i['T'] - (i['E']/i['CPpower'])*60),1),0) ## make sure i['F_t'] is non-negative value
        
        if (i['F_t']>= timestep):
            i['F_p'] = i['CPpower']
        else:
            i['F_p'] = round((i['F_t'] * i['CPpower']/timestep),1)
        
        # classify into two flex groups
        if (i['F_p']>= flex_level):
            i['flex_priority'] = 1 # highest priority from 1
            flex_supply_G1 += i['F_p']
        else:
            i['flex_priority'] = 2
            flex_supply_G2 += i['F_p']
            #count number of events in low flex group
            num_G2 += 1        

    # allocate the charging power again and send back to cpDB
    if totalPowerDemand <= powerLimit:
        #no grid congestion, update the db with full power supply for each CP
        for i in charging_pool:
            newPowerLevel = {"$set":{"updatedPower":i['CPpower']}}
            database_update(i['evse_id'], newPowerLevel)
            
            ### for simulation
            _energy = - round(i['CPpower']*0.25,1)
            _updatedStatus = {"$inc":{"chargingInfo.E":_energy,'chargingInfo.T': -timestep}}            
            database_update(i['evse_id'], _updatedStatus)
            chargingPoolNext.append(i)
        print('all updated1')
        
    else :    
        flex_demand = totalPowerDemand - powerLimit
        if flex_demand <= flex_supply_G1: # high flex group can solve the grid congestion (this indicate flex_G1 not equal to 0)
            #only this group will experience a reduced power
            for i in charging_pool:
                if (i['flex_priority'] == 1):
                    _updatedPower = round((i['CPpower'] - (flex_demand/flex_supply_G1) *i['F_p']),1)
                    _flex = round((i['CPpower'] - _updatedPower)*(timestep/60),1)
                    newPowerLevel = {"$set":{"updatedPower":_updatedPower}}
                    database_update(i['evse_id'], newPowerLevel)
                    newFlex = {"$inc":{"chargingInfo.flex_rec":_flex}}
                    database_update(i['evse_id'], newFlex)   
                    
                    ### for simulation
                    _energy = - round(_updatedPower*0.25,1)
                    _updatedStatus = {"$inc":{"chargingInfo.E":_energy,'chargingInfo.T': -timestep}}            
                    database_update(i['evse_id'], _updatedStatus) 
                    chargingPoolNext.append(i)
                    
                else:
                    newPowerLevel = {"$set":{"updatedPower":i['CPpower']}}
                    database_update(i['evse_id'], newPowerLevel)
                    
                    ###for simulation
                    _energy = - round(i['CPpower']*0.25,1)
                    _updatedStatus = {"$inc":{"chargingInfo.E":_energy,'chargingInfo.T': -timestep}}            
                    database_update(i['evse_id'], _updatedStatus)                      
                    chargingPoolNext.append(i)
                    
            print('all updated2')
                
        else: # high flex group all reduced to zero, low flex group reduce proportionally
            flex_demand_2 = flex_demand - flex_supply_G1

            for i in charging_pool:
                if (i['flex_priority'] == 1):
                    _updatedPower = round((i['CPpower'] - i['F_p']),1)
                    _flex = round(i['F_p']*(timestep/60),1)
                    newPowerLevel = {"$set":{"updatedPower":_updatedPower}}
                    database_update(i['evse_id'], newPowerLevel)
                    newFlex = {"$inc":{"chargingInfo.flex_rec":_flex}}
                    database_update(i['evse_id'], newFlex)  

                    ### for simulation
                    _energy = - round(_updatedPower*0.25,1)
                    _updatedStatus = {"$inc":{"chargingInfo.E":_energy,'chargingInfo.T': -timestep}}            
                    database_update(i['evse_id'], _updatedStatus)
                    chargingPoolNext.append(i)
                #here we have two situations: for 1: flex_G2 can support flex_demand_2           
                elif flex_demand_2 <= flex_supply_G2:

                    _updatedPower = round((i['CPpower'] - (flex_demand_2/flex_supply_G2) *i['F_p']),1)
                    _flex = round((i['CPpower'] - _updatedPower)*(timestep/60),1)
                    newPowerLevel = {"$set":{"updatedPower":_updatedPower}}
                    database_update(i['evse_id'], newPowerLevel)
                    newFlex = {"$inc":{"chargingInfo.flex_rec":_flex}}
                    database_update(i['evse_id'], newFlex)  
                    
                    ### for simulation
                    _energy = - round(_updatedPower*0.25,1)
                    _updatedStatus = {"$inc":{"chargingInfo.E":_energy,'chargingInfo.T': -timestep}}            
                    database_update(i['evse_id'], _updatedStatus) 
                    chargingPoolNext.append(i)
                    
                #for 2. flex_G2 cannot support flex_demand_2, which is very unlikely to happen.      
                #reduce power for those who don't provide information or other measures
                #reduce the power equally to low flex group (we choose this)
                else:        
                    print('impossible situation')
                    #all flex group power reduce to zero, the unknown group will reduce the power equally. (next step)
             
        
            print('all updated3')
    
    collection.save({'_id':'est_next','charging_profile':chargingPoolNext})



# In[46]:


optimization(powerLimit)





