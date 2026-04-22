def find_rpc_by_request(
    config: dict, package_name: str, service_name: str, func_name: str
):
    protos = config.get("protos", [])
    for proto in protos:
        if proto.get("package") != package_name:
            continue
        services = proto.get("services", [])
        for service in services:
            if service.get("name") != service_name:
                continue
            rpcs = service.get("rpc", [])
            for rpc in rpcs:
                if rpc.get("func") == func_name:
                    return rpc
    return {}
