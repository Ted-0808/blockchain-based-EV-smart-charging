# blockchain-based-EV-smart-charging
this project is composed of two part: smart contracts to interact with blockchain and smart charging algorithm to better coordinate the EV charging activities for a particular charging station.
the UX should consider both EV customers and CPOs. FOr EV users, they need to be well informed with the battery status of the EV during the charging process (i.e. % SOC or kWh increase) and make sure their charging need can be met. For CPOs, they should be able to see the real time charging status of their charging points (at which power level the CP is charging the EV, compared with the rated power) it can be a cockpit dashboard.
the smart charging algorithm has three inputs: charging time, energy (electricity needed) and the threshold of power supply to the charging station. the first two inputs are indicated by EV users and the third one by the CPO. 


$$steps to formulate a concrete work plan$$
1. go through the site map and identify (mark) all CPs and PV inverters
2. to know which CP(s) should be grouped together (for those who share a same power distribution cabinet) and if any PV should also be        considered as an extra power source. Please also be aware of whether the CPs are also share the load with other equipmets!! 
   now we can turn the big problem into many subproblems. now only to focus the CPs of the same group when do the EV charging                coordination.In smart charging system, it should be able to identiy which CPs are in the same group in order to performing the charging    optimization.
3. all CPs and PV facilities as assets should be registered in the smart contract. [SC1 for asset registration] 
   information to be included in the registration smart contract:
   CP: id, ald, longtd,status, rated power, real time power, price, etc.
   PV (inverter):
   Battery: capacity, electricity available, etc.
4. there will be another smart contract to allow status update for all assets. [SC2 for asset's status update]
   

 
