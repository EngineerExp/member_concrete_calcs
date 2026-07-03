import math

class ConcreteSection:
    """
    A class to calculate ACI 318-19 capacities and stiffness properties 
    for a rectangular concrete section.
    """
    def __init__(self, section_id, b, h, fc, fy=60000):
        self.section_id = section_id
        self.b = float(b)
        self.h = float(h)
        self.fc = float(fc)
        self.fy = float(fy)
        self.Ec = 57000.0 * math.sqrt(self.fc)
        self.Es = 29000000.0
        self.n = self.Es / self.Ec
        
        self.As_top = 0.0
        self.d_top = 0.0
        self.As_bot = 0.0
        self.d_bot = 0.0
        self.Av = 0.0
        self.s = 0.0

    def set_flexural_reinforcement(self, As_top, d_top, As_bot, d_bot):
        self.As_top = float(As_top)
        self.d_top = float(d_top)
        self.As_bot = float(As_bot)
        self.d_bot = float(d_bot)

    def set_shear_reinforcement(self, Av, s):
        self.Av = float(Av)
        self.s = float(s)

    def calculate_moment_capacity(self, is_positive_bending=True):
        """
        Calculates Mn and phi_Mn. Includes ACI 318-19 strain compatibility check.
        """
        As = self.As_bot if is_positive_bending else self.As_top
        d = self.d_bot if is_positive_bending else self.d_top

        if As == 0.0 or d == 0.0 or self.b == 0.0:
            return 0.0, 0.0, False

        # Equilibrium: C = T -> 0.85 * fc * a * b = As * fy
        a = (As * self.fy) / (0.85 * self.fc * self.b)
        
        # Beta1 per ACI 318-19 Table 22.2.2.4.3
        if self.fc <= 4000: beta1 = 0.85
        elif self.fc <= 8000: beta1 = 0.85 - 0.05 * (self.fc - 4000) / 1000
        else: beta1 = 0.65
            
        c = a / beta1
        
        # Strain Compatibility (ACI 318-19 22.2.1)
        epsilon_cu = 0.003
        epsilon_ty = self.fy / self.Es
        epsilon_t = epsilon_cu * (d - c) / c if c > 0 else float('inf')
        
        # Tension-controlled limit (ACI 318-19 Table 21.2.2)
        # Net tensile strain limit for phi=0.9 is 0.005
        is_tension_controlled = epsilon_t >= 0.005
        
        # Strength Reduction Factor (phi)
        if is_tension_controlled:
            phi = 0.90
        elif epsilon_t <= epsilon_ty:
            phi = 0.65 # Compression controlled
        else:
            # Transition zone (ACI 21.2.2.1)
            phi = 0.65 + 0.25 * ((epsilon_t - epsilon_ty) / (0.005 - epsilon_ty))

        Mn_kipft = (As * self.fy * (d - (a / 2.0))) / 12000.0
        return Mn_kipft, phi * Mn_kipft, is_tension_controlled

    def calculate_shear_capacity(self, is_positive_bending=True):
        """
        Calculates Vn and phi_Vn per ACI 318-19 (One-Way Shear).
        """
        As = self.As_bot if is_positive_bending else self.As_top
        d = self.d_bot if is_positive_bending else self.d_top

        if d == 0.0 or self.b == 0.0:
            return 0.0, 0.0

        lambda_s = min(math.sqrt(2.0 / (1.0 + (d / 10.0))), 1.0)
        rho_w = As / (self.b * d)

        # Steel Shear (Vs)
        Vs_lbs = (self.Av * self.fy * d) / self.s if self.s > 0 else 0.0

        # Min Shear Reinforcement (Av,min)
        if self.s > 0:
            Av_min = max(0.75 * math.sqrt(self.fc) * self.b * self.s / self.fy, 
                         50.0 * self.b * self.s / self.fy)
        else:
            Av_min = float('inf')

        # Concrete Shear (Vc)
        if self.Av >= Av_min:
            Vc_lbs = 2.0 * math.sqrt(self.fc) * self.b * d
        else:
            Vc_lbs = 8.0 * lambda_s * (rho_w ** (1/3)) * math.sqrt(self.fc) * self.b * d

        Vn_kips = (Vc_lbs + Vs_lbs) / 1000.0
        return Vn_kips, 0.75 * Vn_kips

    def get_stiffness_properties(self, Ma_kipft=0.0, is_positive_bending=True):
        # Ig, Mcr, Icr logic remains standard
        Ig = (self.b * (self.h ** 3)) / 12.0
        fr = 7.5 * math.sqrt(self.fc)
        Mcr = (fr * Ig / (self.h / 2.0)) / 12000.0
        
        # Cracked I calculation omitted for brevity but follows standard transformed section
        return Ig, Mcr, 0.0, 0.0 # Placeholder