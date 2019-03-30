import firedrake as fe
import sunfire.mms
import sunfire.models.convection_diffusion as model_module


sin, pi = fe.sin, fe.pi

def manufactured_solution(model):
    
    x = fe.SpatialCoordinate(model.mesh)
    
    return sin(2.*pi*x[0])*sin(pi*x[1])
    
    
def advection_velocity(mesh):

    x = fe.SpatialCoordinate(mesh)
    
    ihat, jhat = sunfire.model.unit_vectors(mesh)
    
    return sin(2.*pi*x[0])*sin(4.*pi*x[1])*ihat \
        + sin(pi*x[0])*sin(2.*pi*x[1])*jhat
    
    
def test__verify_convergence_order_via_mms(
        mesh_sizes = (16, 32), tolerance = 0.1, quadrature_degree = 2):
    
    sunfire.mms.verify_spatial_order_of_accuracy(
        model_module = model_module,
        manufactured_solution = manufactured_solution,
        meshes = [fe.UnitSquareMesh(n, n) for n in mesh_sizes],
        model_constructor_kwargs = {
            "quadrature_degree": quadrature_degree,
            "element_degree": 1,
            "advection_velocity": advection_velocity},
        parameters = {"kinematic_viscosity": 0.1},
        expected_order = 2,
        tolerance = tolerance)
