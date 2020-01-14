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
   with the smart charging algorithm running every timestep (15 minutes), there could be the case that several CPs are supposed to alter    their power supply to the chargeing EV. we need both data record and implementation.
5. A smart contract for billing and flexibility token allocation between CPO and users is also necessary. [SC3 for token transfer]
   token transfer is based on two things: the actual electricity consumption for charging, which should be precisely measured by built-    in metering device in the CP, and the total flexibility user contributed during his/her charging process. This will be calculated in    the smart charging algorithm.
  
6. last but not least, the whole smart charging algorithm should be stored to the blockchain so that people can verifiy this (but how?)

 
$$function design for the product$$
our cloud architecture shows that all datas are from CPO's backend and HEMS backend(if PV data is available), therefore it is important to consider which data among all are important for us to record in blockchain. Billing and smart charging are the two major functions to be realized in blockchain ecosystem. Nornally, if to start a charging session, the billing system is done by CPO. We can copy this and make it on-chain. When they want to actively control the charging power, they shoulod also be able to do through CPO's backend. What we want is help them to make such decision by smart charging algorithm with a certain extra input data. 

To sum up, the blockchain is not doing any computationally heavy tasks and only responsible for data recording and billing. That is to say, the smart charging and flexibility calculation are taken placce in off-chain environment. since the smart charging algorithm is written in Python, web3.py is chosen to connect the simulation program and smart contracts.
