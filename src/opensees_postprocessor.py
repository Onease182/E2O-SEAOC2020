'''
    MIT License
    
    Copyright (c) 2020 OpenSeesPro
    
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

    Developed by:
        Ayush Singhania (ayushs@stanford.edu)
        Pearl Ranchal (ranchal@berkeley.edu)
      
    Publication:
        Goings, C. B., Singhania, A., Ranchal, P., Weaver B., 2020, “Industrial 
        Scale NLRH Analysis Using OpenSees and Comparison with Perform3D,” 
        Proceedings of 2020 SEAOC Virtual Convention, SEAOC, CA
    
    Description of the script - 
        This is a supporting script for the main.py (user should execute main.py)
        This script is used to post-process the data generated through analyses
        in OpenSees.

'''

import os
import glob
import numpy as np 
import pandas as pd

COLS = ['FX', 'FY', 'FZ', 'MX', 'MY', 'MZ']
COL_DICT = {i:col for i, col in zip(range(6), COLS)}

def post_process(initialOrTangent, dir_):
    # Plot the moment-rotation hysteresis of the first hinge element whose
    # recorder actually produced data. The previous version hardcoded element
    # 20279 from the SEAOC benchmark; models without that hinge produced empty
    # .out files and crashed reading column 0. We now scan for whichever hinge
    # files exist and skip gracefully when the model has no nonlinear hinges.
    for fpath in sorted(glob.glob(os.path.join(dir_, f'ele_frc_*_{initialOrTangent}.out'))):
        ele_tag = os.path.basename(fpath).split('_')[2]
        fpath2 = os.path.join(dir_, f'ele_def_{ele_tag}_{initialOrTangent}.out')
        if not os.path.exists(fpath2):
            continue

        frc_rows = [s.split() for s in open(fpath, 'r').readlines() if s.strip()]
        def_rows = [s.split() for s in open(fpath2, 'r').readlines() if s.strip()]
        if not frc_rows or not def_rows:
            continue

        df = pd.DataFrame(frc_rows)
        df['RY'] = pd.DataFrame(def_rows)[0]
        df = df.astype(float).rename(columns=COL_DICT)

        ax = df.plot(x='RY', y='MY', grid=True, figsize=(15,5))
        ax.set_axisbelow(True)

        df.to_excel(os.path.join(dir_, f'hinge_hyst-{initialOrTangent}.xlsx'))
        return df.copy()

    print('post_process: no hinge element recorders with data were found '
          f'in {dir_}; skipping the hysteresis plot.')
    return None

def base_shear(dir_, dict_of_rxn_nodes, initialOrTangent):
    df_shear_x = pd.DataFrame(columns = [])
    df_shear_x['t'] = np.arange(0,50.01,0.01)
    df_shear_y = df_shear_x.copy()
    
    for rxn_node in dict_of_rxn_nodes:
        fpath = os.path.join(dir_, 'node_' + str(rxn_node) + '_rxn_' + initialOrTangent + '.out')
        df = pd.DataFrame([s.split() for s in open(fpath, 'r').readlines()])
        df = df.astype(float).rename(columns=COL_DICT)
        
        df_shear_x[f'X - {rxn_node}'] = df.FX
        df_shear_y[f'Y - {rxn_node}'] = df.FY
        
    df_shear_x['Vx'] = df_shear_x.sum(axis = 1)
    df_shear_y['Vy'] = df_shear_y.sum(axis = 1)
    
    df_shear_x.to_excel(os.path.join(dir_, f'base shear x-{initialOrTangent}.xlsx'))
    df_shear_y.to_excel(os.path.join(dir_, f'base shear y-{initialOrTangent}.xlsx'))
    
    return

# LOAD PER-NODE DISPLACEMENT RECORDERS (node_<tag>_disp_<case>.out, 6 cols).
def _load_node_disp(dir_, initialOrTangent):
    node_disp = {}
    nsteps = None
    for fpath in sorted(glob.glob(os.path.join(dir_, f'node_*_disp_{initialOrTangent}.out'))):
        tag = int(os.path.basename(fpath).split('_')[1])
        arr = np.loadtxt(fpath)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.shape[1] < 3:
            continue
        arr = arr[:, :3]
        nsteps = arr.shape[0] if nsteps is None else min(nsteps, arr.shape[0])
        node_disp[tag] = arr
    for tag in list(node_disp):
        node_disp[tag] = node_disp[tag][:nsteps]
    return node_disp, (nsteps or 0)

def _load_geometry(dir_):
    import pickle
    path = os.path.join(dir_, 'model_geometry.pkl')
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return pickle.load(f)

# PLOT ROOF DISPLACEMENT AND BASE SHEAR TIME HISTORIES, AND THE INTERSTORY
# DRIFT ENVELOPE, FROM THE RECORDED OUTPUTS. Pure matplotlib; saves PNGs.
def plot_response_histories(dir_, dict_of_rxn_nodes, initialOrTangent, dt=0.01):
    import matplotlib
    import matplotlib.pyplot as plt

    node_disp, nsteps = _load_node_disp(dir_, initialOrTangent)
    geom = _load_geometry(dir_)
    if not node_disp or geom is None:
        print('plot_response_histories: missing displacement recorders or geometry '
              f'snapshot in {dir_}; skipping response-history plots.')
        return None
    node_coords = geom['node_coords']
    t = np.arange(nsteps) * dt

    # roof = recorded node at the highest elevation
    roof_tag = max(node_disp, key=lambda tg: node_coords[tg][2])
    roof = node_disp[roof_tag]

    fig, axes = plt.subplots(1, 2, figsize=(15, 5), sharex=True)
    axes[0].plot(t, roof[:, 0], lw=1.0, color='tab:blue')
    axes[0].set_title(f'Roof displacement X (node {roof_tag})')
    axes[0].set_xlabel('time [s]'); axes[0].set_ylabel('disp [in]'); axes[0].grid(True)
    axes[1].plot(t, roof[:, 1], lw=1.0, color='tab:red')
    axes[1].set_title(f'Roof displacement Y (node {roof_tag})')
    axes[1].set_xlabel('time [s]'); axes[1].set_ylabel('disp [in]'); axes[1].grid(True)
    fig.tight_layout()
    roof_png = os.path.join(dir_, f'roof_displacement-{initialOrTangent}.png')
    fig.savefig(roof_png, dpi=150); plt.close(fig)

    # base shear = sum of recorded reactions
    vx = np.zeros(nsteps); vy = np.zeros(nsteps)
    for rxn_node in dict_of_rxn_nodes:
        fpath = os.path.join(dir_, f'node_{rxn_node}_rxn_{initialOrTangent}.out')
        if not os.path.exists(fpath):
            continue
        arr = np.loadtxt(fpath)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        n = min(nsteps, arr.shape[0])
        vx[:n] += arr[:n, 0]; vy[:n] += arr[:n, 1]

    fig, axes = plt.subplots(1, 2, figsize=(15, 5), sharex=True)
    axes[0].plot(t, vx, lw=1.0, color='tab:blue')
    axes[0].set_title('Base shear Vx'); axes[0].set_xlabel('time [s]')
    axes[0].set_ylabel('force [kip]'); axes[0].grid(True)
    axes[1].plot(t, vy, lw=1.0, color='tab:red')
    axes[1].set_title('Base shear Vy'); axes[1].set_xlabel('time [s]')
    axes[1].set_ylabel('force [kip]'); axes[1].grid(True)
    fig.tight_layout()
    bs_png = os.path.join(dir_, f'base_shear-{initialOrTangent}.png')
    fig.savefig(bs_png, dpi=150); plt.close(fig)

    # interstory drift envelope: group recorded nodes by elevation (diaphragm levels)
    levels = {}
    for tag in node_disp:
        levels.setdefault(round(node_coords[tag][2], 3), []).append(tag)
    zs = sorted(levels)
    drift_x = []; drift_y = []; heights = []
    prev_z, prev_ux, prev_uy = 0.0, np.zeros(nsteps), np.zeros(nsteps)
    for z in zs:
        tags = levels[z]
        ux = np.mean([node_disp[tg][:, 0] for tg in tags], axis=0)
        uy = np.mean([node_disp[tg][:, 1] for tg in tags], axis=0)
        dh = z - prev_z
        if dh > 1e-9:
            drift_x.append(float(np.max(np.abs(ux - prev_ux)) / dh))
            drift_y.append(float(np.max(np.abs(uy - prev_uy)) / dh))
            heights.append(z)
        prev_z, prev_ux, prev_uy = z, ux, uy

    fig, ax = plt.subplots(figsize=(6, 7))
    ax.plot(np.array(drift_x), heights, '-o', label='X direction', color='tab:blue')
    ax.plot(np.array(drift_y), heights, '-o', label='Y direction', color='tab:red')
    ax.set_xlabel('peak interstory drift ratio'); ax.set_ylabel('elevation [in]')
    ax.set_title('Interstory drift envelope'); ax.grid(True); ax.legend()
    fig.tight_layout()
    dr_png = os.path.join(dir_, f'interstory_drift-{initialOrTangent}.png')
    fig.savefig(dr_png, dpi=150); plt.close(fig)

    print(f'Saved response-history plots: {os.path.basename(roof_png)}, '
          f'{os.path.basename(bs_png)}, {os.path.basename(dr_png)}')
    return {'roof_png': roof_png, 'base_shear_png': bs_png, 'drift_png': dr_png,
            'drift_x': drift_x, 'drift_y': drift_y, 'heights': heights}
        