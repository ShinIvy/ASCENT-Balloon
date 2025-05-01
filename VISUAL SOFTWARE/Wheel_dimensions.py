#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 28 14:54:30 2024

@author: laravincent
"""

import numpy as np

Rext = np.linspace(2,3.7,90) #Rayon extérieur en cm
Rint = np.linspace(1.7,3.4,90) #Rayon intérieur a 4mm de moins que Rext (en cm)
h = np.linspace(2,3,20) #hauteur en cm
h_base = np.linspace(0.1,2.2,30)
#masse_wheel = np.linspace(10,150,140)

rho = 1.28 #g/cm^3
#masse_wheel = 90
#masse_base = 20

ok_Rext = []
ok_Rint = []
ok_h = []
ok_masse = []
ok_masse_base = []
ok_h_base = []
I_wheel = []
ok_masse_tot = []
ok_h_tot = []
k = 0


for i in range(int(len(Rext))) :
    for j in range(int(len(h))) :
        for d in range(int(len(h_base))) :
            for f in range(int(len(Rint))) :
                if Rint[f] < Rext[i]:
                    masse_wheel = rho * np.pi * h[j] * (Rext[i]**2 - Rint[f]**2)
                    masse_base = rho * np.pi * h_base[d] * (Rext[i]**2)
                    masse_totale = masse_base + masse_wheel
                    I_cylindre_creux = (1/2) * masse_wheel * (Rext[i]**2 + Rint[f]**2)
                    I_cylindre_plein = (1/2) * masse_base * Rext[i]**2
                    I_wheel = I_cylindre_creux + I_cylindre_plein
                    h_tot = h[j] + h_base[d]

                    if I_wheel <= 2000 and I_wheel >= 1100 and masse_totale <= 125 and h_tot <= 4:
                        ok_Rext.append(Rext[i])
                        ok_Rint.append(Rint[f])
                        ok_h.append(h[j])
                        ok_h_base.append(h_base[d])
                        ok_masse.append(masse_wheel)
                        ok_masse_base.append(masse_base)
                        ok_masse_tot.append(masse_totale)
                        ok_h_tot.append(h_tot)
                        #print(I_wheel)


for k in range(int(len(ok_Rext))):
    if ok_masse_tot[k] == min(ok_masse_tot):
        masse_finale = ok_masse_tot[k]
        indice = k
    print('R_ext =',f"{ok_Rext[k]:.2f}",'; R_int =',f"{ok_Rint[k]:.2f}",'; h =',f"{ok_h[k]:.2f}",'; masse roue =',f"{ok_masse[k]:.2f}")
    print('h base =',f"{ok_h_base[k]:.2f}",'; masse base =',f"{ok_masse_base[k]:.2f}")
    print('Masse totale :', f"{ok_masse_tot[k]:.2f}", '; h totale :', f"{ok_h_tot[k]:.2f}")
    print('\n')


print('Final : Masse =', masse_finale,' ; R_ext =', ok_Rext[indice], ' ; R_int =', ok_Rint[indice], ' ; hauteur =', ok_h_tot[indice], ' ; H base =', ok_h_base[indice], ' ; H roue =', ok_h[indice])

'''   
torque = 4e5


for I_wheel in range(1100,1400,10) :
    acc_ang = torque/I_wheel
    print(acc_ang)
'''
    
    