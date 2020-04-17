#!/bin/sh
MERLIN_INFO=$1
CONTAINER=$2
SCRIPTS=$3

FOAM_INPUT=/opt/openfoam6/tutorials/incompressible/icoFoam/cavity/cavity

# Set up the cavity directory in the MERLIN_INFO directory
echo "***** Copy the Deck from the Singularity Image *****"
singularity exec ${CONTAINER} cp -r ${FOAM_INPUT} ${MERLIN_INFO}

cd ${MERLIN_INFO}/cavity

echo "***** Setting Up Mesh *****"
python ${MERLIN_INFO}/scripts/mesh_param_script.py -scripts_dir ${MERLIN_INFO}/scripts/
mv blockMeshDict.txt system/blockMeshDict

echo "***** Setting Control Dictionary *****"
# Use a json encoded dict to tset the new values in the OpenFOAM file
python ${MERLIN_INFO}/scripts/ofoam_replace.py -f system/controlDict -j '{"writeControl":"runTime","endTime":1,"writeInterval":0.1}'
