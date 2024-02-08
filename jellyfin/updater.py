import argparse
import requests
import json
import os

from dataclasses import dataclass
from typing import AnyStr, Dict, List
from urllib.parse import urlparse


@dataclass
class PluginVersion:
    version: AnyStr
    changelog: AnyStr
    target_abi: AnyStr
    source_url: AnyStr
    checksum: AnyStr
    timestamp: AnyStr

    def to_dict(self) -> Dict[AnyStr, AnyStr]:
        return {
            "version": str(self.version),
            "changelog": str(self.changelog),
            "targetAbi": str(self.target_abi),
            "sourceUrl": str(self.source_url),
            "checksum": str(self.checksum),
            "timestamp": str(self.timestamp)
        }

    @classmethod
    def from_dict(cls, data: Dict[AnyStr, AnyStr]):
        return cls(
            version=str(data.get("version")),
            changelog=str(data.get("changelog", "")),
            target_abi=str(data.get("targetAbi")),
            source_url=str(data.get("sourceUrl")),
            checksum=str(data.get("checksum")),
            timestamp=str(data.get("timestamp"))
        )


@dataclass
class Plugin:
    guid: AnyStr
    name: AnyStr
    description: AnyStr
    overview: AnyStr
    owner: AnyStr
    category: AnyStr
    image_url: AnyStr
    versions: List[PluginVersion]

    def to_dict(self) -> Dict[AnyStr, AnyStr | Dict]:
        return {
            "guid": str(self.guid),
            "name": str(self.name),
            "description": str(self.description),
            "overview": str(self.overview),
            "owner": str(self.owner),
            "category": str(self.category),
            "imageUrl": str(self.image_url),
            "versions": list(map(lambda pv: pv.to_dict(), self.versions))
        }

    @classmethod
    def from_dict(cls, data: Dict[AnyStr, AnyStr | Dict]):
        return cls(
            guid=str(data.get("guid")),
            name=str(data.get("name")),
            description=str(data.get("description", "")),
            overview=str(data.get("overview", "")),
            owner=str(data.get("owner")),
            category=str(data.get("category")),
            image_url=str(data.get("imageUrl", "")),
            versions=list(map(lambda pvd: PluginVersion.from_dict(
                pvd), data.get("versions", [])))
        )


def fetch_manifest(url: str):
    try:
        req = requests.get(url)
        req.raise_for_status()
        return req.json()
    except:
        return None


def patch_url(url: str, prefix: str, match_hosts: List[str] = None, exclude_hosts: List[str] = None):
    if not url:
        return url
    hostname = urlparse(url).hostname
    if match_hosts is not None and len(match_hosts) > 0:
        if hostname in match_hosts:
            url = prefix + url
    elif exclude_hosts is not None and len(exclude_hosts) > 0:
        if hostname not in exclude_hosts:
            url = prefix + url
    else:
        url = prefix + url
    return url


def add_manifest(url: str):
    manifest = fetch_manifest(url)
    if manifest is not None:
        return list(Plugin.from_dict(p) for p in manifest)
    return list()


def parse_args():
    parser = argparse.ArgumentParser(prog="JFManifestUpdater")
    parser.add_argument("-m", "--manifest", type=str,
                        nargs="+", required=True, help="manifest url")
    parser.add_argument("-p", "--prefix-url", type=str,
                        required=True, help="prefix url")
    parser.add_argument("-o", "--output", type=str,
                        required=True, help="output json")
    parser.add_argument("--whitelist", type=str, nargs="*",
                        required=False, help="host whitelist")
    parser.add_argument("--blacklist", type=str, nargs="*",
                        required=False, help="host blacklist")
    args = parser.parse_args()
    if not args.output.endswith(".json"):
        args.output = args.output + ".json"
    return args


def main():
    args = parse_args()

    plugins = list()
    for repo_url in args.manifest:
        plugins.extend(add_manifest(repo_url))

    for plg in plugins:
        plg.image_url = patch_url(
            plg.image_url, args.prefix_url, args.whitelist, args.blacklist)
        for plg_v in plg.versions:
            plg_v.source_url = patch_url(
                plg_v.source_url, args.prefix_url, args.whitelist, args.blacklist)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as fp:
        json.dump([plg.to_dict() for plg in plugins], fp, indent=2)


if __name__ == "__main__":
    main()
