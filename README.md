# blockchain-based-EV-smart-charging

The highlights of this project are: implementing smart charging algorithm to better coordinate the EV charging activities for a particular charging station as well as using blockchain platform to document and reward the EV user with tokens for the flexibility contribution. 

The UX matters and should consider thoroghly. EV users are given the choices of if they want to join the smart charging scheme. meanwhile, they need to be well informed with the battery status of the EV during the charging process (i.e. % SOC or kWh increase) through the charging App. For those who participate the smart charging algorithm, if their charging requests are accepted, the system have to make sure their charging need can be met by the time of departure. For CPOs, they should be able to see the real time charging status of their charging points (at which power level the CP is charging the EV, compared with the rated power). This can be well presented through a cockpit dashboard.

The smart charging algorithm has three inputs: charging time, energy (electricity needed) and the total power capacity of the charging station. the first two inputs are indicated by EV users and the third one by the CPO. 


$$steps to formulate a concrete work plan$$

1. go through the site map and identify (mark) all CPs and PV inverters (if available)

2. to know which CP(s) should be grouped together (for those who share a same power distribution cabinet) and if any PV should also be considered as an extra power source. Please also be aware of whether the CPs are also share the load with other equipmets!! The smart charging algorithm running independly within each charging group.

3. draw a project architecture and user story mapping (sequence diagram)

4. discussion with developers and technicians and identify the difficulties and obstacles 

5. come up with alternatives until no technical related issues

6. start implementation and constant test and feedback.

$$porject architecture$$

![project_architecture](https://user-images.githubusercontent.com/48090782/73442829-d13df080-4355-11ea-9c9f-13e3ae5118bf.png)

A Oli Move backend server is proposed to receive data from CPO's backend and process user registration and charging requests. It sends the necessary data to the blockchain. There are four conponents: a database to store all CPs information which are required for running smart charging algorithm; the smart charging algorithm; an eWallet to manage EV users' blockchain account; and a Ethereum client for interacting with the Blockchain.

3. all CPs and PV facilities are regarded as assets so that they should be registered in the smart contract. [SC1 for asset registration] 
   information to be included in the registration smart contract:
   CP_id (for oli move backend);
   evseID (from CPO backend);
   powerValue (from CPO backend);
   energy (from CPO backend);
   powerInfo (from CPO backend);
   connectionType (from CPO backend);
   status (from CPO backend);
   cp_group (for oli move backend);
   userEnergyLeft (for oli move backend);
   userTimeLeft (for oli move backend);
   
   PV (inverter):
   Battery: capacity, electricity available, etc.
   
4. there will be another smart contract to allow status update for all assets. [SC2 for asset's status update]
   with the smart charging algorithm running every timestep (15 minutes), there could be the case that several CPs are supposed to alter    their power supply to the chargeing EV. we need both data record and implementation.
5. A smart contract for billing and flexibility token allocation between CPO and users is also necessary. [SC3 for token transfer]
   token transfer is based on two things: the actual electricity consumption for charging, which should be precisely measured by built-    in metering device in the CP, and the total flexibility user contributed during his/her charging process. This will be calculated in    the smart charging algorithm.
  
6. last but not least, the whole smart charging algorithm should be stored to the blockchain so that people can verifiy this (but how?)

 
$$function design for the product$$

Our cloud architecture shows that all CP data are acquired from CPO's backend and HEMS backend(if PV data is available), therefore it is important to consider which data are important for smart charging algorithm and which are for blockchain. Billing and smart charging are the two major functions to be realized in blockchain ecosystem. Nornally, if to start a charging session, the billing system is done by CPO. We can copy this and make it on-chain. When they want to actively control the charging power, they shoulod also be able to do through CPO's backend. What we want is help them to make such decision by smart charging algorithm with a certain extra input data. 

To sum up, the blockchain is not doing any computationally heavy tasks and only responsible for data recording and billing. That is to say, the smart charging and flexibility calculation are taken placce in off-chain environment. since the smart charging algorithm is written in Python, web3.py is chosen to connect the simulation program and smart contracts.
