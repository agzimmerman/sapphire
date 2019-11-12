""" A simulation class for binary alloy melting and solidification in enthalpy form """
import firedrake as fe
import sapphire.simulation


def enthalpy(sim, temperature, porosity):

    T = temperature

    phi_l = porosity

    c_sl = sim.heat_capacity_solid_to_liquid_ratio

    c = phase_dependent_material_property(c_sl)(phi_l)
    
    T_0 = sim.reference_temperature
    
    Ste = sim.stefan_number
    
    return c*(T - T_0) + 1./Ste*phi_l


def liquidus_temperature(sim, solute_concentration):
    
    T_m = sim.pure_liquidus_temperature
    
    S_l = solute_concentration
    
    return T_m*(1. - S_l)
    
    
def liquidus_enthalpy(sim, solute_concentration):
    
    Ste = sim.stefan_number
    
    S_l = solute_concentration
    
    T_L = liquidus_temperature(sim = sim, solute_concentration = S_l)
    
    T_0 = sim.reference_temperature
    
    return T_L - T_0 + 1./Ste
    
   
def liquid_volume_fraction(sim, enthalpy, solute_concentration):
    
    h = enthalpy
    
    S_l = solute_concentration
    
    T_m = sim.pure_liquidus_temperature
    
    Ste = sim.stefan_number
    
    h_L = liquidus_enthalpy(sim = sim, solute_concentration = S_l)
    
    c_sl = sim.heat_capacity_solid_to_liquid_ratio
    
    T_0 = sim.reference_temperature
    
    phi_l_mush = \
        (h - c_sl*(T_m*(1. - S_l) - T_0)) / \
        ((1. - c_sl)*(T_m*(1. - S_l) - T_0) + 1./Ste)
    
    return fe.conditional(h >= h_L, 1., phi_l_mush)


def phase_dependent_material_property(solid_to_liquid_ratio):

    P_sl = solid_to_liquid_ratio
    
    def P(phil):
    
        return P_sl + (1. - P_sl)*phil
    
    return P
    

def temperature(sim, enthalpy, solute_concentration):
    
    h = enthalpy
    
    S_l = solute_concentration
    
    phi_l = liquid_volume_fraction(
        sim = sim, enthalpy = h, solute_concentration = S_l)
    
    Ste = sim.stefan_number
    
    c_sl = sim.heat_capacity_solid_to_liquid_ratio
    
    c = phase_dependent_material_property(c_sl)(phi_l)
    
    T_0 = sim.reference_temperature
    
    return (h - 1./Ste*phi_l)/c + T_0


def solute_concentration(sim, enthalpy, porosity):
    
    h = enthalpy
    
    phi_l = porosity
    
    c_sl = sim.heat_capacity_solid_to_liquid_ratio
    
    c = phase_dependent_material_property(c_sl)(phi_l)
    
    T_m = sim.pure_liquidus_temperature
    
    T_0 = sim.reference_temperature
    
    Ste = sim.stefan_number
    
    return 1. - 1./T_m*((h - 1./Ste*phi_l)/c + T_0)
    

dot, grad = fe.dot, fe.grad
    
    
def time_discrete_terms(sim, solutions, timestep_size):

    h_t, _ = sapphire.simulation.time_discrete_terms(
        solutions = solutions, timestep_size = timestep_size)
    
    (h, S_l), (h_n, S_l_n) = solutions
    
    phi_l = liquid_volume_fraction(
        sim = sim, enthalpy = h, solute_concentration = S_l)
    
    phi_l_n = liquid_volume_fraction(
        sim = sim, enthalpy = h_n, solute_concentration = S_l_n)
    
    S = S_l*phi_l
    
    S_n = S_l_n*phi_l_n
    
    S_t = (S - S_n)/timestep_size
    
    return h_t, S_t
    
    
def variational_form_residual(sim, solution):
    
    h, S_l = fe.split(solution)
    
    T = temperature(sim = sim, enthalpy = h, solute_concentration = S_l)
    
    h_t, S_t = time_discrete_terms(
        sim = sim, 
        solutions = sim.solutions, 
        timestep_size = sim.timestep_size)
    
    psi_h, psi_S_l = fe.TestFunctions(sim.solution.function_space())
    
    phi_l = liquid_volume_fraction(
        sim = sim, enthalpy = h, solute_concentration = S_l)
        
    k_sl = sim.thermal_conductivity_solid_to_liquid_ratio
    
    k = phase_dependent_material_property(k_sl)(phi_l)
    
    energy = psi_h*h_t + dot(grad(psi_h), k*grad(T))
    
    Le = sim.lewis_number
    
    solute = psi_S_l*S_t + 1./Le*dot(grad(psi_S_l), phi_l*grad(S_l))
    
    dx = fe.dx(degree = sim.quadrature_degree)
    
    return (energy + solute)*dx
    
    
diff, div = fe.diff, fe.div
    
def strong_residual(sim, solution):
    
    h, S_l = solution
    
    t = sim.time
    
    phi_l = liquid_volume_fraction(
        sim = sim, enthalpy = h, solute_concentration = S_l)
        
    k_sl = sim.thermal_conductivity_solid_to_liquid_ratio
    
    k = phase_dependent_material_property(k_sl)(phi_l)
    
    T = temperature(sim = sim, enthalpy = h, solute_concentration = S_l)
    
    energy = diff(h, t) - div(k*grad(T))
    
    Le = sim.lewis_number
    
    S = S_l*phi_l
    
    solute = diff(S, t) - 1./Le*div(phi_l*grad(S_l))
    
    return energy, solute
    

def element(cell, degree):

    scalar_element = fe.FiniteElement("P", cell, degree)
    
    return fe.MixedElement(scalar_element, scalar_element)

    
def plotvars(sim, solution = None):
    
    if solution is None:
    
        solution = sim.solution
    
    h, S_l = solution.split()
    
    phi_l = sim.postprocessed_liquid_volume_fraction
    
    S = sim.postprocessed_bulk_solute_concentration
    
    T = sim.postprocessed_temperature
    
    T_L = sim.postprocessed_liquidus_temperature
    
    h_L = sim.postprocessed_liquidus_enthalpy
    
    return (h, S_l, phi_l, S, T, T_L, h_L), \
        ("h", "S_l", "\\phi_l", "S", "T", "T_L(S_l)", "h_L(S_l)"), \
        ("h", "S_l", "phil", "S", "T", "T_L", "h_L")
     
    
class Simulation(sapphire.simulation.Simulation):
    
    def __init__(self, *args, 
            mesh, 
            stefan_number,
            lewis_number,
            pure_liquidus_temperature,
            reference_temperature,
            heat_capacity_solid_to_liquid_ratio,
            thermal_conductivity_solid_to_liquid_ratio,
            element_degree = 1, 
            snes_max_iterations = 100,
            snes_absolute_tolerance = 1.e-9,
            snes_step_tolerance = 1.e-9,
            snes_linesearch_damping = 1.,
            snes_linesearch_maxstep = 1.,
            **kwargs):
        
        self.stefan_number = fe.Constant(stefan_number)
        
        self.lewis_number = fe.Constant(lewis_number)
        
        self.pure_liquidus_temperature = fe.Constant(
            pure_liquidus_temperature)
        
        self.reference_temperature = fe.Constant(
            reference_temperature)
            
        self.heat_capacity_solid_to_liquid_ratio = fe.Constant(
            heat_capacity_solid_to_liquid_ratio)
        
        self.thermal_conductivity_solid_to_liquid_ratio = fe.Constant(
            thermal_conductivity_solid_to_liquid_ratio)
            
        self.initial_temperature = fe.Constant(1.)   # (T_i - T_e)/(T_i - T_e)
        
        self.snes_max_iterations = snes_max_iterations
        
        self.snes_absolute_tolerance = snes_absolute_tolerance
        
        self.snes_step_tolerance = snes_step_tolerance
        
        self.snes_linesearch_damping = snes_linesearch_damping
        
        self.snes_linesearch_maxstep = snes_linesearch_maxstep
        
        super().__init__(*args,
            mesh = mesh,
            element = element(
                cell = mesh.ufl_cell(), degree = element_degree),
            variational_form_residual = variational_form_residual,
            **kwargs)
            
        self.postprocessed_liquid_volume_fraction = \
            fe.Function(self.postprocessing_function_space)
        
        self.postprocessed_temperature = \
            fe.Function(self.postprocessing_function_space)
            
        self.postprocessed_bulk_solute_concentration = \
            fe.Function(self.postprocessing_function_space)
            
        self.postprocessed_liquidus_temperature = \
            fe.Function(self.postprocessing_function_space)
            
        self.postprocessed_liquidus_enthalpy = \
            fe.Function(self.postprocessing_function_space)
            
        self.postprocessed_functions = (
            self.postprocessed_liquid_volume_fraction,
            self.postprocessed_bulk_solute_concentration,
            self.postprocessed_temperature,
            self.postprocessed_liquidus_temperature,
            self.postprocessed_liquidus_enthalpy)
            
    def solve(self, *args, **kwargs):
        
        return super().solve(*args,
            parameters = {
                "snes_type": "newtonls",
                "snes_max_it": self.snes_max_iterations,
                "snes_monitor": None,
                "snes_abstol": self.snes_absolute_tolerance,
                "snes_stol": self.snes_step_tolerance,
                "snes_rtol": 0.,
                "snes_linesearch_type": "l2",
                "snes_linesearch_maxstep": self.snes_linesearch_maxstep,
                "snes_linesearch_damping": self.snes_linesearch_damping,
                "ksp_type": "preonly", 
                "pc_type": "lu", 
                "mat_type": "aij",
                "pc_factor_mat_solver_type": "mumps"},
            **kwargs)
            
    def postprocess(self):
    
        h, S_l = self.solution.split()
        
        
        phi_l = fe.interpolate(
            liquid_volume_fraction(
                sim = self,
                enthalpy = h,
                solute_concentration = S_l),
            self.postprocessing_function_space)
            
        self.postprocessed_liquid_volume_fraction = \
            self.postprocessed_liquid_volume_fraction.assign(phi_l)
        
        
        T = fe.interpolate(
            temperature(
                sim = self,
                enthalpy = h,
                solute_concentration = S_l),
            self.postprocessing_function_space)
        
        self.postprocessed_temperature = \
            self.postprocessed_temperature.assign(T)
        
        
        S = fe.interpolate(
            S_l*phi_l,
            self.postprocessing_function_space)
        
        self.postprocessed_bulk_solute_concentration = \
            self.postprocessed_bulk_solute_concentration.assign(S)
        
        
        T_L = fe.interpolate(
            liquidus_temperature(
                sim = self,
                solute_concentration = S_l),
            self.postprocessing_function_space)
            
        self.postprocessed_liquidus_temperature = \
            self.postprocessed_liquidus_temperature.assign(T_L)
        
        
        h_L = fe.interpolate(
            liquidus_enthalpy(
                sim = self,
                solute_concentration = S_l),
            self.postprocessing_function_space)
            
        self.postprocessed_liquidus_enthalpy = \
            self.postprocessed_liquidus_enthalpy.assign(h_L)
        
        
        self.total_solute = fe.assemble(S*fe.dx)
        
        
        return self
        
    def write_outputs(self, *args, **kwargs):
        
        super().write_outputs(*args, plotvars = plotvars, **kwargs)
        