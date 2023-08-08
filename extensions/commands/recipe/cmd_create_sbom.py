import os.path

from packageurl import PackageURL
from cyclonedx.factory.license import LicenseFactory
from cyclonedx.model import ExternalReference, ExternalReferenceType, LicenseChoice, XsUri
from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.output.json import JsonV1Dot4

from conan.api.output import cli_out_write
from conan.api.conan_api import ConanAPI
from conan.cli.args import common_graph_args, validate_common_graph_args
from conan.cli.command import conan_command
from conans.client.graph.graph import Node

lFac = LicenseFactory()


def package_type_to_component_type(pt: str) -> ComponentType:
    if pt is "application":
        return ComponentType.APPLICATION
    else:
        return ComponentType.LIBRARY


def licenses(ids):
    """
    see https://cyclonedx.org/docs/1.4/json/#components_items_licenses
    """
    if ids is None:
        return None
    if not isinstance(ids, tuple):
        ids = [ids]
    return [LicenseChoice(license=lFac.make_from_string(i)) for i in ids]


def package_url(node: Node) -> PackageURL:
    """
    Creates a PURL following https://github.com/package-url/purl-spec/blob/master/PURL-TYPES.rst#conan
    """
    return PackageURL(
        type="conan",
        name=node.conanfile.name,
        version=node.conanfile.version,
        qualifiers={
            "prev": node.prev,
            "rref": node.ref.revision,
            "user": node.conanfile.user,
            "channel": node.conanfile.channel,
            "repository_url": node.remote.url if node.remote else None
        })


def create_component(n: Node) -> Component:
    result = Component(
        type=package_type_to_component_type(n.conanfile.package_type),
        name=n.conanfile.name,
        version=n.conanfile.version,
        licenses=licenses(n.conanfile.license),
        bom_ref=package_url(n).to_string(),
        purl=package_url(n),
        description=n.conanfile.description
    )
    if n.conanfile.homepage:
        result.external_references.add(ExternalReference(
            type=ExternalReferenceType.WEBSITE,
            url=XsUri(n.conanfile.homepage),
        ))
    return result


@conan_command(group="Recipe")
def create_sbom(conan_api: ConanAPI, parser, *args):
    """
    creates an SBOM in CycloneDX 1.4 JSON format from a Conan graph JSON
    """

    # BEGIN COPY FROM conan: cli/commands/graph.py
    common_graph_args(parser)
    args = parser.parse_args(*args)
    validate_common_graph_args(args)
    cwd = os.getcwd()
    path = conan_api.local.get_conanfile_path(args.path, cwd, py=None) if args.path else None
    remotes = conan_api.remotes.list(args.remote) if not args.no_remote else []
    overrides = eval(args.lockfile_overrides) if args.lockfile_overrides else None
    lockfile = conan_api.lockfile.get_lockfile(lockfile=args.lockfile,
                                               conanfile_path=path,
                                               cwd=cwd,
                                               partial=args.lockfile_partial,
                                               overrides=overrides)
    profile_host, profile_build = conan_api.profiles.get_profiles_from_args(args)
    deps_graph = conan_api.graph.load_graph_consumer(path, args.name, args.version,
                                                     args.user, args.channel,
                                                     profile_host, profile_build, lockfile,
                                                     remotes, args.update)
    # END COPY
    root = deps_graph.root
    root_component = create_component(root)
    bom = Bom()
    bom.metadata.component = root_component
    component_per_node = {root: root_component}
    for n in deps_graph.nodes[1:]:  # node 0 is the root
        component = create_component(n)
        bom.components.add(component)
        component_per_node[n] = component
    for dep in deps_graph.nodes:
        for dep_dep in dep.dependencies:
            bom.register_dependency(component_per_node[dep], [component_per_node[dep_dep.dst]])
    serialized_json = JsonV1Dot4(bom).output_as_string()
    cli_out_write(serialized_json)