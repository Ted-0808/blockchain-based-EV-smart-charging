# -*- coding: utf-8 -*-
"""
Created on Mon Feb 10 14:32:36 2020

@author: zeguang.li
"""
from datetime import datetime
from pymongo import MongoClient
from copy import deepcopy
client = MongoClient('mongodb://localhost:27017/')
db = client['cpDB']
collection = db.test1

charging_ticket = dict()
a = False #token flag to indicate if the charging request is accepted or not
PowerLimit = 44
timestep = 15
flex_level = 11 #

def database_update(_cpid, changes):
    query = {"evse_id":_cpid}
    collection.update_one(query,changes)

def generate_charging_request():
 
    userId = input('your user id:(e.g. user003) ')
    cpId = input('which cp to charge: (e.g. evse007) ')
    energyAmount = float(input('how much kWh you need?'))
    timeAvailable = 60* float(input('time availability before departure? (h)'))
    charging_ticket['evse_id'] = cpId
    charging_ticket['userID'] = userId
    charging_ticket['E'] = energyAmount
    charging_ticket['E_rec'] = energyAmount
    charging_ticket['T'] = timeAvailable
    charging_ticket['chargingEnd'] = 0 # 0: charging start/on going; 1: charigng end/ finished
    charging_ticket['gen_time'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    return charging_ticket

def fulfillment_check(charging_ticket):
    charging_ticket2 = deepcopy(charging_ticket) 
    chargingForm = []
    global timestep
    global PowerLimit
    # whether cp is available
    if collection.count_documents({'evse_id':charging_ticket['evse_id']}) == 0:
        print('no such CP')
        return False
    elif collection.count_documents({'evse_id':charging_ticket['evse_id'],'status':'A'}) == 0:
        print('CP is not available')
        return False
    else:
        print('request will be evaluated')
        #get the charging group, and powerValue of the CP
        cpGroup = collection.find_one({'evse_id':charging_ticket['evse_id']},{'_id':0, 'cp_group':1})
        x = cpGroup.get("cp_group",0) # x specif the charging group
        powerCP = collection.find_one({'evse_id':charging_ticket['evse_id']},{'_id':0, 'powerValue':1}).get("powerValue",0)
        print('this CP is in ',x)
        print('this CP with rated power of ',powerCP, 'kW')
        #add more info to charging_ticket
        charging_ticket['F_t'] = (charging_ticket['T'] - charging_ticket['E']/ powerCP *60)
        charging_ticket['F_p'] = powerCP if charging_ticket['F_t']>=15 else (charging_ticket['F_t']*powerCP/15)
        charging_ticket['CPpower'] = powerCP
    ##smart charging should come in here!
    #get est charging result of current timestep
    chargingForm = collection.find_one({'_id':'est_next'},{'_id':0,'charging_profile':1}).get('charging_profile')
    chargingForm.append(charging_ticket)
    #return chargingForm
    
    while True:
        powerLimit = PowerLimit
        totalPowerDemand = 0
        flex_supply_G1 = 0 
        flex_supply_G2 = 0
        num_G2 = 0

        i = 0
            #before the simulation, delete the finished events from the pool
        while (i<len(chargingForm)): 
            if chargingForm[i]["T"] == 0 or chargingForm[i]["E"] <= 0:
                chargingForm[i]["End"] =1
                print("simulation: %s Charging finished" % chargingForm[i]["evse_id"])
                chargingForm.pop(i)            
                i-=1

            print("simulation: %s Charging checked" % chargingForm[i]["evse_id"])
            i+=1


        for i in chargingForm:

            # for the last timestep case
            if i['T']== timestep:
                powerLimit -= round(min(i['CPpower'],(4* i['E'])),1)        
                i['last_step']= True # creat new field indicating last timestep charging
                i['T'] -= timestep # time field become 0, in next simulation it will be pop out

            #all other charging events will be evaluated
            else:
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

        if totalPowerDemand <= powerLimit:
            #no grid congestion, accept the charging request
            a = True
            print('charging request accepted')
            break
            #update the db

        else:
            flex_demand = totalPowerDemand - powerLimit

            if flex_demand > (flex_supply_G1 + flex_supply_G2):
                a = False
                print('charging request rejected')  
                break

            elif flex_demand <= flex_supply_G1: # high flex group cover the extra demand
                for i in chargingForm:
                    if i['T'] == 0:  #last time step donn't consider
                         pass 
                    elif (i['flex_priority'] == 1):  
                        _updatedPower = round((i['CPpower'] - (flex_demand/flex_supply_G1) *i['F_p']),1)
                        i['E'] -=  round(_updatedPower*0.25,1)
                        i['T'] -= timestep
                    else:
                        i['E'] -=  round(i['CPpower']*0.25,1)
                        i['T'] -= timestep  
                    print("%s values updated" % i["evse_id"] )
            else: # high flex group all reduced to zero, low flex group reduce proportionally
                flex_demand_2 = flex_demand - flex_supply_G1

                for i in chargingForm:
                    if i['T'] == 0:  #last time step donn't consider
                         pass 
                    elif (i['flex_priority'] == 1):  # no E reduction for high flex group
                        #_updatedPower = round((i['CPpower'] - (flex_demand/flex_supply_G1) *i['F_p']),1)
                        #i['E'] -=  round(_updatedPower*0.25,1) 
                        i['T'] -= timestep
                    else: 
                        _updatedPower = round((i['CPpower'] - (flex_demand_2/flex_supply_G2) *i['F_p']),1)
                        i['E'] -=  round(_updatedPower*0.25,1)
                        i['T'] -= timestep  
                    print("%s values updated" % i["evse_id"] )
    
    if a:
        
        newevent = {"$set":{"status":'O',
                             "chargingInfo.user_id":charging_ticket2['userID'],
                             "chargingInfo.E":charging_ticket2['E'],
                             "chargingInfo.T":charging_ticket2['T']}}
        database_update(charging_ticket['evse_id'], newevent) 
        
        
        




def charging_request_result():
    if a:
        chargingInfo_update(charging_ticket)
        print('charging accepted')
    else:
        print('charging rejected')

if __name__ == '__main__':
    generate_charging_request()
    fulfillment_check(charging_ticket)
    charging_request_result()
