import yaml

def load_yaml(stream):
    return yaml.safe_load(stream)

def dump_yaml(data, stream=None, **kwargs):
    kwargs.setdefault("default_flow_style", False)
    kwargs.setdefault("sort_keys", False)
    kwargs.setdefault("allow_unicode", True)
    return yaml.safe_dump(data, stream=stream, **kwargs)

safe_load = yaml.safe_load
safe_dump = dump_yaml
load = yaml.safe_load
dump = dump_yaml
YAMLError = yaml.YAMLError
