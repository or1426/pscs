from __future__ import annotations
import numpy as np
from dataclasses import dataclass
import util

@dataclass
class CHState:
    N : int # number of qubits
    A : np.ndarray # NxN matrix of bytes (we are using as bits) partly determines U_C
    B : np.ndarray # NxN matrix of bytes (we are using as bits) partly determines U_C
    C : np.ndarray # NxN matrix of bytes (we are using as bits) partly determines U_C
    g : np.ndarray # gamma is in (Z / Z^4)^N
    v : np.ndarray # array of N bytes (which we are using as bits) determining U_H 
    s : np.ndarray #array of N bytes (which we are using as bits) - the initial state 
    phase : complex #initial phase

    @classmethod
    def basis(cls, N:int = None, s=None) -> CHState:
        """
        Return a computational basis state defined by the bitstring s
        """
        if N == None and s is None:
            #given no input we assume a single qubit in state |0>
            return cls(N=1,
                       A=np.eye(1, dtype=np.uint8),
                       B=np.eye(1, dtype=np.uint8),
                       C=np.zeros((1,1), dtype=np.uint8),
                       g=np.zeros(1, dtype=np.uint8),
                       v=np.zeros(1, dtype=np.uint8),
                       s=np.zeros(1, dtype=np.uint8),
                       phase = complex(1,0)
            )
        elif N != None and s is None:
            #we get given a number of qubits but no other information so return the state |0,0....0>
            return cls(N=N,
                       A=np.eye(N, dtype=np.uint8),
                       B=np.eye(N, dtype=np.uint8),
                       C=np.zeros((N,N), dtype=np.uint8),
                       g=np.zeros(N, dtype=np.uint8),
                       v=np.zeros(N, dtype=np.uint8),
                       s=np.zeros(N, dtype=np.uint8),
                       phase = complex(1,0)
            )
        elif N == None and not s is None:
            #we get given some bitstring so we return that computational basis state
            N = len(s)
            s = np.array(s, dtype=np.uint8) #we accept lists etc, but convert them to np arrays
            return cls(N=N,
                       A=np.eye(N, dtype=np.uint8),
                       B=np.eye(N, dtype=np.uint8),
                       C=np.zeros((N,N), dtype=np.uint8),
                       g=np.zeros(N, dtype=np.uint8),
                       v=np.zeros(N, dtype=np.uint8),
                       s=s,
                       phase = complex(1,0)
            )
        else:
            #both N and s are not none
            # if N <= len(s) we truncate s to length s and proceed as before
            # if N > len(s) we extend s by adding zeros at the end and proceed as before
            s = np.array(s, dtype=np.uint8)
            if N <= len(s):
                return CHState.basis(N=None, s = s[:N])
            else:
                return CHState.basis(N=None, s = np.concatenate((s, np.zeros(N-len(s), dtype=np.uint8))))  

    @property
    def F(self):
        return self.A
    @F.setter
    def F(self, mat):
        self.A = mat
    @property
    def G(self):
        return self.B
    @G.setter
    def G(self, mat):
        self.B = mat
    @property
    def M(self):
        return self.C
    @M.setter
    def M(self, mat):
        self.C = mat
    @property
    def gamma(self):
        return self.g
    @gamma.setter
    def gamma(self, mat):
        self.g = mat
    @property
    def w(self):
        return self.phase
    @w.setter
    def w(self, c):
        self.phase = c

    def __or__(self, other : CliffordGate):
        return other.applyCH(self)

    def _rowToStr(row):
        return "".join(map(str,row))

    def tab(self):
        """
        pretty "to string" method for small qubit numbers
        prints blocks F G M gamma v s
        with headings to indicate which is which
        """
        
        s  = str(self.N) + " "
        qubitNumberStrLen = len(s)
        matrix_width = self.N
        half_matrix_width = self.N//2
        s = "N" + " "*(qubitNumberStrLen -1 + half_matrix_width) + "F" + " "*matrix_width + "G" + " "*matrix_width + "M" + " "*(matrix_width-half_matrix_width) + "g v s w\n" + s
        
        for i, (Fr, Gr, Mr, gr, vr, sr) in enumerate(zip(self.F, self.G, self.M, self.g, self.v, self.s)):
            if i != 0:
                s += " "*qubitNumberStrLen
            s += CHState._rowToStr(Fr) + " " + CHState._rowToStr(Gr) + " " + CHState._rowToStr(Mr) + " " + str(gr) + " " + str(vr) + " " + str(sr)

            if i == 0:
                s += " " + str(self.phase)
            s += "\n"
        return s

        
    def __str__(self):
        """
        pretty "to string" method for small qubit numbers
        prints blocks F G M gamma v s
        """
        qubitNumberStrLen = None
        s = ""
        
        for i, (Fr, Gr, Mr, gr, vr, sr) in enumerate(zip(self.F, self.G, self.M, self.g, self.v, self.s)):
            if i == 0:
                s = str(self.N) + " "
                qubitNumberStrLen = len(s)
            if i != 0:
                s += " "*qubitNumberStrLen
            s += CHState._rowToStr(Fr) + " " + CHState._rowToStr(Gr) + " " + CHState._rowToStr(Mr) + " " + str(gr) + " " + str(vr) + " " + str(sr)

            if i == 0:
                s += " " + str(self.phase)
            s += "\n"
        return s

    def delete_qubit(self, k):
        mask = np.ones(self.N,dtype=bool)
        mask[k] = False
        mask2d = np.outer(mask,mask)
        
        return CHState(self.N-1, self.A[mask2d].reshape(self.N-1, self.N-1), self.B[mask2d].reshape(self.N-1, self.N-1), self.C[mask2d].reshape(self.N-1, self.N-1), self.g[mask], self.v[mask],self.s[mask], self.phase)
        


    def __sub__(self,other):
        return CHState(self.N,
                         (self.A - other.A)%np.uint8(2),
                         (self.B - other.B)%np.uint8(2),
                         (self.C - other.C)%np.uint8(2),
                         (self.g - other.g)%np.uint8(4),
                         (self.v - other.v)%np.uint8(2),
                         (self.s - other.s)%np.uint8(2),
                         (self.phase / other.phase))

    def __add__(self,other):
        return CHState(self.N,
                         (self.A + other.A)%np.uint8(2),
                         (self.B + other.B)%np.uint8(2),
                         (self.C + other.C)%np.uint8(2),
                         (self.g + other.g)%np.uint8(4),
                         (self.v + other.v)%np.uint8(2),
                         (self.s + other.s)%np.uint8(2),
                         (self.phase * other.phase))

    def equatorial_inner_product(self, A):
        """
        Given an equatorial state |phi_A> defined by a symmetric binary matrix A
        compute
        <|phi_A | self >
        """

        print("A = ", A)
        J = np.int64((self.M @ self.F.T) % np.uint8(2))
        J[np.diag_indices_from(J)] = self.g

        print("J = ", J)
        
        K = (self.G.T @ (A + J) @ self.G) 
        print("K = ", K)
        prefactor = (2**(-(self.N + self.v.sum())/2)) * ((1j)**(self.s @ K @ self.s)) * ((-1)**(self.s @ self.v))
        print("pf = ", prefactor)
        B = (K + 2*np.diag(self.s + self.s @ K))[self.v == 1][:,self.v == 1] % np.uint8(4)
        print("B = ", B)
        #M = np.triu(B) % np.uint8(2) #upper triangular part including diagonal
        #M[np.diag_indices_from(M)] = np.uint8(0)
        #print("M = ", M)
        K = B[np.diag_indices_from(B)] % np.uint8(2)
        print("K = ", K)
        L = ((B[np.diag_indices_from(B)] - K) // np.uint8(2))  # the // forces integer division and makes sure the dtype remains uint8
        print("L = ", L)

        newL = np.append(L,0)

        newM = np.triu((B +  np.outer(K,K)) %np.uint8(2))
        newM[np.diag_indices_from(newM)] = np.uint8(0)
        
        newM = np.concatenate((newM, np.array([K],dtype=np.uint8)), axis=0)
        newM = np.concatenate((newM, np.array([[0]*newM.shape[0]],dtype=np.uint8).T) ,  axis=1)
        
        re = util.z2ExponentialSum(newM, newL) / 2
        newL[-1] = 1

        print("newM = ", newM)
        print("newL = ", newL)
        
        im = util.z2ExponentialSum(newM, newL) / 2
        print("re = ", re, "im = ", im)
        print(self.w.conjugate()*prefactor)
        return self.w.conjugate()*prefactor*(re + 1.j *im)

        
        
