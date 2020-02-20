#!/usr/bin/env python
# coding: utf-8

# In[36]:


from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
db = client['cpDB']
collection = db.test1


# In[ ]:





# In[37]:


timestep = 15 # in minutes


# In[38]:


powerLimit = 44
flex_level = 11 # if the flex power of a charging event is greater than 11 kW, it is catigorized to high flex group, otherwise, low flex group


# In[39]:


def database_update(_cpid, changes):
    query = {"evse_id":_cpid}
    collection.update_one(query,changes)
    
    
def optimization(powerLimit): #in real situation, _cpGroup shoud be included
    # get updated status from cpDB
    charging_pool =[]
    totalPowerDemand =0
    flex_supply =0
    flex_supply_G1 =0
    flex_supply_G2 =0
    dbcopy =[]
    num_G2 = 0 #num of events in low flex group
    global timestep
    
    
    #use pymongo to change status of all finished events, think about how to record flexibility?! the values will be deleted once the EV is driven away 
    
    #collection.update_many({'cp_group':'G1','status':'O',"$or":[{'chargingInfo.E':{"$lte":0}},{'chargingInfo.T':0}]},{"$set":{'status': 'Finished','updatedPower': 0, 'chargingInfo.E': None,'chargingInfo.T': None}})
    collection.update_many({'cp_group':'G1','status':'L'},{"$set":{'status': 'Finished','updatedPower': 0}})
    
    #for the last timestep events, change status, update new power
    for i in collection.find({'cp_group':'G1','status':'O','chargingInfo.T':timestep}):
        
        _updatedPower = round(min(i['powerValue'],(4* i['chargingInfo']['E'])),1)
        newPowerLevel = {"$set":{"updatedPower":_updatedPower, 'status':'L'}}
        database_update(i['evse_id'], newPowerLevel) 
        powerLimit -= _updatedPower
        
        ####for simulation
        _energy = - _updatedPower*0.25
        _updatedStatus = {"$inc":{"chargingInfo.E":_energy,'chargingInfo.T': -timestep}}
        database_update(i['evse_id'], _updatedStatus) 
    
    for i in collection.find({'cp_group':'G1','status':'O'},{'_id':0,'evse_id':1, 'powerValue':1,'chargingInfo.user_id':1, 'chargingInfo.E':1,'chargingInfo.T':1}):
        dbcopy.append(i)
        print(i)
    
    for i in dbcopy:
        charging_pool.append({"evse_id":i['evse_id'],"CPpower":i['powerValue'],"userID":i['chargingInfo']['user_id'],"E":i['chargingInfo']['E'],"T":i['chargingInfo']['T']})
        print(charging_pool)
    
    for i in charging_pool:
        i['F_t'] = max(round((i['T'] - (i['E']/i['CPpower'])*60),1),0) ##cannot be negative value!!!, correct it! 
        if (i['F_t']>= timestep):
            i['F_p'] = i['CPpower']
        else:
            i['F_p'] = round((i['F_t'] * i['CPpower']/timestep),1)
        
        # classify into two flex groups
        if (i['F_p']>= flex_level):
            i['flex_priority'] = 1 # highest priority from 1
        else:
            i['flex_priority'] = 2
            #count number of events in low flex group
            num_G2 += 1        

                             
        
        totalPowerDemand += i['CPpower'] ## this is ideal case, in reality, some EV can not charge with full CP power!!!
        
        if (i['flex_priority'] == 1):
            flex_supply_G1 += i['F_p']
        else:
            flex_supply_G2 += i['F_p']
            
        #flex_supply += i['F_p']
        #i['flex_rec']= 0 #flexibility record
    
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
            
        print('all updated1')
        
    else :    
        flex_demand = totalPowerDemand - powerLimit
        '''
        #update db with reduced power proportional to each CP, and add flex_rec to each document 
        for i in charging_pool:
            
            _updatedPower = round((i['CPpower'] - flex_demand/flex_supply *i['F_p']),1)
            _flex = round((i['CPpower'] - _updatedPower)*(timestep/60),1)
            newPowerLevel = {"$set":{"updatedPower":_updatedPower}}
            database_update(i['evse_id'], newPowerLevel)
            newFlex = {"$inc":{"chargingInfo.flex_rec":_flex}}
            database_update(i['evse_id'], newFlex)
            
            ### for simulation
            _energy = - round(_updatedPower*0.25,1)
            _updatedStatus = {"$inc":{"chargingInfo.E":_energy,'chargingInfo.T': -timestep}}            
            database_update(i['evse_id'], _updatedStatus)    
            '''
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
                    
                else:
                    newPowerLevel = {"$set":{"updatedPower":i['CPpower']}}
                    database_update(i['evse_id'], newPowerLevel)
                    
                    ###for simulation
                    _energy = - round(i['CPpower']*0.25,1)
                    _updatedStatus = {"$inc":{"chargingInfo.E":_energy,'chargingInfo.T': -timestep}}            
                    database_update(i['evse_id'], _updatedStatus)  
                    
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
                    
                #for 2. flex_G2 cannot support flex_demand_2, which is very unlikely to happen.      
                #reduce power for those who don't provide information or other measures
                #reduce the power equally to low flex group (we choose this)
                else:        
                    print('impossible situation')
             
        
            print('all updated3')


# In[42]:


for t in range(0,20):
    print("round %d " %t)
    optimization(powerLimit)


# In[46]:


optimization(powerLimit)


# In[1]:


round(8.23445134,1)


# In[ ]:




