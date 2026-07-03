import json
import os
from conc_sect_cap import ConcreteSection

def compile_section_data(name, b, h, fc, fy, As_top, d_top, As_bot, d_bot, Av=0, s=0, Ma_pos=0.0, Ma_neg=0.0):
    """
    Instantiates a ConcreteSection, calculates all positive and negative 
    properties, and returns them packed in a clean dictionary.
    """
    # 1. Initialize the section
    sec = ConcreteSection(name, b, h, fc, fy)
    sec.set_flexural_reinforcement(As_top, d_top, As_bot, d_bot)
    sec.set_shear_reinforcement(Av, s)
    
    # 2. Extract Positive Bending Properties
    pos_Mn, pos_phiMn, pos_tc = sec.calculate_moment_capacity(is_positive_bending=True)
    pos_Vn, pos_phiVn = sec.calculate_shear_capacity(is_positive_bending=True)
    pos_Ig, pos_Mcr, pos_Icr, pos_Ie = sec.get_stiffness_properties(Ma_kipft=Ma_pos, is_positive_bending=True)
    
    # 3. Extract Negative Bending Properties
    neg_Mn, neg_phiMn, neg_tc = sec.calculate_moment_capacity(is_positive_bending=False)
    neg_Vn, neg_phiVn = sec.calculate_shear_capacity(is_positive_bending=False)
    neg_Ig, neg_Mcr, neg_Icr, neg_Ie = sec.get_stiffness_properties(Ma_kipft=Ma_neg, is_positive_bending=False)
    
    # 4. Pack the dictionary
    return {
        "geometry": {"b_in": b, "h_in": h},
        "material": {
            "fc_psi": fc, 
            "fy_psi": fy, 
            "Ec_ksi": round(sec.Ec / 1000.0, 1),
            "Es_ksi": round(sec.Es / 1000.0, 1)
        },
        "gross_properties": {"Ig_in4": round(pos_Ig, 1)},
        "positive_bending": {
            "phi_Mn_kft": round(pos_phiMn, 1),
            "phi_Vn_kips": round(pos_phiVn, 1),
            "Mcr_kft": round(pos_Mcr, 1),
            "Icr_in4": round(pos_Icr, 1),
            "Ie_in4": round(pos_Ie, 1),
            "tension_controlled": pos_tc
        },
        "negative_bending": {
            "phi_Mn_kft": round(neg_phiMn, 1),
            "phi_Vn_kips": round(neg_phiVn, 1),
            "Mcr_kft": round(neg_Mcr, 1),
            "Icr_in4": round(neg_Icr, 1),
            "Ie_in4": round(neg_Ie, 1),
            "tension_controlled": neg_tc
        }
    }

def get_float(prompt, default=0.0):
    """Helper to get float input with a default fallback."""
    val = input(f"{prompt} [{default}]: ").strip()
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        print(f"Invalid input. Using default: {default}")
        return default

def get_bool(prompt, default=False):
    """Helper to get boolean input."""
    def_str = "y/N" if not default else "Y/n"
    val = input(f"{prompt} ({def_str}): ").strip().lower()
    if not val:
        return default
    return val in ['y', 'yes', 'true', '1']

def main():
    catalog = {}
    print("\n" + "="*50)
    print(" CONCRETE SECTION CATALOG BUILDER ")
    print("="*50)
    
    while True:
        name = input("\nEnter section name (e.g., mem_a) [done]: ").strip()
        if name.lower() in ['done', 'quit', 'exit', 'q', '']:
            break
            
        print(f"\n--- Geometry & Material for {name} ---")
        b = get_float("Width (b) in inches", 12.0)
        h = get_float("Height (h) in inches", 12.0)
        fy = get_float("Steel Yield Strength (fy) in psi", 60000.0)
        fc = get_float("Concrete Strength (f'c) in psi", 5000.0)
        
        print(f"\n--- Flexural Reinforcement for {name} ---")
        As_top = get_float("Top Steel Area (As_top) in sq in", 0.0)
        d_top = get_float("Top Steel Depth (d_top) in inches", 0.0)
        As_bot = get_float("Bottom Steel Area (As_bot) in sq in", 0.0)
        d_bot = get_float("Bottom Steel Depth (d_bot) in inches", 0.0)
        
        print(f"\n--- Shear Reinforcement for {name} ---")
        Av = get_float("Shear Tie Area (Av) in sq in", 0.0)
        s = get_float("Shear Tie Spacing (s) in inches", 0.0)
        
        print(f"\n--- Applied Demands for {name} ---")
        Ma_pos = get_float("Applied Positive Moment (Ma_pos) for Ie in k-ft [0 if unknown]", 0.0)
        Ma_neg = get_float("Applied Negative Moment (Ma_neg) for Ie in k-ft [0 if unknown]", 0.0)
        
        # Compile and store the section
        catalog[name] = compile_section_data(
            name=name, b=b, h=h, fc=fc, fy=fy,
            As_top=As_top, d_top=d_top, 
            As_bot=As_bot, d_bot=d_bot, 
            Av=Av, s=s, Ma_pos=Ma_pos, Ma_neg=Ma_neg
        )
        print(f"\n[+] Section '{name}' added to catalog.")

    # Print out the dictionary nicely to the console
    if catalog:
        print("\n" + "="*50)
        print(" CONCRETE SECTION CATALOG (JSON EXPORT READY) ")
        print("="*50)
        print(json.dumps(catalog, indent=4))
        print("="*50 + "\n")
        
        # Export to JSON file in the 'data' directory
        os.makedirs("data", exist_ok=True)
        
        counter = 0
        while True:
            filename = "sections.json" if counter == 0 else f"sections_{counter}.json"
            export_path = os.path.join("data", filename)
            
            if os.path.exists(export_path):
                overwrite = get_bool(f"File '{export_path}' already exists. Overwrite?", default=False)
                if overwrite:
                    break
                else:
                    counter += 1
            else:
                break
                
        try:
            with open(export_path, "w") as f:
                json.dump(catalog, f, indent=4)
            print(f"[+] Successfully exported catalog to: {export_path}\n")
        except Exception as e:
            print(f"[-] Failed to write JSON file: {e}\n")
    else:
        print("\nNo sections created. Exiting.\n")

if __name__ == "__main__":
    main()