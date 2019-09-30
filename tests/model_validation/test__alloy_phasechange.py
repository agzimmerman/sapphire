import firedrake as fe 
import sapphire.benchmarks.diffusive_solidification_of_alloy


class DebugSim(sapphire.benchmarks.diffusive_solidification_of_alloy.Simulation):
    
    """
    def write_outputs(self, write_headers, plotvars = None):
        
        if self.solution_file is None:
            
            solution_filepath = self.output_directory_path.joinpath(
                "solution").with_suffix(".pvd")
            
            self.solution_file = fe.File(str(solution_filepath))
        
        self = self.postprocess()
        
        sapphire.output.report(sim = self, write_header = write_headers)
        
        sapphire.output.write_solution(sim = self, file = self.solution_file)
        
        #sapphire.output.plot(sim = self, plotvars = plotvars)
    """
    
    
def test__validate__diffusive_solidification():
    
    endtime = t_f = 0.1
    
    cutoff_length = xmax = 1.
    
    mesh_cellcount = nx = 80
    
    timestep_size = Delta_t = 0.00125
    
    quadrature_degree = q = 2
    
    
    T_m = 0.  # [deg C]
    
    T_e = -21.1  # [deg C]
    
    S_e = 0.233  # [% wt. NaCl]
    
    m = (T_e - T_m)/S_e
    
    def T_L(S):
        
        return T_m + m*S
        
    
    def T(T__degC):
        
        return (T__degC - T_e)/(T_h - T_e)
        
    
    S_h = 0.038
    
    T_h = T_L(S_h)  # [deg C]
    
    phi_lc = 0.
    
    T_c = T_e + 1.  # [deg C]
    
    
    k_l = 0.544  # [W/(m K)]
    
    #k_s = 2.14  # [W/(m K)]
    k_s = k_l
    
    k_sl = k_s/k_l
    
    
    C_p = 4.186e6  # [J/(m^3 K)]
    
    rho = 1000.  # [kg/m^3]
    
    c_p = C_p/rho # [J/(kg K)]
    
    c_l = c_p
    
    c_s = 2110.  # [J /(kg deg C)]
    
    c_sl = c_s/c_l
    
    
    #alpha = k_l/(rho*c_p)
    
    #D = 1.e-9  # [m^2/s]
    
    #Le = alpha/D
    Le = 80.
    
    h_m = 3.3488e8  # [J/m^3]
    
    Ste = C_p*(T_h - T_e)/h_m
    
    def S(S__wtperc):
    
        return S__wtperc/S_e
    
    
    outdir_path = "output/diffusive_solidification/"\
    + "Le{}_csl{:.3f}_ksl{}_Ste{:.3f}_Te{}_Se{}_Tc{}_Th{:.3f}_Sh{:.3f}"\
    + "__tf{}_philc{}_xmax{}_nx{}_Deltat{}_q{}"
    
    outdir_path = outdir_path.format(
        Le, c_sl, k_sl, Ste, T_e, S_e, T_c, T_h, S_h,
        t_f, phi_lc, xmax, nx, Delta_t, q)
    
    sim = DebugSim(
        lewis_number = Le,
        stefan_number = Ste,
        heat_capacity_solid_to_liquid_ratio = c_sl,
        thermal_conductivity_solid_to_liquid_ratio = k_sl,
        farfield_concentration = S(S_h),
        pure_liquidus_temperature = T(T_m),
        cold_boundary_temperature = T(T_c),
        cold_boundary_porosity = phi_lc,
        quadrature_degree = q,
        mesh_cellcount = nx,
        cutoff_length = xmax,
        output_directory_path = outdir_path)
    
    sim.timestep_size.assign(Delta_t)
    
    sim.solutions, sim.time, = sim.run(endtime = endtime)
