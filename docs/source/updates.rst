
V0.82
1) PowerDynSimEnvDef (v5) simplifies the environment creation by moving the IpssGateWay setup into env.init() function
2) Create the PowerDynSimEnvDef (v5) test case
3) Update the lib to V0.82
4) Update the IEEE39 Bus test cases to base on PowerDynSimEnvDef (v5)


V0.80
1) updated IpssGateWay, json configuration file definition and PowerDynSimEnvDef (the latest is v4)to support continuous control actions.
2) updated PowerDynSimEnvDef (v4) and test cases to support recent versions of OpenAI Gym and OpenAI Baselines. Our internal test environments are: OpenAI gym (0.15.3) and baselines (0.1.5)


V0.72  updated IpssGateWay, and replace the use of "global" variables for gateway ans ipss_app in python end to address the errors occuring during multi-processing


V0.71  add observation output variable names


V0.70 development for the LDRD project and IEEE TSG paper