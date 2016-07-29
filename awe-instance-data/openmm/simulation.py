#!/usr/bin/env python3

##########################################################################
# this script was generated by openmm-builder. to customize it further,
# you can save the file to disk and edit it with your favorite editor.
##########################################################################

from __future__ import print_function
from simtk.openmm import app
import simtk.openmm as mm
from simtk import unit
from sys import stdout
import numpy as np
import argparse
import mdtraj
import time

np.set_printoptions(threshold=np.nan)

def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--checkpoint",
                        help="path to an OpenMM checkpoint",
                        type=str
                       )
    
    parser.add_argument("-s", "--steps",
                        help="the number of integration steps",
                        type=int,
                        default=10000
                       )
    
    parser.add_argument("-p", "--platform",
                        help="the OpenMM Platform to use in this run",
                        type=str,
                        default="CPU",
                        choices=["Reference", "CPU", "OpenCL", "CUDA"]
                       )

    parser.add_argument("-i", "--input-pdb",
                        help="path to the input trajectory file",
                        type=str,
                        default="structure.pdb"
                       )
                        
    parser.add_argument("-o", "--output",
                        help="path to trajectory output file",
                        type=str,
                        default="structure2.pdb",
                       )
    
    parser.add_argument("-a", "--atom-select",
                        help="MDTraj-compatible atom selection string for computing RMSD",
                        type=str,
                        default="all"
                       )

    parser.add_argument("--cell-defs",
                        help="path to the cell definition file",
                        type=str,
                        default="cells.dat",
                       )
    
    parser.add_argument("--assignment-out",
                        help="path to the file to write the cell assignment",
                        type=str,
                        default="cell2.dat"
                       )

    return parser.parse_args()


def read_cells(infile):
    cells = []
    ncells = 0
    natoms = 0
    ndims = 0
    with open(infile, 'r') as f:
        for line in f:
            try:
                if "ncells:" in line or "ncoords:" in line or "ndims:" in line:
                    entries = line.strip().split()
                    if entries[0] == "ncells:":
                        ncells = int(entries[1])
                    elif entries[0] == "ncoords:":
                        natoms = int(entries[1])
                    else:
                        ndims = int(entries[1])
                else:
                    cells.append(float(line))
            except ValueError:
                continue
    print(ncells, natoms, ndims)
    return np.reshape(np.array(cells), (ncells, natoms, ndims))


def determine_assignment(pdb_file, cell_file, atom_select, assignment_out):
    cells = read_cells(cell_file)
    min_rmsd = float('inf')
    assignment = -1
    traj = mdtraj.load(pdb_file)
    cell_traj = mdtraj.load(pdb_file)
    rmsd_atoms = traj.topology.select(atom_select)
    print(rmsd_atoms)
    for i in range(0, len(cells)):
        cell_traj.xyz = cells[i]
        rmsd = mdtraj.rmsd(traj,
                           cell_traj,
                           atom_indices=rmsd_atoms,
                          )
        print(rmsd)
        if rmsd < min_rmsd:
            min_rmsd = rmsd
            assignment = i
    with open(assignment_out, 'w') as f:
        f.write(str(assignment))
    
        

if  __name__ == "__main__":
    args = parse_args(None)
    print(args) 
    print("Loading pdb...")
    pdb = app.PDBFile(args.input_pdb)
    print(pdb.positions)
    print(len(pdb.positions))
    print("Loading force field...")
    forcefield = app.ForceField('amber99sb.xml', 'amber99_obc.xml')
    
    print("Creating system...")
    system = forcefield.createSystem(pdb.topology, nonbondedMethod=app.NoCutoff,
        constraints=None)
    print("Creating integrator...")
    integrator = mm.LangevinIntegrator(300*unit.kelvin, 1/unit.picoseconds,
        1.0*unit.femtoseconds)
    
    print("Creating platform...")
    try:
        platform = mm.Platform.getPlatformByName(args.platform)
    except Exception:
        print("Error: could not load platform %s. Loading Reference platform" % (args.platform))
        platform = mm.Platform.getPlatformByName("Reference")
    print("Creating simulation object...")
    simulation = app.Simulation(pdb.topology, system, integrator, platform)
    
    simulation.context.setPositions(pdb.positions)
    
    print("Minimizing...")
    #simulation.minimizeEnergy()

    print("Equilibrating...")
    #simulation.step(100)

    print("Creating PDB reporter...")
    simulation.reporters.append(app.PDBReporter(args.output, args.steps))
    
    print("Creating checkpointer...")
    simulation.reporters.append(app.CheckpointReporter("ckpt.chk", 100))

    print('Running Production...')
    #steps = 0
    #interval = 100
    #while steps < args.steps:
    simulation.step(args.steps + 1)
        #steps += interval

    print("Determining cell assignment...")
    
    time.sleep(5)
    determine_assignment(args.output, args.cell_defs, args.atom_select, args.assignment_out)

    print("Done!")