# MyPyPSA-Ger
![1-s2 0-S0306261922000587-gr8_lrg](https://user-images.githubusercontent.com/60949903/179805438-f593a866-a2a9-4bd9-b0a4-33075f7bd344.jpg)


MyPyPSA-Ger, a myopic optimization model developed to represent the German energy system with a detailed mapping of the electricity sector, on a highly disaggregated level, spatially and temporally, with regional differences and investment limitations.

MyPyPSA-Ger was developed by [Anas Abuzayed] (https://de.linkedin.com/in/anas-abuzayed-5b991aa7), at [EEW group](https://ines.hs-offenburg.de/forschung/energiesysteme-und-energiewirtschaft) at [Hochschule Offenburg](https://www.hs-offenburg.de/) . MyPyPSA-Ger model is built using the Modeling Framework [PyPSA](https://github.com/PyPSA/pypsa), with the main network being implemented from [PyPSA-Eur](https://github.com/PyPSA/pypsa-eur).

The model is described in the paper [MyPyPSA-Ger: Introducing CO2 taxes on a multi-regional myopic roadmap of the German electricity system towards achieving the 1.5 °C target by 2050](https://www.sciencedirect.com/science/article/pii/S0306261922000587), and has been used in several other publications. A YouTube course explaining basics of energy system analysis in Python is available [here] (https://www.youtube.com/playlist?list=PLa98mykrHEG8MlH5hCSlB_Dpaje_m5wSY). The course material will be made publicly available soon.

## The German Heating Sector for residential and industrial heating is added by Ali Hassan as his master's thesis unders the supervision of [Anna Sandhaas] (https://github.com/asandhaa) and Prof. Niklas Hartmann (niklas.hartmann@hs-offenburg.de , Hochschule Offenburg).




# Installation 

## Clone the Repository 
## Install the Library
% cd MyPyPSA-Ger

% conda create --name MyPyPSA-Ger --file req.txt

## The results of this model will be saved in a folder within the main repository following the length of its clusters.

## The model accepts clusters that represent the NUTS statistical regions of Germany. 4 Clusters is the default, with 12 GW/cluster as a default regional potential. The values could be adapted from the config file.


## Many thanks for [Hamza Abo Alrob] (https://github.com/haboalr) for his help on splitting the model and the functions description and for [Anna Sandhaas] (https://github.com/asandhaa) Omar Elaskalani, and Martin Thomas for their help on the NUTS clustering of the model.
