import click
import yaml
from typing import List, Optional

PACKAGE_NAME = "python main.py"

SERVICE_KIND = "Service"
POD_KIND = "Pod"
DEPLOYMENT_KIND = "Deployment"
SERVICE_ACCOUNT_KIND = "ServiceAccount"
INGRESS_KIND = "Ingress"
NETWORK_POLICY_KIND = "NetworkPolicy"
CONFIGMAP_KIND = "ConfigMap"
CRONJOB_KIND = "CronJob"
STATEFUL_SET_KIND = "StatefulSet"

D2_FORMAT = "d2"
MERMAID_FORMAT = "mermaid"

class Resource:
    def __init__(self, description: dict) -> None:
        self.description = description

    def get_key(self):
        name = self.get_name()
        kind = self.get_kind()
        return f"{kind}_{name}"

    def get_name(self) -> str:
        return self.description["metadata"]["name"]

    def get_kind(self) -> str:
        return self.description["kind"]

    def get_short_kind(self):
        kind = self.get_kind()
        if kind == SERVICE_KIND:
            return "svc"
        if kind == POD_KIND:
            return "pod"
        if kind == DEPLOYMENT_KIND:
            return "deploy"
        if kind == SERVICE_ACCOUNT_KIND:
            return "sa"
        if kind == INGRESS_KIND:
            return "ing"
        if kind == NETWORK_POLICY_KIND:
            return "netpol"
        if kind == CONFIGMAP_KIND:
            return "cm"
        if kind == CRONJOB_KIND:
            return "cronjob"
        if kind == STATEFUL_SET_KIND:
            return "sts"
        return ""

    def get_icon_url(self) -> str:
        base_url = "https://github.com/kubernetes/community/blob/master/icons/svg/resources/labeled/"
        return f"{base_url}{self.get_short_kind()}.svg?raw=true"

    def get_selector(self) -> dict:
        if self.get_kind() == SERVICE_KIND:
            return self.description["spec"]["selector"]
        raise Exception("Try to get selector for resource type without selector.")

    def matches_selector(self, matchesLabels: dict) -> bool:
        labels = self.get_labels()
        match = True
        for item in matchesLabels.items():
            match &= item in labels.items()
        return match

    def get_labels(self) -> dict:
        return self.description["metadata"]["labels"]

    def get_deployment_selector(self) -> dict:
        return self.description["spec"]["selector"]["matchLabels"]

    def get_pod_template(self) -> dict:
        template = self.description["spec"]["template"]
        template["kind"] = POD_KIND
        template["metadata"]["name"] = self.get_name()
        return template


def get_resources_from_input(i):
    try:
        with open(i, "r") as stream:
            for resource_description in yaml.safe_load_all(stream):
                if not resource_description or not resource_description["metadata"]:
                    continue
                resource = Resource(resource_description)
                yield resource
                if resource.get_kind() == DEPLOYMENT_KIND:
                    pod_description = resource.get_pod_template()
                    if not pod_description:
                        continue
                    yield Resource(pod_description)
    except IOError:
        print(f"Unable to load file from path {i}")


class Node:
    def __init__(self, key: str, name: str, icon_url: str) -> None:
        self.key = key
        self.name = name
        self.icon_url = icon_url

    def to_string(self, output_format: str) -> str:
        if output_format == D2_FORMAT:
            return f"{self.key}:{self.name} {{\n  icon: {self.icon_url}\n  shape: image\n}}"
        if output_format == MERMAID_FORMAT:
            return f"subgraph {self.key}[{self.name}]\n {self.key}_icon(<img src='{self.icon_url}' width='32' height='32'/>)\nend\n"
        raise Exception("Unknown output format.")


class Edge:
    def __init__(self, node: str, dependency: str) -> None:
        self.node = node
        self.dependency = dependency

    def to_string(self, output_format: str) -> str:
        if output_format == D2_FORMAT:
            return f"{self.node} --> {self.dependency}"
        if output_format == MERMAID_FORMAT:
            return f"{self.node} --> {self.dependency}"
        raise Exception("Unknown output format.")


class Diagram:
    nodes: List[Node] = []
    edges: List[Edge] = []

    def add_node(self, node: Node):
        self.nodes.append(node)

    def add_edge(self, edge: Edge):
        self.edges.append(edge)

    def output(self, output_path, output_format):
        with open(output_path, "w") as output_file:
            if output_format == MERMAID_FORMAT:
                output_file.write("flowchart TD\n")
            for node in self.nodes:
                output_file.write(f"{node.to_string(output_format)}\n")
            for edge in self.edges:
                output_file.write(f"{edge.to_string(output_format)}\n")


class Resources:
    def __init__(self, resources: List[Resource]) -> None:
        self.resources = resources

    def find_deployments_matching_selector(self, selector):
        return []

    def find_service_by_name(self, name):
        for resource in self.resources:
            if resource.get_kind() == SERVICE_KIND and resource.get_name() == name:
                return resource
        raise Exception(f"No Service found with name {name}")

    def find_dependencies(self, resource: Resource) -> List[Resource]:
        kind = resource.get_kind()
        if kind == DEPLOYMENT_KIND:
            return self.find_deployment_dependencies(resource)
        if kind == POD_KIND:
            return self.find_pod_dependencies(resource)
        if kind == SERVICE_KIND:
            return self.find_service_dependencies(resource)
        if kind == INGRESS_KIND:
            return self.find_ingress_dependencies(resource)
        if kind == NETWORK_POLICY_KIND:
            return self.find_network_policy_dependencies(resource)
        return []

    def find_network_policy_dependencies(self, network_policy: Resource):
        selector = network_policy.description["spec"]["podSelector"]["matchLabels"]
        return [
            resource
            for resource in self.resources
            if resource.get_kind() == POD_KIND and resource.matches_selector(selector)
        ]

    def find_deployment_dependencies(self, deployment: Resource):
        selector = deployment.get_deployment_selector()
        return [
            resource
            for resource in self.resources
            if resource.get_kind() == POD_KIND and resource.matches_selector(selector)
        ]

    def find_pod_dependencies(self, resource: Resource):
        containers = resource.description["spec"]["containers"]
        config_maps = []
        for container in containers:
            env_froms = container.get("envFrom", [])
            for env_from in env_froms:
                config_map_ref=env_from.get("configMapRef")
                if config_map_ref:
                    name = config_map_ref["name"]
                    config_maps.append(self.find_config_map_by_name(name))
        return config_maps

    def find_config_map_by_name(self, name: str) -> Resource:
        for resource in self.resources:
            if resource.get_kind() == CONFIGMAP_KIND and resource.get_name() == name:
                return resource
        Exception(f"No config map with name {name} in resources.")

    def find_service_dependencies(self, service: Resource) -> List[Resource]:
        try:
            selector = service.get_selector()
        except:
            return []
        return [
            resource
            for resource in self.resources
            if resource.get_kind() == POD_KIND and resource.matches_selector(selector)
        ]

    def find_ingress_dependencies(self, ingress: Resource):
        rules = ingress.description["spec"]["rules"]
        services = []
        for rule in rules:
            paths = rule["http"]["paths"]
            for path in paths:
                service_name = path["backend"]["service"]["name"]
                service = self.find_service_by_name(service_name)
                services.append(service)
        return services


@click.command()
@click.option("-i")
@click.option("-o", default="output.d2")
@click.option("-f", default=D2_FORMAT)
def cli(i, o, f) -> None:
    if not i:
        print(f"No input file provided. Do: {PACKAGE_NAME} -i <input-file-path>")
        return

    resources = Resources(resources=[r for r in get_resources_from_input(i)])
    diagram = Diagram()

    for resource in resources.resources:
        diagram.add_node(
            Node(resource.get_key(), resource.get_name(), resource.get_icon_url())
        )
        for dependency in resources.find_dependencies(resource):
            diagram.add_edge(Edge(resource.get_key(), dependency.get_key()))

    diagram.output(o, f)


if __name__ == "__main__":
    cli()
