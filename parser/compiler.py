import os
import re
import solcx

def extract_solidity_version(contract_path):
    """
    Extracts the Solidity compiler version from the pragma statement in the file.
    If none is found, default to 0.8.20.
    """
    pragma_regex = re.compile(r'pragma\s+solidity\s+([^;]+);')
    with open(contract_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = pragma_regex.search(content)
    if not match:
        return "0.8.20"
    
    version_expr = match.group(1).strip()
    # strip range operators such as ^ and >= to get a plain version
    clean_version = re.sub(r'[^\d\.]', '', version_expr)
    
    # pad short versions such as 0.8 to 0.8.0
    parts = clean_version.split('.')
    if len(parts) == 2:
        clean_version = f"{clean_version}.0"
    elif len(parts) == 1:
        clean_version = f"{clean_version}.0.0"
        
    # map each minor series to the solc release used for testing
    if "0.8" in clean_version:
        return "0.8.20"
    elif "0.7" in clean_version:
        return "0.7.6"
    elif "0.6" in clean_version:
        return "0.6.12"
    elif "0.5" in clean_version:
        return "0.5.17"
    elif "0.4" in clean_version:
        return "0.4.25"
        
    return clean_version

def compile_contract(contract_path):
    """
    Compiles a Solidity contract using py-solc-x and returns its AST.
    """
    version = extract_solidity_version(contract_path)
    print(f"[*] Detected pragma version requirement. Using solc {version}")
    
    installed_versions = solcx.get_installed_solc_versions()
    target_ver = solcx.wrapper.Version(version)
    
    if target_ver not in installed_versions:
        print(f"[*] Installing solc {version}...")
        solcx.install_solc(version)
    
    solcx.set_solc_version(version)
    
    print(f"[*] Compiling {contract_path}...")
    compiled = solcx.compile_files(
        [contract_path],
        output_values=["ast"]
    )
    
    # keys look like 'path:ContractName' or just 'path'
    ast_dict = {}
    for key, value in compiled.items():
        file_part = key.split(':')[0]
        if os.path.basename(file_part) == os.path.basename(contract_path):
            if "ast" in value:
                ast_dict = value["ast"]
                break
                
    if not ast_dict:
        # fall back to the first entry that has an AST
        for key, value in compiled.items():
            if "ast" in value:
                ast_dict = value["ast"]
                break
                
    if not ast_dict:
        raise ValueError(f"Could not retrieve AST from compiled output of {contract_path}")
        
    return ast_dict

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        try:
            ast = compile_contract(test_path)
            print("[+] Compiled successfully! AST keys:", ast.keys())
        except Exception as e:
            print(f"[-] Compilation failed: {e}")
    else:
        print("Usage: python compiler.py <path_to_solidity_file>")
