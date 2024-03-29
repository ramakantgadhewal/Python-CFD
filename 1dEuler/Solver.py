from __future__ import annotations

import math

from ModelBase import SolverBase
from PhysicalProperty import *


class RiemannRoe(SolverBase):
    def __init__(self, rho:Rho, rhoU:RhoU, rhoE:RhoE, p:P, epsilon:float=0.15):
        if type(epsilon) is not float:
            raise TypeError
        if not (type(rho) is Rho and type(rhoU) is RhoU and type(rhoE) is RhoE and type(p) is P):
            raise TypeError
        
        self.rho = rho
        self.rhoU = rhoU
        self.rhoE = rhoE
        self.p = p
        self.epsilon = epsilon
        
    def __call__(self) -> None:
        for i in range(1, len(self.rho.value)):
            # プリミティブ変数の算出
            rhoR = self.rho.rightBoundaryValue[i]
            rhoL = self.rho.leftBoundaryValue[i]
            uL = self.rhoU.leftBoundaryValue[i] / self.rho.leftBoundaryValue[i]
            uR = self.rhoU.rightBoundaryValue[i] / self.rho.rightBoundaryValue[i]
            pL = self.p(self.rho.leftBoundaryValue[i], self.rhoU.leftBoundaryValue[i], self.rhoE.leftBoundaryValue[i])
            pR = self.p(self.rho.rightBoundaryValue[i], self.rhoU.rightBoundaryValue[i], self.rhoE.rightBoundaryValue[i])
            hL = (self.rhoE.leftBoundaryValue[i] + pL) / self.rho.leftBoundaryValue[i]
            hR = (self.rhoE.rightBoundaryValue[i] + pR) / self.rho.rightBoundaryValue[i]
            eL = self.rhoE.leftBoundaryValue[i] / self.rho.leftBoundaryValue[i]
            eR = self.rhoE.rightBoundaryValue[i] / self.rho.rightBoundaryValue[i]
                        
            # Roe平均の算出
            rhoAve = math.sqrt(rhoL * rhoR)
            uAve = (uL * math.sqrt(rhoL) + uR * math.sqrt(rhoR)) / (math.sqrt(rhoL) + math.sqrt(rhoR))
            hAve = (hL * math.sqrt(rhoL) + hR * math.sqrt(rhoR)) / (math.sqrt(rhoL) + math.sqrt(rhoR))
            cAve = math.sqrt((self.p.gamma - 1)*(hAve - uAve**2/2))
            
            # 特性速度の算出
            lambda1 = Harten(uAve, self.epsilon)
            lambda2 = Harten(uAve + cAve, self.epsilon)
            lambda3 = Harten(uAve - cAve, self.epsilon)
            
            # 数値流束の算出
            dw1 = rhoR - rhoL - (pR - pL)/cAve**2
            dw2 = uR - uL + (pR - pL) / (rhoAve*cAve)
            dw3 = uR - uL - (pR - pL) / (rhoAve*cAve)
            
            self.rho.f[i] = .5 * (self.rho.F(rhoR*uR) + self.rho.F(rhoL*uL)) \
                - .5 * (lambda1*dw1 + lambda2*rhoAve/(2*cAve)*dw2 - lambda3*rhoAve/(2*cAve)*dw3)
            self.rhoU.f[i] = .5 * (self.rhoU.F(rhoR, rhoR*uR, pR) + self.rhoU.F(rhoL, rhoL*uL, pL)) \
                - .5 * (lambda1*dw1*uAve + lambda2*rhoAve/(2*cAve)*dw2*(uAve+cAve) - lambda3*rhoAve/(2*cAve)*dw3*(uAve-cAve))
            self.rhoE.f[i] = .5 * (self.rhoE.F(rhoR, rhoR*uR, rhoR*eR, pR) + self.rhoE.F(rhoL, rhoL*uL, rhoL*eL, pL)) \
                - .5 * (lambda1*dw1*(uAve**2/2) + lambda2*rhoAve/(2*cAve)*dw2*(hAve+cAve*uAve) - lambda3*rhoAve/(2*cAve)*dw3*(hAve-cAve*uAve))

        # 境界条件
        self.rho.f[0] = self.rho.f[1]
        self.rhoU.f[0] = self.rhoU.f[1]
        self.rhoE.f[0] = self.rhoE.f[1]
        
        self.rho.f[-1] = self.rho.f[-2]
        self.rhoU.f[-1] = self.rhoU.f[-2]
        self.rhoE.f[-1] = self.rhoE.f[-2]
        

def Harten(alpha:float, epsilon:float) -> float:
    if abs(alpha) < 2*epsilon:
        return alpha**2 / (4 * epsilon) + epsilon       
    else:
        return abs(alpha)